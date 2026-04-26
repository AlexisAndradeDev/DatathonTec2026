"""Entry point del dashboard Streamlit — Hey Banco · Havi Motor."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.styling import apply_hey_theme, brand_header


def main() -> None:
    apply_hey_theme()
    brand_header()

    pg = st.navigation(
        {
            "📊 Dashboard": [
                st.Page("pages/home.py", title="🏠 Home"),
                st.Page("pages/segments.py", title="🔍 Segmentos"),
                st.Page("pages/customer_360.py", title="👤 Customer 360"),
                st.Page("pages/chatbot.py", title="💬 Havi Next"),
                st.Page("pages/analytics.py", title="📈 Analytics"),
            ],
        },
    )
    pg.run()


if __name__ == "__main__":
    main()