"""Analytics -- Heatmap, Sankey, intenciones y cohortes con filtros."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.data_loader import (
    load_transactions, load_havi, load_conv_intents,
)
from src.dashboard.components.charts import (
    heatmap_hora_dia, sankey_categories, sunburst_intents,
)


def run_analytics() -> None:
    st.title("Analytics")

    tx = load_transactions()
    havi = load_havi()

    # ── Top Metrics ─────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Transacciones", f"{tx.shape[0]:,}", border=True)
    with m2:
        st.metric("Volumen Total", f"${tx['monto'].sum():,.0f}", border=True)
    with m3:
        st.metric("Interacciones Havi", f"{havi.shape[0]:,}", border=True)
    with m4:
        pct_voz_tmp = int((havi["channel_source"] == "2").sum()) / havi.shape[0] * 100
        st.metric("% Canal Voz", f"{pct_voz_tmp:.1f}%", border=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "Actividad Transaccional",
        "Conversaciones",
        "Adopcion de Productos",
    ])

    with tab1:
        st.subheader("Actividad por Hora y Dia")
        tx_heat = tx.select(["hora_del_dia", "dia_semana", "monto"])
        heat = heatmap_hora_dia(tx_heat.to_pandas())
        st.plotly_chart(heat, use_container_width=True)

        st.markdown("---")
        st.subheader("Flujo de Transacciones")
        tx_sankey = tx.select(["categoria_mcc", "tipo_operacion", "estatus"])
        sankey = sankey_categories(tx_sankey.to_pandas())
        st.plotly_chart(sankey, use_container_width=True)

    with tab2:
        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.subheader("Intenciones de Conversaciones")
            try:
                ci = load_conv_intents()
                sun = sunburst_intents(ci.to_pandas())
                st.plotly_chart(sun, use_container_width=True)
            except Exception:
                st.info("Datos de intenciones no disponibles (5% sample)")

        with col2:
            st.subheader("Canales de Conversacion")
            channel_counts = havi.group_by("channel_source").len().to_pandas()
            channel_counts["channel_source"] = channel_counts["channel_source"].map(
                {"1": "Texto", "2": "Voz"}
            )
            st.dataframe(
                channel_counts.rename(
                    columns={"channel_source": "Canal", "len": "Interacciones"}
                ),
                use_container_width=True,
                hide_index=True,
            )

            pct_voz = (
                int((havi["channel_source"] == "2").sum()) / havi.shape[0] * 100
                if havi.shape[0] > 0 else 0
            )
            st.metric("% Canal Voz", f"{pct_voz:.1f}%", border=True)

            st.markdown("---")

            try:
                ci = load_conv_intents()
                sentiment_counts = (
                    ci.group_by("sentiment").len().to_pandas()
                )
                st.subheader("Sentimiento")
                for _, row in sentiment_counts.iterrows():
                    sent = row["sentiment"]
                    cnt = row["len"]
                    pct_sent = cnt / ci.shape[0] * 100 if ci.shape[0] > 0 else 0
                    st.metric(
                        sent.capitalize(),
                        f"{cnt:,} ({pct_sent:.1f}%)",
                        border=True,
                    )
            except Exception:
                st.caption("Datos de sentimiento no disponibles")

    with tab3:
        from src.dashboard.utils.data_loader import load_products, load_clients

        prods = load_products()
        clients = load_clients()

        st.subheader("Adopcion de Productos")
        tipo_counts = prods.group_by("tipo_producto").len().sort("len", descending=True)
        st.dataframe(
            tipo_counts.to_pandas().rename(
                columns={"tipo_producto": "Producto", "len": "Usuarios"}
            ),
            use_container_width=True,
            hide_index=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            hey_pro = clients["es_hey_pro"].sum()
            total_cl = clients.shape[0]
            st.metric(
                "Usuarios Hey Pro",
                f"{hey_pro:,}",
                f"{hey_pro/total_cl*100:.1f}%" if total_cl > 0 else "",
                border=True,
            )
        with col2:
            con_seguro = clients["tiene_seguro"].sum()
            st.metric("Usuarios con Seguro", f"{con_seguro:,}", border=True)
        with col3:
            con_atipico = clients["patron_uso_atipico"].sum()
            st.metric("Patron Atipico", f"{con_atipico:,}", border=True)


run_analytics()
