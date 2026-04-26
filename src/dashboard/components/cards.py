"""Componentes de tarjeta: segmento, DNA, metricas, gauge, productos."""

import streamlit as st

from src.dashboard.utils.styling import (
    HEY_BLACK, HEY_GRAY_TEXT, HEY_PRIMARY, HEY_TEAL,
    HEY_CORAL, HEY_LIME, HEY_WHITE,
    hex_to_rgba,
)


def segment_card(profile: dict) -> None:
    """Tarjeta de perfil de segmento con visual bars."""
    name = profile.get("nombre", "?")
    size = profile.get("size", 0)
    pct = profile.get("pct", 0)
    desc = profile.get("descripcion", "")
    needs = profile.get("necesidades", [])
    action = profile.get("accion_proactiva", "")
    stats = profile.get("estadisticas", {})
    top_feats = profile.get("top_features", [])

    st.markdown("---")
    st.subheader(name)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tamano", f"{size:,}", f"{pct}% del total")
        st.metric("Edad promedio", f"{stats.get('edad_promedio','?')} anos")
        st.metric("Ingreso promedio", f"${stats.get('ingreso_promedio','?'):,.0f} MXN")
        st.metric("Hey Pro", f"{stats.get('hey_pro_pct','?')}%")
    with col2:
        st.metric("Score Buro", f"{stats.get('score_buro_promedio','?')}")
        st.metric("Satisfaccion", f"{stats.get('satisfaccion_promedio','?')}/10")
        st.metric("Antiguedad", f"{stats.get('antiguedad_promedio','?'):,.0f} dias")
        st.metric("Conversaciones", f"{stats.get('conversaciones_promedio','?')}")

    st.markdown(f"**Descripcion:** {desc}")

    if needs:
        st.markdown("**Necesidades implicitas:**")
        for n in needs:
            st.markdown(f"- {n}")

    if action:
        st.info(f"Accion proactiva: {action}")

    if top_feats:
        st.markdown("**Top features discriminantes:**")
        import altair as alt
        import pandas as pd

        feat_df = pd.DataFrame([
            {"feature": f["feature"], "z_score": abs(f["z_score"]),
             "dir": "mayor" if f["direction"] == "mayor" else "menor"}
            for f in top_feats[:8]
        ])
        bar = (
            alt.Chart(feat_df)
            .mark_bar(color=HEY_PRIMARY)
            .encode(
                y=alt.Y("feature:N", sort="-x", title=None),
                x=alt.X("z_score:Q", title="|Z-score|"),
                tooltip=["feature", "z_score", "dir"],
            )
            .properties(height=200)
        )
        st.altair_chart(bar, use_container_width=True)


