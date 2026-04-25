"""Chatbot RAG con tool calling y streaming via DeepSeek-V3.2 (OpenAI-compatible endpoint)."""

from collections.abc import Generator

from ..enrichment.llm_client import chat_completion_stream


def chat_stream(
    user_id: str,
    messages: list[dict[str, str]],
    tools: list[dict],
) -> Generator[str, None, None]:
    """Generador de chunks para streaming en Streamlit con tool calling via DeepSeek-V3.2.

    Args:
        user_id: Identificador del usuario para personalización.
        messages: Historial de mensajes con roles.
        tools: Tool definitions en formato OpenAI dict.

    Yields:
        Chunks de texto para st.write_stream().
    """
    yield from chat_completion_stream(messages, tools=tools)
