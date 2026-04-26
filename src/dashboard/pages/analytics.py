"""Analytics — Heatmap, Sankey, intenciones y cohortes."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.data_loader import load_transactions, load_havi, load_conv_intents
from src.dashboard.components.charts import (
    heatmap_hora_dia, sankey_categories, sunburst_intents,
)


def run_analytics() -> None:
    st.title("Analytics")

    tx = load_transactions()

    st.subheader("Actividad Transaccional por Hora y Dia")
    tx_heat = tx.select(["hora_del_dia", "dia_semana", "monto"])
    heat = heatmap_hora_dia(tx_heat.to_pandas())
    st.plotly_chart(heat, use_container_width=True)

    st.markdown("---")

    st.subheader("Flujo de Transacciones")
    tx_sankey = tx.select(["categoria_mcc", "tipo_operacion", "estatus"])
    sankey = sankey_categories(tx_sankey.to_pandas())
    st.plotly_chart(sankey, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Intenciones de Conversaciones")
        try:
            ci = load_conv_intents()
            sun = sunburst_intents(ci.to_pandas())
            st.plotly_chart(sun, use_container_width=True)
        except Exception:
            st.info("Datos de intenciones no disponibles (5% sample)")

    with col2:
        st.subheader("Canales de Conversacion (Havi)")
        havi = load_havi()
        channel_counts = havi.group_by("channel_source").len().to_pandas()
        channel_counts["channel_source"] = channel_counts["channel_source"].map(
            {"1": "Texto", "2": "Voz"}
        )
        st.dataframe(
            channel_counts.rename(columns={"channel_source": "Canal", "len": "Interacciones"}),
            use_container_width=True, hide_index=True,
        )
        st.metric("Total interacciones", f"{havi.shape[0]:,}")
        pct_voz = int((havi["channel_source"] == "2").sum()) / havi.shape[0] * 100
        st.metric("% Canal Voz", f"{pct_voz:.1f}%")

    st.markdown("---")
    st.subheader("Adopcion de Productos")

    from src.dashboard.utils.data_loader import load_products, load_clients
    prods = load_products()
    clients = load_clients()

    tipo_counts = prods.group_by("tipo_producto").len().sort("len", descending=True)
    st.dataframe(
        tipo_counts.to_pandas().rename(columns={"tipo_producto": "Producto", "len": "Usuarios"}),
        use_container_width=True, hide_index=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        hey_pro = clients["es_hey_pro"].sum()
        st.metric("Usuarios Hey Pro", f"{hey_pro:,} ({hey_pro/clients.shape[0]*100:.1f}%)")
    with col2:
        con_seguro = clients["tiene_seguro"].sum()
        st.metric("Usuarios con Seguro", f"{con_seguro:,}")


run_analytics()