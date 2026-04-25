"""Cliente compartido de IA — dos endpoints independientes.

- Chat: DeepSeek-V3.2 via OpenAI-compatible serverless endpoint.
- Embeddings: text-embedding-3-large via Azure OpenAI endpoint.
"""

import os
import time
from collections.abc import Generator

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
from openai import APIError, RateLimitError

load_dotenv()

# --- Chat (DeepSeek-V3.2) ---
CHAT_API_KEY = os.environ.get("AZURE_CHAT_API_KEY", "")
CHAT_BASE_URL = os.environ.get("AZURE_CHAT_BASE_URL", "")
CHAT_MODEL = os.environ.get("AZURE_CHAT_MODEL", "DeepSeek-V3.2")

# --- Embeddings (text-embedding-3-large) ---
EMBEDDING_API_KEY = os.environ.get("AZURE_EMBEDDING_API_KEY", "")
EMBEDDING_ENDPOINT = os.environ.get("AZURE_EMBEDDING_ENDPOINT", "")
EMBEDDING_MODEL = os.environ.get("AZURE_EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_API_VERSION = "2024-12-01-preview"

MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]
RPM_LIMIT = 60

_chat_client: OpenAI | None = None
_embed_client: AzureOpenAI | None = None
_last_chat_request: float = 0.0
_last_embed_request: float = 0.0


def _get_chat_client() -> OpenAI:
    global _chat_client
    if _chat_client is None:
        _chat_client = OpenAI(
            base_url=CHAT_BASE_URL,
            api_key=CHAT_API_KEY,
        )
    return _chat_client


def _get_embed_client() -> AzureOpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = AzureOpenAI(
            azure_endpoint=EMBEDDING_ENDPOINT,
            api_key=EMBEDDING_API_KEY,
            api_version=EMBEDDING_API_VERSION,
        )
    return _embed_client


def _rate_limit(last_attr: str) -> None:
    val = globals()[last_attr]
    elapsed = time.monotonic() - val
    min_interval = 60.0 / RPM_LIMIT
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)


def _retry_with_backoff(func, *args, **kwargs):
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except (RateLimitError, APIError) as e:
            last_error = e
            status = getattr(e, "status_code", 0)
            if status in (429, 503) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])
                continue
            raise
    raise last_error


# ---------------------------------------------------------------------------
# Chat Completion (no streaming)
# ---------------------------------------------------------------------------


def chat_completion(
    messages: list[dict[str, str]],
    *,
    tools: list[dict] | None = None,
    json_mode: bool = False,
    json_schema: dict | None = None,
    json_schema_name: str = "output",
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> dict:
    """Chat completion con soporte para JSON mode y tool calling.

    Args:
        messages: Mensajes con role 'system'|'user'|'assistant'|'tool'.
        tools: Tool definitions en formato OpenAI dict.
        json_mode: Si True, fuerza salida JSON sin schema.
        json_schema: Schema JSON opcional para Structured Output.
        json_schema_name: Nombre del schema.
        temperature: Creatividad (0.0 a 2.0).
        max_tokens: Tokens máximos en respuesta.

    Returns:
        Dict con 'content', 'tool_calls' (opcional), 'usage'.
    """
    client = _get_chat_client()

    kwargs: dict = {
        "model": CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    if json_schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": json_schema_name,
                "schema": json_schema,
                "strict": True,
            },
        }
    elif json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    global _last_chat_request
    _rate_limit("_last_chat_request")

    response = _retry_with_backoff(
        client.chat.completions.create,
        **kwargs,
    )
    _last_chat_request = time.monotonic()

    return _parse_response(response)


def _parse_response(response) -> dict:
    choice = response.choices[0]
    result: dict = {
        "content": choice.message.content or "",
        "usage": {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        },
    }
    if choice.message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in choice.message.tool_calls
        ]
    return result


# ---------------------------------------------------------------------------
# Chat Completion (streaming)
# ---------------------------------------------------------------------------


def chat_completion_stream(
    messages: list[dict[str, str]],
    *,
    tools: list[dict] | None = None,
    temperature: float = 0.3,
) -> Generator[str, None, None]:
    """Streaming de chat para st.write_stream().

    Args:
        messages: Mensajes con role.
        tools: Tool definitions opcionales.
        temperature: Creatividad (0.0 a 2.0).

    Yields:
        Chunks de texto a medida que llegan del stream.
    """
    client = _get_chat_client()

    kwargs: dict = {
        "model": CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    for attempt in range(MAX_RETRIES):
        try:
            global _last_chat_request
            _rate_limit("_last_chat_request")
            response = client.chat.completions.create(**kwargs)
            _last_chat_request = time.monotonic()
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except (RateLimitError, APIError) as e:
            status = getattr(e, "status_code", 0)
            if status in (429, 503) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])
                continue
            raise


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Vectoriza textos con text-embedding-3-large (3072 dimensiones).

    Args:
        texts: Lista de strings a vectorizar (max 500 por batch).

    Returns:
        Lista de vectores (cada uno de 3072 floats).
    """
    if not texts:
        return []

    client = _get_embed_client()

    def _embed_call():
        return client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )

    global _last_embed_request
    _rate_limit("_last_embed_request")

    response = _retry_with_backoff(_embed_call)
    _last_embed_request = time.monotonic()

    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Token Estimation
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Estima tokens de un texto (heurística chars / 3.5).

    DeepSeek no tiene tokenizer público. Estimación conservadora (~10% error).
    Para conteo exacto usar response.usage.total_tokens post-llamada.

    Args:
        text: Texto a estimar.

    Returns:
        Número estimado de tokens.
    """
    return max(1, int(len(text) / 3.5))
