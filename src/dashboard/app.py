"""Entry point del dashboard Streamlit -- Hey Banco - Havi Motor."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.styling import (
    apply_hey_theme, brand_header, data_freshness_indicator,
)


def main() -> None:
    apply_hey_theme()
    brand_header()

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
