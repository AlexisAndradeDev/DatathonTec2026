"""Componentes de tarjeta: segmento, DNA, métricas."""

import streamlit as st

from src.dashboard.utils.styling import (
    HEY_BLACK, HEY_GRAY_TEXT, HEY_PRIMARY, HEY_TEAL,
    HEY_CORAL, HEY_LIME, HEY_WHITE,
)


def segment_card(profile: dict) -> None:
    """Tarjeta de perfil de segmento."""
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
        st.metric("Tamaño", f"{size:,}", f"{pct}% del total")
        st.metric("Edad promedio", f"{stats.get('edad_promedio','?')} años")
        st.metric("Ingreso promedio", f"${stats.get('ingreso_promedio','?'):,.0f} MXN")
        st.metric("Hey Pro", f"{stats.get('hey_pro_pct','?')}%")
    with col2:
        st.metric("Score Buró", f"{stats.get('score_buro_promedio','?')}")
        st.metric("Satisfacción", f"{stats.get('satisfaccion_promedio','?')}/10")
        st.metric("Antigüedad", f"{stats.get('antiguedad_promedio','?'):,.0f} días")
        st.metric("Conversaciones", f"{stats.get('conversaciones_promedio','?')}")

    st.markdown(f"**Descripción:** {desc}")

    if needs:
        st.markdown("**Necesidades implícitas:**")
        for n in needs:
            st.markdown(f"- {n}")

    if action:
        st.info(f"🎯 **Acción proactiva:** {action}")

    if top_feats:
        st.markdown("**Top features discriminantes:**")
        import altair as alt
        import pandas as pd

        feat_df = pd.DataFrame([
            {"feature": f["feature"], "z_score": abs(f["z_score"]),
             "dir": "▲ mayor" if f["direction"] == "mayor" else "▼ menor"}
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
    """Tarjeta de datos demograficos del usuario."""
    items = [
        ("Edad", user_row.get("edad")),
        ("Género", user_row.get("sexo")),
        ("Estado", user_row.get("estado") or "—"),
        ("Ciudad", user_row.get("ciudad") or "—"),
        ("Ocupación", user_row.get("ocupacion")),
        ("Educación", user_row.get("nivel_educativo")),
        ("Ingreso", f"${user_row.get('ingreso_mensual_mxn',0):,}/mes"),
        ("Idioma", user_row.get("idioma_preferido", "es_MX")),
    ]
    lines = []
    for label, val in items:
        lines.append(
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
        <div style="color:{HEY_GRAY_TEXT};font-size:0.7rem;font-weight:700;
        text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;">
        Datos demográficos</div>
        {''.join(lines)}
        </div>
        """,
        unsafe_allow_html=True,
    )