def dna_card(text: str) -> None:
    """Tarjeta de Customer DNA narrativo."""
    st.markdown(
        f"""
        <div style="background:{HEY_WHITE};border-radius:12px;padding:1.5rem;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid {HEY_TEAL};
        margin:1rem 0;">
        <div style="color:{HEY_GRAY_TEXT};font-size:0.7rem;font-weight:700;
        text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">
        Customer DNA</div>
        <div style="color:{HEY_BLACK};font-size:0.9rem;line-height:1.6;">
        {text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def demographic_card(user_row: dict) -> None:
    """Tarjeta de datos demograficos del usuario con avatar."""
    initials = _get_initials(user_row)
    items = [
        ("Edad", user_row.get("edad")),
        ("Genero", user_row.get("sexo")),
        ("Estado", user_row.get("estado") or "--"),
        ("Ciudad", user_row.get("ciudad") or "--"),
        ("Ocupacion", user_row.get("ocupacion")),
        ("Educacion", user_row.get("nivel_educativo")),
        ("Ingreso", f"${user_row.get('ingreso_mensual_mxn',0):,}/mes"),
        ("Idioma", user_row.get("idioma_preferido", "es_MX")),
    ]
    rows = []
    for label, val in items:
        rows.append(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:0.3rem 0;border-bottom:1px solid #f0f0f0;">'
            f'<span style="color:{HEY_GRAY_TEXT};font-size:0.8rem;">{label}</span>'
            f'<span style="color:{HEY_BLACK};font-weight:600;font-size:0.85rem;">{val}</span>'
            f'</div>'
        )
    st.markdown(
        f"""
        <div style="background:{HEY_WHITE};border-radius:12px;padding:1.25rem 1.5rem;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);margin:0.5rem 0;">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
            <div class="avatar-circle">{initials}</div>
            <div>
                <div style="font-weight:700;font-size:1rem;color:{HEY_BLACK};">
                {user_row.get('user_id','')}</div>
                <div style="color:{HEY_GRAY_TEXT};font-size:0.72rem;">
                Datos demograficos</div>
            </div>
        </div>
        {''.join(rows)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_gauge(score: float, label: str = "Salud Financiera") -> None:
    """Gauge circular de health score (0-100)."""
    import plotly.graph_objects as go

    clamped = max(0, min(100, score))
    if clamped >= 70:
        color = HEY_TEAL
    elif clamped >= 40:
        color = HEY_PRIMARY
    else:
        color = HEY_CORAL

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=clamped,
        number={"font": {"size": 32, "family": "Inter, sans-serif", "color": HEY_BLACK}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickfont": {"size": 0}},
            "bar": {"color": color, "thickness": 0.2},
            "bgcolor": "#f0f0f0",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": hex_to_rgba(HEY_CORAL, 0.13)},
                {"range": [40, 70], "color": hex_to_rgba(HEY_PRIMARY, 0.13)},
                {"range": [70, 100], "color": hex_to_rgba(HEY_TEAL, 0.13)},
            ],
        },
        title={"text": label, "font": {"size": 13, "family": "Inter, sans-serif",
                                         "color": HEY_GRAY_TEXT}},
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def product_card(tipo: str, saldo: float = 0, limite: float = 0,
                 utilizacion: float = 0, estatus: str = "activa",
                 tasa: float = 0) -> None:
    """Tarjeta visual para un producto financiero."""
    tipo_lower = tipo.lower().replace(" ", "_")
    icon_map = {
        "tarjeta_de_credito": ("C", "credito"),
        "tarjeta_de_debito": ("D", "debito"),
        "cuenta_de_inversion": ("I", "inversion"),
        "cuenta_de_nomina": ("N", "nomina"),
    }
    letter, cls = icon_map.get(tipo_lower, ("?", "default"))

    saldo_fmt = f"${saldo:,.0f}" if saldo else "--"
    limite_fmt = f"${limite:,.0f}" if limite else "--"

    st.markdown(
        f"""
        <div style="background:{HEY_WHITE};border-radius:10px;padding:0.85rem 1rem;
        box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:0.5rem;
        display:flex;align-items:center;gap:0.75rem;
        border:1px solid #f0f0f0;transition:box-shadow 0.2s ease;"
        onmouseover="this.style.boxShadow='0 2px 12px rgba(0,0,0,0.1)'"
        onmouseout="this.style.boxShadow='0 1px 4px rgba(0,0,0,0.06)'">
            <div class="product-icon {cls}">{letter}</div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:0.85rem;color:{HEY_BLACK};">
                {tipo.replace('_',' ').title()}</div>
                <div style="font-size:0.72rem;color:{HEY_GRAY_TEXT};">
                Saldo: {saldo_fmt} &nbsp;|&nbsp; Limite: {limite_fmt}
                {f"&nbsp;|&nbsp; Tasa: {tasa:.1f}%" if tasa else ""}</div>
            </div>
            <div>
                <span class="hey-tag {'teal' if estatus == 'activa' else 'gray'}">{estatus}</span>
                {f'<span style="font-size:0.7rem;color:{HEY_GRAY_TEXT};display:block;text-align:right;margin-top:2px;">Uso: {utilizacion:.0f}%</span>' if utilizacion else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def quick_action_card(icon: str, label: str, desc: str = "",
                      key: str = "", on_click=None) -> None:
    """Tarjeta de accion rapida clickeable."""
    st.markdown(
        f"""
        <div class="quick-action">
            <div class="quick-action-icon">{icon}</div>
            <div class="quick-action-label">{label}</div>
            <div class="quick-action-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if on_click and key:
        st.button(
            label,
            key=f"qa_{key}",
            on_click=on_click,
            kwargs={},
            use_container_width=True,
            help=desc,
        )


def _get_initials(user_row: dict) -> str:
    """Genera iniciales para el avatar."""
    uid = user_row.get("user_id", "")
    parts = uid.split("-") if uid else []
    if len(parts) >= 2 and parts[-1].isdigit():
        num = int(parts[-1])
        letters = "ABCDEFGH"
        return f"{parts[0][0]}{letters[num % 8]}" if parts else "U"
    return uid[:2].upper() if len(uid) >= 2 else "U"
