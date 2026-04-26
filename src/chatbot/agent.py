"""Chatbot RAG con tool calling y streaming via DeepSeek-V3.2."""

import json
import os
import sys
from collections.abc import Generator

sys.path.insert(0, os.getcwd())

from src.enrichment.llm_client import chat_completion, chat_completion_stream
from src.chatbot.tools import TOOLS_DICT, TOOL_EXECUTORS


def _execute_tool(name: str, args: str) -> str:
    """Ejecuta una herramienta y retorna el resultado como JSON string."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"Tool '{name}' no encontrada"})
    try:
        params = json.loads(args) if isinstance(args, str) else args
        result = executor(**params)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def chat_with_tools(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> Generator[dict, None, None]:
    """Generador que maneja streaming + tool calling en un loop.

    Yields:
        {"type": "text", "content": str}
        {"type": "tool_call", "name": str, "args": str, "result": str}
    """
    if tools is None:
        tools = TOOLS_DICT

    response = chat_completion(
        messages=messages,
        tools=tools,
        temperature=0.5,
        max_tokens=1024,
    )

    tool_calls = response.get("tool_calls", [])
    content = response.get("content", "")

    if tool_calls:
        if content:
            yield {"type": "text", "content": content}

        for tc in tool_calls:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]
            result = _execute_tool(name, args)

            yield {"type": "tool_call", "name": name, "args": args, "result": result}

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function",
                     "function": {"name": name, "arguments": args}}
                ],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": "call_1",
                "content": result,
            })

        for chunk_text in chat_completion_stream(
            messages=messages,
            temperature=0.5,
        ):
            yield {"type": "text", "content": chunk_text}

    elif content:
        yield {"type": "text", "content": content}
    else:
        yield {"type": "text", "content": "Lo siento, no pude procesar tu solicitud."}


def chat_stream(
    user_id: str,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> Generator[str, None, None]:
    """Streaming wrapper compatible con st.write_stream()."""
    for chunk in chat_with_tools(messages, tools):
        if chunk["type"] == "text":
            yield chunk["content"]