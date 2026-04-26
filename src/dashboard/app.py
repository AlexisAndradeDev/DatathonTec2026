"""Entry point del dashboard Streamlit -- Hey Banco - Havi Motor."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.styling import (
    apply_hey_theme, brand_header, data_freshness_indicator,
)
from src.dashboard.utils.data_loader import load_profiles


def _render_sidebar_filters() -> None:
    """Filtros globales en sidebar compartidos entre paginas via session_state."""
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-label">Filtros Globales</div>',
        unsafe_allow_html=True,
    )

    profiles = load_profiles()
    valid = [p for p in profiles if p["cluster_id"] != -1]
    seg_opts = {f"{p['nombre']} ({p['size']:,})": p["cluster_id"] for p in valid}
    seg_names = list(seg_opts.keys())

    if "global_segment_filter" not in st.session_state:
        st.session_state.global_segment_filter = []

    selected_names = st.sidebar.multiselect(
        "Segmentos",
        options=seg_names,
        default=st.session_state.global_segment_filter,
        placeholder="Todos los segmentos",
        key="sidebar_segment_select",
    )
    st.session_state.global_segment_filter = selected_names

    st.session_state.global_segment_ids = [
        seg_opts[n] for n in selected_names
    ] if selected_names else []

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-label">Usuario</div>',
        unsafe_allow_html=True,
    )
    if "global_hey_pro_filter" not in st.session_state:
        st.session_state.global_hey_pro_filter = "Todos"
    st.session_state.global_hey_pro_filter = st.sidebar.radio(
        "Tipo de cliente",
        options=["Todos", "Hey Pro", "Regular"],
        horizontal=False,
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    apply_hey_theme()
    brand_header()

    _render_sidebar_filters()
    data_freshness_indicator()

    pg = st.navigation(
        {
            "Dashboard": [
                st.Page("pages/home.py", title="Home", icon=":material/home:"),
                st.Page("pages/segments.py", title="Segmentos", icon=":material/donut_small:"),
                st.Page("pages/customer_360.py", title="Customer 360", icon=":material/person:"),
                st.Page("pages/chatbot.py", title="Havi Next", icon=":material/forum:"),
                st.Page("pages/analytics.py", title="Analytics", icon=":material/monitoring:"),
            ],
        },
    )
    pg.run()


if __name__ == "__main__":
    main()
