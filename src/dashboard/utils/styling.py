"""Tema Hey Banco — paleta de colores oficial y CSS global para Streamlit."""

import streamlit as st


# ── Tokens de color ────────────────────────────────────────────────────
HEY_PRIMARY = "#FFD400"
HEY_BLACK = "#1A1A1A"
HEY_WHITE = "#FFFFFF"
HEY_TEAL = "#00C9A7"
HEY_CORAL = "#FF4F6D"
HEY_LIME = "#C6F135"
HEY_GRAY_BG = "#F4F4F5"
HEY_GRAY_TEXT = "#6B6B6B"
HEY_CARD_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.08)"


def apply_hey_theme() -> None:
    """Inyecta CSS global + configuración de página con tema Hey Banco."""

    st.set_page_config(
        page_title="Hey Banco | Havi Motor",
        page_icon="💛",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        /* ── Global ─────────────────────────────────── */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        .main .block-container {{
            background-color: {HEY_GRAY_BG};
            padding-top: 1.5rem;
        }}

        /* ── Sidebar ────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background-color: {HEY_BLACK};
        }}
        [data-testid="stSidebar"] * {{
            color: {HEY_WHITE};
        }}
        [data-testid="stSidebar"] .st-emotion-cache-1d8cy3q {{
            background-color: transparent;
        }}
        [data-testid="stSidebarNavLink"] {{
            border-left: 3px solid transparent;
            transition: border-left 0.2s;
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            border-left: 3px solid {HEY_PRIMARY};
            background-color: rgba(255, 212, 0, 0.12);
        }}

        /* ── Sidebar brand ──────────────────────────── */
        .hey-brand {{
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.25rem;
            color: {HEY_PRIMARY};
            padding: 1rem 0.5rem 0.5rem 0.5rem;
            letter-spacing: -0.5px;
        }}

        /* ── KPI Cards ───────────────────────────────── */
        .kpi-card {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            box-shadow: {HEY_CARD_SHADOW};
            border-top: 3px solid {HEY_PRIMARY};
            margin-bottom: 0.5rem;
        }}
        .kpi-card .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {HEY_BLACK};
            line-height: 1.2;
        }}
        .kpi-card .kpi-label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: {HEY_GRAY_TEXT};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 0.25rem;
        }}
        .kpi-card .kpi-delta {{
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }}
        .kpi-delta.positive {{ color: {HEY_TEAL}; }}
        .kpi-delta.negative {{ color: {HEY_CORAL}; }}

        /* ── Card genérica ───────────────────────────── */
        .hey-card {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: {HEY_CARD_SHADOW};
            margin-bottom: 1rem;
        }}

        /* ── Botones ─────────────────────────────────── */
        .stButton > button {{
            background-color: {HEY_PRIMARY};
            color: {HEY_BLACK};
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.25rem;
            transition: 0.15s;
        }}
        .stButton > button:hover {{
            background-color: #e6c200;
            color: {HEY_BLACK};
        }}

        /* ── Tags / Badges ───────────────────────────── */
        .hey-tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 0.4rem;
        }}
        .hey-tag.pro {{ background: {HEY_LIME}; color: {HEY_BLACK}; }}
        .hey-tag.alerta {{ background: {HEY_CORAL}; color: {HEY_WHITE}; }}
        .hey-tag.cashback {{ background: {HEY_TEAL}; color: {HEY_WHITE}; }}
        .hey-tag.teal {{ background: {HEY_TEAL}; color: {HEY_WHITE}; }}

        /* ── Chat bubbles ────────────────────────────── */
        .chat-message {{
            padding: 0.75rem 1rem;
            border-radius: 14px;
            margin: 0.5rem 0;
            max-width: 85%;
            line-height: 1.5;
            font-size: 0.95rem;
        }}
        .chat-user {{
            background: {HEY_PRIMARY};
            color: {HEY_BLACK};
            margin-left: auto;
            font-weight: 500;
        }}
        .chat-havi {{
            background: {HEY_WHITE};
            border: 1.5px solid {HEY_TEAL};
            margin-right: auto;
            color: {HEY_BLACK};
        }}

        /* ── Chat input container ────────────────────── */
        .suggested-chips {{
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
            flex-wrap: wrap;
        }}
        .suggested-chips button {{
            background: {HEY_WHITE};
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: 0.15s;
            font-family: 'Inter', sans-serif;
        }}
        .suggested-chips button:hover {{
            border-color: {HEY_PRIMARY};
            background: #FFF9E0;
        }}

        /* ── Select / Input overrides ────────────────── */
        [data-baseweb="select"] {{
            border-radius: 8px;
        }}

        /* ── DataFrame / Table ───────────────────────── */
        [data-testid="stTable"] {{
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ── Expander (tool calls) ───────────────────── */
        .tool-expander {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 0.5rem 0;
            overflow: hidden;
        }}
        .tool-expander-header {{
            background: #F8F8F8;
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            font-weight: 600;
            color: {HEY_GRAY_TEXT};
            cursor: pointer;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_header() -> None:
    """Renderiza el header de marca en la sidebar."""
    import streamlit as st
    st.sidebar.markdown(
        '<div class="hey-brand">💛 Hey Banco</div>'
        '<div style="color:#6B6B6B;font-size:0.75rem;padding:0 0.5rem 1rem 0.5rem;">'
        'Havi Motor · Inteligencia & Atención</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = "", icon: str = "") -> None:
    """Renderiza una tarjeta KPI con estilo Hey Banco."""
    delta_html = ""
    if delta:
        cls = "positive" if delta.startswith("+") else "negative"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">{icon} {value}</div>
            <div class="kpi-label">{label}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
