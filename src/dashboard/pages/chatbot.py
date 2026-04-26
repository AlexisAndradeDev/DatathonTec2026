"""Pagina Havi Next -- Chatbot RAG con streaming y tool calling."""

import os
import sys

sys.path.insert(0, os.getcwd())

import polars as pl
import streamlit as st

from src.dashboard.utils.data_loader import (
    get_user_ids, get_profile_for_user, get_dna_for_user,
    load_clients,
)
from src.dashboard.components.chatbot_ui import render_chat_ui


def run_chatbot() -> None:
    st.title("Havi Next")
    st.caption("Asistente virtual inteligente de Hey Banco  ·  Streaming + RAG")

    user_ids = get_user_ids()

    preselected = st.session_state.pop("chatbot_preselected", None)
    default_idx = None
    if preselected and preselected in user_ids:
        default_idx = user_ids.index(preselected)

    selected = st.selectbox(
        "Seleccionar cliente",
        options=user_ids,
        index=default_idx,
        placeholder="Elige un usuario USR-XXXXX...",
        key="chatbot_user_selector",
    )

    if not selected:
        st.info("Selecciona un cliente para iniciar la conversacion con Havi.")
        return

    if "chatbot_current_user" not in st.session_state:
        st.session_state.chatbot_current_user = None

    if st.session_state.chatbot_current_user != selected:
        st.session_state.chatbot_current_user = selected
        st.session_state.pop("havi_messages", None)
        st.session_state.pop("chatbot_prompt_override", None)

    dna = get_dna_for_user(selected)
    profile = get_profile_for_user(selected)
    segment_name = profile["nombre"] if profile else None

    clients = load_clients()
    user_row = clients.filter(pl.col("user_id") == selected)

    render_chat_ui(selected, dna, segment_name, user_row)


run_chatbot()
