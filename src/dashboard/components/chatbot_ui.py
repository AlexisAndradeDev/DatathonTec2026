"""Chat UI reutilizable para Havi Next -- streaming + tool calls inline."""

import os
import sys
import time

sys.path.insert(0, os.getcwd())

import polars as pl
import streamlit as st

from src.chatbot.agent import chat_with_tools
from src.chatbot.tools import TOOLS_DICT
from src.dashboard.utils.styling import (
    HEY_PRIMARY, HEY_TEAL, HEY_WHITE, HEY_BLACK, HEY_GRAY_TEXT,
)


def _on_chip_click(prompt: str) -> None:
    """Callback para chips de accion rapida: guarda el prompt en session state."""
    st.session_state.chatbot_prompt_override = prompt


def _make_initials(row: dict) -> str:
    uid = row.get("user_id", "U")
    parts = uid.split("-") if uid else []
    letters = "ABCDEFGH"
    if len(parts) >= 2 and parts[-1].isdigit():
        n = int(parts[-1])
        return f"{parts[0][0]}{letters[n % 8]}"
    return uid[:2].upper()


def _render_client_preview(user_id: str, user_row,
                           segment_name: str | None,
                           dna_text: str | None) -> None:
    row = {c: user_row[c][0] for c in user_row.columns}
    initials = _make_initials(row)
    edad = row.get("edad", "?")
    ingreso = row.get("ingreso_mensual_mxn", 0)
    score = row.get("score_buro", "?")
    sat = row.get("satisfaccion_1_10", "?")

    dna_snippet = ""
    if dna_text:
        dna_snippet = dna_text[:120] + "..." if len(dna_text) > 120 else dna_text

    st.markdown(
        f"""
        <div style="background:{HEY_WHITE};border-radius:12px;padding:1rem 1.25rem;
        box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:0.75rem;
        display:flex;align-items:flex-start;gap:0.75rem;">
            <div class="avatar-circle">{initials}</div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:700;font-size:0.95rem;color:{HEY_BLACK};">
                {user_id}</div>
                <div style="margin-top:0.15rem;">
                    {f'<span class="hey-tag cashback">{segment_name}</span>' if segment_name else ''}
                </div>
                <div style="font-size:0.75rem;color:{HEY_GRAY_TEXT};margin-top:0.3rem;">
                {edad} anos · ${ingreso:,}/mes · Score {score} · Satisfaccion {sat}/10</div>
                {f'<div style="font-size:0.75rem;color:{HEY_GRAY_TEXT};margin-top:0.15rem;line-height:1.4;">{dna_snippet}</div>' if dna_snippet else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _get_suggested_prompts(segment_name: str | None) -> list[dict]:
    """Genera prompts sugeridos segun el segmento del cliente."""
    common = [
        {"label": "Ver saldo", "prompt": "Cual es el saldo de mis cuentas y productos?",
         "icon": ":material/account_balance:"},
        {"label": "Ultimos gastos", "prompt": "Muestrame mis ultimas transacciones",
         "icon": ":material/receipt_long:"},
        {"label": "Mi recomendacion", "prompt": "Que recomendacion tienes para mi?",
         "icon": ":material/auto_awesome:"},
    ]
    if segment_name:
        common.append({
            "label": "Sobre mi segmento",
            "prompt": f"Pertenezco al segmento '{segment_name}', que significa eso para mis finanzas?",
            "icon": ":material/donut_small:",
        })
    return common


def render_chat_ui(user_id: str, dna_text: str | None = None,
                   segment_name: str | None = None,
                   user_row: pl.DataFrame | None = None) -> None:
    """Renderiza la UI completa del chatbot con historial y tool calls."""

    if user_row is not None and user_row.shape[0] > 0:
        _render_client_preview(user_id, user_row, segment_name, dna_text)

    # ── Suggested prompts ─────────────────────────────
    st.markdown('<div class="suggested-chips">', unsafe_allow_html=True)
    suggestions = _get_suggested_prompts(segment_name)
    cols = st.columns(len(suggestions))
    for i, sug in enumerate(suggestions):
        with cols[i]:
            st.button(
                f"{sug['icon']}  {sug['label']}",
                key=f"chip_{user_id}_{i}",
                on_click=_on_chip_click,
                kwargs={"prompt": sug["prompt"]},
                use_container_width=True,
                help=sug["prompt"],
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Initialize messages ───────────────────────────
    if "havi_messages" not in st.session_state:
        dna_prefix = (
            f"[PERFIL DEL CLIENTE {user_id}]\n{dna_text}\n\n"
            if dna_text else ""
        )
        st.session_state.havi_messages = [
            {"role": "system", "content": dna_prefix + (
                "Eres Havi, el asistente virtual inteligente de Hey Banco. "
                f"El cliente actual es {user_id}. Cuando necesites datos "
                "concretos (saldo, transacciones, recomendaciones), "
                "usa las herramientas disponibles pasando este user_id. "
                "NUNCA menciones que estas usando herramientas ni "
                "procesos internos. Responde de forma natural como si "
                "ya tuvieras la informacion. "
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
                + (f"Eres parte del segmento {segment_name}. " if segment_name else "")
                + "Estoy aqui para ayudarte con tus finanzas. "
                "En que puedo apoyarte hoy?"
            )},
        ]

    # ── Render message history ────────────────────────
    for i, msg in enumerate(st.session_state.havi_messages):
        role = msg["role"]
        if role == "system":
            continue
        content = msg.get("content", "")

        # style
        style_parts = "padding:0.6rem 1rem;border-radius:14px;max-width:80%;"
        if role == "user" and content:
            style_str = f"background:{HEY_PRIMARY};color:{HEY_WHITE};{style_parts}font-weight:500;"
        elif role == "assistant" and content:
            style_str = f"background:{HEY_WHITE};border:1.5px solid {HEY_TEAL};color:{HEY_BLACK};{style_parts}"
        else:
            style_str = ""

        if role == "user" and content:
            with st.chat_message("user", avatar=":material/person:"):
                st.markdown(
                    f'<div style="{style_str}">{content}</div>',
                    unsafe_allow_html=True,
                )
        elif role == "assistant" and content:
            with st.chat_message("assistant", avatar=":material/smart_toy:"):
                st.markdown(
                    f'<div style="{style_str}">{content}</div>',
                    unsafe_allow_html=True,
                )

    # ── Chat input ────────────────────────────────────
    prompt = st.chat_input("Escribe tu mensaje...", key="havi_input")

    # Check for chip override (set via callback)
    if st.session_state.get("chatbot_prompt_override"):
        prompt = st.session_state.pop("chatbot_prompt_override")

    if not prompt:
        return

    # ── Process user message ──────────────────────────
    st.session_state.havi_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(
            f'<div style="background:{HEY_PRIMARY};color:{HEY_WHITE};'
            f'padding:0.6rem 1rem;border-radius:14px;display:inline-block;'
            f'max-width:80%;font-weight:500;">{prompt}</div>',
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        placeholder = st.empty()
        text_buffer = ""
        showing_typing = True

        # Show typing indicator
        placeholder.markdown(
            '<div style="display:inline-flex;align-items:center;gap:4px;'
            f'padding:0.5rem 1rem;">'
            f'<span class="typing-dot"></span>'
            f'<span class="typing-dot"></span>'
            f'<span class="typing-dot"></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        try:
            for chunk in chat_with_tools(
                st.session_state.havi_messages,
                TOOLS_DICT,
            ):
                if chunk["type"] == "text":
                    if showing_typing:
                        showing_typing = False
                    words = chunk["content"].split(" ")
                    for i, word in enumerate(words):
                        if i > 0:
                            text_buffer += " "
                        text_buffer += word
                        placeholder.markdown(
                            f'<div style="background:{HEY_WHITE};'
                            f'border:1.5px solid {HEY_TEAL};'
                            f'padding:0.6rem 1rem;border-radius:14px;'
                            f'display:inline-block;max-width:80%;'
                            f'color:{HEY_BLACK};">'
                            f'{text_buffer}</div>',
                            unsafe_allow_html=True,
                        )
                        time.sleep(0.03)
                elif chunk["type"] == "tool_call":
                    showing_typing = False
                    placeholder.markdown(
                        f'<div style="background:{HEY_WHITE};'
                        f'border:1.5px solid {HEY_TEAL};'
                        f'padding:0.6rem 1rem;border-radius:14px;'
                        f'display:inline-block;max-width:80%;'
                        f'color:{HEY_BLACK};">'
                        f'{text_buffer}\n\n'
                        f'<span style="color:{HEY_GRAY_TEXT};font-size:0.8rem;">'
                        f'Consultando tus datos...</span></div>',
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            placeholder.error(f"Error: {e}")
            text_buffer = f"Lo siento, ocurrio un error: {e}"

        # Final text
        placeholder.markdown(
            f'<div style="background:{HEY_WHITE};'
            f'border:1.5px solid {HEY_TEAL};'
            f'padding:0.6rem 1rem;border-radius:14px;'
            f'display:inline-block;max-width:80%;'
            f'color:{HEY_BLACK};">'
            f'{text_buffer}</div>',
            unsafe_allow_html=True,
        )

    st.session_state.havi_messages.append({
        "role": "assistant",
        "content": text_buffer,
    })

    st.rerun()
