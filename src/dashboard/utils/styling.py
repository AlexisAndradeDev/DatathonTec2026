"""Tema monocromatico blanco/negro -- paleta de colores y CSS global para Streamlit."""

import streamlit as st
from datetime import datetime


# ── Tokens de color ────────────────────────────────────────────────────
HEY_PRIMARY = "#1A1A1A"
HEY_BLACK = "#1A1A1A"
HEY_WHITE = "#FFFFFF"
HEY_TEAL = "#444444"
HEY_CORAL = "#777777"
HEY_LIME = "#CCCCCC"
HEY_GRAY_BG = "#F4F4F5"
HEY_GRAY_TEXT = "#6B6B6B"
HEY_CARD_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.08)"
HEY_HOVER_SHADOW = "0 4px 16px rgba(0, 0, 0, 0.12)"


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convierte hex (#RRGGBB o #RGB) a rgba(r, g, b, alpha)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def apply_hey_theme() -> None:
    """Inyecta CSS global + configuracion de pagina con tema Hey Banco."""

    st.set_page_config(
        page_title="Hey Banco | Havi Motor",
        page_icon="🔷",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* ── Global ─────────────────────────────────── */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 15px;
        }}
        .main .block-container {{
            background-color: {HEY_GRAY_BG};
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }}

        /* ── Sidebar ────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background-color: {HEY_BLACK};
        }}
        [data-testid="stSidebar"] * {{
            color: {HEY_WHITE};
        }}
        [data-testid="stSidebarContent"] {{
            display: flex;
            flex-direction: column;
        }}
        [data-testid="stSidebar"] .st-emotion-cache-1d8cy3q {{
            background-color: transparent;
        }}
        [data-testid="stSidebarNavLink"] {{
            border-left: 3px solid transparent;
            transition: border-left 0.2s ease;
            border-radius: 0 8px 8px 0;
            padding: 0.6rem 1rem;
            font-weight: 500;
            margin: 2px 0;
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            border-left: 3px solid {HEY_WHITE};
            background-color: rgba(255, 255, 255, 0.12);
        }}
        [data-testid="stSidebarNavLink"]:hover {{
            background-color: rgba(255, 255, 255, 0.08);
        }}

        /* ── Sidebar Sections ───────────────────────── */
        .sidebar-section {{
            border-top: 1px solid rgba(255,255,255,0.12);
            padding: 1rem 0.5rem;
            margin-top: 0.5rem;
        }}
        .sidebar-label {{
            color: {HEY_GRAY_TEXT};
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.75rem;
        }}

        /* ── Sidebar Brand ──────────────────────────── */
        .hey-brand {{
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.35rem;
            color: {HEY_PRIMARY};
            padding: 0.75rem 0.5rem 0.25rem 0.5rem;
            letter-spacing: -0.5px;
        }}
        .hey-brand-sub {{
            color: {HEY_GRAY_TEXT};
            font-size: 0.72rem;
            padding: 0 0.5rem 0.75rem 0.5rem;
            font-weight: 400;
        }}

        /* ── Data Freshness ──────────────────────────── */
        .data-freshness {{
            font-size: 0.65rem;
            color: {HEY_GRAY_TEXT};
            padding: 0.75rem 0.5rem;
            margin-top: auto;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .freshness-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {HEY_TEAL};
            display: inline-block;
        }}

        /* ── KPI Cards ───────────────────────────────── */
        .kpi-card {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            box-shadow: {HEY_CARD_SHADOW};
            border-top: 3px solid {HEY_PRIMARY};
            margin-bottom: 0.5rem;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }}
        .kpi-card:hover {{
            box-shadow: {HEY_HOVER_SHADOW};
            transform: translateY(-1px);
        }}
        .kpi-card .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {HEY_BLACK};
            line-height: 1.2;
        }}
        .kpi-card .kpi-label {{
            font-size: 0.72rem;
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

        /* ── KPI Card with Sparkline ─────────────────── */
        .kpi-spark {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1rem 1.25rem;
            box-shadow: {HEY_CARD_SHADOW};
            border-top: 3px solid {HEY_PRIMARY};
            margin-bottom: 0.5rem;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }}
        .kpi-spark:hover {{
            box-shadow: {HEY_HOVER_SHADOW};
            transform: translateY(-1px);
        }}
        .kpi-spark .kpi-spark-value {{
            font-size: 1.7rem;
            font-weight: 700;
            color: {HEY_BLACK};
            line-height: 1.1;
        }}
        .kpi-spark .kpi-spark-label {{
            font-size: 0.68rem;
            font-weight: 600;
            color: {HEY_GRAY_TEXT};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .kpi-spark .kpi-spark-delta {{
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .kpi-spark-delta.up {{ color: {HEY_TEAL}; }}
        .kpi-spark-delta.down {{ color: {HEY_CORAL}; }}

        /* ── Hero Section ─────────────────────────────── */
        .hero-section {{
            background: linear-gradient(135deg, #1A1A1A, #333333);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .hero-title {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {HEY_WHITE} !important;
            letter-spacing: -0.5px;
            margin-bottom: 0.3rem;
        }}
        .hero-subtitle {{
            font-size: 0.95rem;
            color: {HEY_GRAY_TEXT} !important;
            font-weight: 400;
        }}

        /* ── Generic Card ─────────────────────────────── */
        .hey-card {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: {HEY_CARD_SHADOW};
            margin-bottom: 1rem;
            transition: box-shadow 0.2s ease;
        }}
        .hey-card:hover {{
            box-shadow: {HEY_HOVER_SHADOW};
        }}

        /* ── Buttons ──────────────────────────────────── */
        .stButton > button {{
            background-color: {HEY_PRIMARY};
            color: {HEY_WHITE};
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.25rem;
            transition: background-color 0.15s ease, transform 0.1s ease;
        }}
        .stButton > button:hover {{
            background-color: #333333;
            color: {HEY_WHITE};
            transform: translateY(-1px);
        }}
        .stButton > button:active {{
            transform: translateY(0);
        }}

        /* ── Secondary Button ──────────────────────────── */
        .btn-secondary > button {{
            background-color: {HEY_WHITE};
            color: {HEY_BLACK};
            border: 1.5px solid #ddd;
            font-weight: 600;
        }}
        .btn-secondary > button:hover {{
            background-color: {HEY_GRAY_BG};
            border-color: {HEY_PRIMARY};
            color: {HEY_BLACK};
        }}

        /* ── Tags / Badges ────────────────────────────── */
        .hey-tag {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 0.4rem;
            margin-bottom: 0.3rem;
        }}
        .hey-tag.pro {{ background: {HEY_LIME}; color: {HEY_BLACK}; }}
        .hey-tag.alerta {{ background: {HEY_CORAL}; color: {HEY_WHITE}; }}
        .hey-tag.cashback {{ background: {HEY_TEAL}; color: {HEY_WHITE}; }}
        .hey-tag.teal {{ background: {HEY_TEAL}; color: {HEY_WHITE}; }}
        .hey-tag.gray {{ background: #E5E5E5; color: {HEY_BLACK}; }}

        /* ── Chat Bubbles ─────────────────────────────── */
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

        /* ── Suggested Chips ──────────────────────────── */
        .suggested-chips {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }}

        /* ── Select / Input Overrides ──────────────────── */
        [data-baseweb="select"] {{
            border-radius: 8px;
        }}

        /* ── DataFrame / Table ────────────────────────── */
        [data-testid="stTable"] {{
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ── Tool Call Card (inline) ──────────────────── */
        .tool-inline {{
            background: #F8F9FA;
            border-radius: 10px;
            padding: 0.6rem 1rem;
            margin: 0.4rem 0;
            border: 1px solid #e8e8e8;
            font-size: 0.82rem;
        }}
        .tool-inline-header {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            color: {HEY_GRAY_TEXT};
            font-weight: 600;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 0.3rem;
        }}

        /* ── Tab Override ──────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background: transparent;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px 8px 0 0;
            padding: 0.6rem 1.25rem;
            font-weight: 600;
            font-size: 0.85rem;
            color: {HEY_GRAY_TEXT};
        }}
        .stTabs [aria-selected="true"] {{
            background: {HEY_WHITE};
            color: {HEY_BLACK};
            box-shadow: 0 -2px 0 {HEY_PRIMARY};
        }}

        /* ── Skeleton Loading ──────────────────────────── */
        @keyframes shimmer {{
            0% {{ background-position: -400px 0; }}
            100% {{ background-position: 400px 0; }}
        }}
        .skeleton {{
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 800px 100%;
            animation: shimmer 1.5s infinite ease-in-out;
            border-radius: 8px;
        }}
        .skeleton-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .skeleton-card {{
            height: 100px;
            border-radius: 12px;
        }}
        .skeleton-chart {{
            height: 280px;
            border-radius: 12px;
            margin-bottom: 1rem;
        }}
        .skeleton-text {{
            height: 14px;
            margin-bottom: 8px;
            width: 70%;
        }}
        .skeleton-text.short {{
            width: 40%;
        }}

        /* ── Score Gauge ───────────────────────────────── */
        .gauge-wrapper {{
            background: {HEY_WHITE};
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: {HEY_CARD_SHADOW};
            text-align: center;
        }}
        .gauge-label {{
            color: {HEY_GRAY_TEXT};
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* ── Avatar Circle ─────────────────────────────── */
        .avatar-circle {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, {HEY_BLACK}, {HEY_GRAY_TEXT});
            color: {HEY_WHITE};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            font-weight: 700;
            flex-shrink: 0;
        }}

        /* ── Product Card ──────────────────────────────── */
        .product-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .product-icon.credito {{ background: {hex_to_rgba(HEY_CORAL, 0.13)}; color: {HEY_CORAL}; }}
        .product-icon.debito {{ background: {hex_to_rgba(HEY_TEAL, 0.13)}; color: {HEY_TEAL}; }}
        .product-icon.inversion {{ background: {hex_to_rgba(HEY_PRIMARY, 0.27)}; color: {HEY_BLACK}; }}
        .product-icon.nomina {{ background: {hex_to_rgba(HEY_LIME, 0.27)}; color: {HEY_BLACK}; }}
        .product-icon.default {{ background: {HEY_GRAY_BG}; color: {HEY_GRAY_TEXT}; }}

        /* ── Divider ───────────────────────────────────── */
        .hey-divider {{
            height: 1px;
            background: #e8e8e8;
            margin: 1.25rem 0;
        }}

        /* ── Typing Indicator ──────────────────────────── */
        @keyframes typingBounce {{
            0%, 80%, 100% {{ transform: scale(0); opacity: 0.3; }}
            40% {{ transform: scale(1); opacity: 1; }}
        }}
        .typing-dots {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 0.5rem 1rem;
        }}
        .typing-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {HEY_TEAL};
            display: inline-block;
        }}
        .typing-dot:nth-child(1) {{ animation: typingBounce 1.4s infinite ease-in-out; }}
        .typing-dot:nth-child(2) {{ animation: typingBounce 1.4s infinite ease-in-out 0.2s; }}
        .typing-dot:nth-child(3) {{ animation: typingBounce 1.4s infinite ease-in-out 0.4s; }}

        /* ── Quick Action Card ─────────────────────────── */
        .quick-action {{
            background: {HEY_WHITE};
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #e8e8e8;
            cursor: pointer;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        .quick-action:hover {{
            border-color: {HEY_PRIMARY};
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
        }}
        .quick-action-icon {{
            font-size: 1.5rem;
            margin-bottom: 0.4rem;
        }}
        .quick-action-label {{
            font-size: 0.82rem;
            font-weight: 600;
            color: {HEY_BLACK};
        }}
        .quick-action-desc {{
            font-size: 0.7rem;
            color: {HEY_GRAY_TEXT};
            margin-top: 0.15rem;
        }}

        /* ── Info Box ──────────────────────────────────── */
        .info-box {{
            background: {hex_to_rgba(HEY_PRIMARY, 0.09)};
            border-left: 4px solid {HEY_PRIMARY};
            padding: 0.75rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            color: {HEY_BLACK};
            margin: 0.5rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_header() -> None:
    """Renderiza el header de marca en la sidebar."""
    st.sidebar.markdown(
        '<div class="hey-brand">Hey Banco</div>'
        '<div class="hey-brand-sub">Havi Motor - Inteligencia & Atencion</div>',
        unsafe_allow_html=True,
    )


def data_freshness_indicator() -> None:
    """Muestra indicador de ultima actualizacion en sidebar."""
    from src.dashboard.utils.data_loader import get_data_timestamp
    ts = get_data_timestamp()
    st.sidebar.markdown(
        f'<div class="data-freshness">'
        f'<span class="freshness-dot"></span> Datos: {ts}'
        f'</div>',
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


def sparkline_kpi_card(label: str, value: str, delta: str = "",
                       delta_up: bool = True) -> None:
    """Renderiza una tarjeta KPI con area para sparkline via st.plotly_chart."""
    cls = "up" if delta_up else "down"
    delta_sign = "+" if delta_up else ""
    st.markdown(
        f"""
        <div class="kpi-spark">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="kpi-spark-label">{label}</div>
                    <div class="kpi-spark-value">{value}</div>
                    <div class="kpi-spark-delta {cls}">{delta_sign}{delta}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def loading_skeleton_kpis() -> None:
    """Renderiza un skeleton placeholder para KPI cards."""
    st.markdown("""
        <div class="skeleton-row">
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
        </div>
    """, unsafe_allow_html=True)


def loading_skeleton_chart(height: int = 280) -> None:
    """Renderiza un skeleton placeholder para chart."""
    st.markdown(
        f'<div class="skeleton skeleton-chart" style="height:{height}px;"></div>',
        unsafe_allow_html=True,
    )


def hero_section(title: str, subtitle: str = "") -> None:
    """Renderiza una seccion hero con titulo y subtitulo."""
    st.markdown(
        f"""
        <div class="hero-section">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(text: str) -> None:
    """Caja de informacion con borde amarillo."""
    st.markdown(f'<div class="info-box">{text}</div>', unsafe_allow_html=True)


def section_divider() -> None:
    """Divisor visual entre secciones."""
    st.markdown('<div class="hey-divider"></div>', unsafe_allow_html=True)
