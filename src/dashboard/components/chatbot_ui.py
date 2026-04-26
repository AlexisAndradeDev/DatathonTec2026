"""Chat UI reutilizable para Havi Next — streaming + tool calls colapsables."""

import json
import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.chatbot.agent import chat_with_tools
from src.chatbot.tools import TOOLS_DICT
from src.dashboard.utils.styling import HEY_PRIMARY, HEY_TEAL, HEY_WHITE, HEY_BLACK, HEY_GRAY_TEXT


def render_chat_ui(user_id: str, dna_text: str | None = None,
                   segment_name: str | None = None) -> None:
    """Renderiza la UI completa del chatbot con historial y tool calls."""

    if dna_text or segment_name:
        parts = []
        if segment_name:
            parts.append(f"Segmento: {segment_name}")
        if dna_text:
            parts.append("DNA: cargado")
        st.info(" | ".join(parts))

    if "havi_messages" not in st.session_state:
        dna_prefix = (
            f"[PERFIL DEL CLIENTE {user_id}]\n{dna_text}\n\n"
            if dna_text else ""
        )
        st.session_state.havi_messages = [
            {"role": "system", "content": dna_prefix + (
                "Eres Havi, el asistente virtual inteligente de Hey Banco. "
                "Tu personalidad es empatica, proactiva y experta en finanzas "
                "personales. Siempre personaliza tus respuestas con el contexto "
                "del cliente. Se proactivo: sugiere acciones relevantes. "
                "Manten un tono calido y profesional. Usa 'tu' en espanol "
                "mexicano. Las respuestas deben ser concisas (maximo 2 parrafos). "
                "No inventes informacion financiera. Si necesitas datos concretos, "
                "usa las herramientas disponibles."
            )},
            {"role": "assistant", "content": (
                "Hola! Soy Havi, tu asistente virtual de Hey Banco. "
                "Estoy aqui para ayudarte con tus finanzas. "
                "En que puedo apoyarte hoy?"
            )},
        ]
        st.session_state.tool_calls_cache = {}

    for i, msg in enumerate(st.session_state.havi_messages):
        role = msg["role"]
        if role == "system":
            continue
        content = msg.get("content", "")

        if role == "user" and content:
            with st.chat_message("user", avatar="👤"):
                st.markdown(
                    f'<div style="background:{HEY_PRIMARY};color:{HEY_BLACK};'
                    f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
                    f'max-width:80%;font-weight:500;">{content}</div>',
                    unsafe_allow_html=True,
                )
        elif role == "assistant" and content:
            with st.chat_message("assistant", avatar="💛"):
                st.markdown(
                    f'<div style="background:{HEY_WHITE};border:1px solid {HEY_TEAL};'
                    f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
                    f'max-width:80%;">{content}</div>',
                    unsafe_allow_html=True,
                )

        tc_key = f"tc_{i}"
        if tc_key in st.session_state.tool_calls_cache:
            for tc in st.session_state.tool_calls_cache[tc_key]:
                with st.expander(f"🔧 {tc['name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption("Parametros")
                        st.code(tc["args"], language="json")
                    with col2:
                        st.caption("Resultado")
                        try:
                            parsed = json.loads(tc["result"])
                            st.json(parsed)
                        except Exception:
                            st.text(tc["result"][:500])

    prompt = st.chat_input("Escribe tu mensaje...", key="havi_input")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💰 Ver saldo", use_container_width=True):
            prompt = "Cual es el saldo de mis cuentas y productos?"
    with col2:
        if st.button("📊 Ultimos gastos", use_container_width=True):
            prompt = "Muestrame mis ultimas transacciones"
    with col3:
        if st.button("🎯 Mi recomendacion", use_container_width=True):
            prompt = "Que recomendacion tienes para mi?"

    if not prompt:
        return

    st.session_state.havi_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="👤"):
        st.markdown(
            f'<div style="background:{HEY_PRIMARY};color:{HEY_BLACK};'
            f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
            f'max-width:80%;font-weight:500;">{prompt}</div>',
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant", avatar="💛"):
        placeholder = st.empty()
        text_buffer = ""
        tool_calls_shown = []

        try:
            for chunk in chat_with_tools(
                st.session_state.havi_messages,
                TOOLS_DICT,
            ):
                if chunk["type"] == "text":
                    text_buffer += chunk["content"]
                    placeholder.markdown(
                        f'<div style="background:{HEY_WHITE};border:1px solid {HEY_TEAL};'
                        f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
                        f'max-width:80%;">{text_buffer}</div>',
                        unsafe_allow_html=True,
                    )
                elif chunk["type"] == "tool_call":
                    tool_calls_shown.append(chunk)
                    placeholder.markdown(
                        f'<div style="background:{HEY_WHITE};border:1px solid {HEY_TEAL};'
                        f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
                        f'max-width:80%;">{text_buffer}\n\n🔧 Usando herramienta...</div>',
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            placeholder.error(f"Error: {e}")
            text_buffer = f"Lo siento, ocurrio un error: {e}"

        placeholder.markdown(
            f'<div style="background:{HEY_WHITE};border:1px solid {HEY_TEAL};'
            f'padding:0.4rem 0.8rem;border-radius:12px;display:inline-block;'
            f'max-width:80%;">{text_buffer}</div>',
            unsafe_allow_html=True,
        )

    msg_idx = len(st.session_state.havi_messages)
    if tool_calls_shown:
        st.session_state.tool_calls_cache[f"tc_{msg_idx}"] = tool_calls_shown

    st.session_state.havi_messages.append({
        "role": "assistant",
        "content": text_buffer,
    })

    st.rerun()