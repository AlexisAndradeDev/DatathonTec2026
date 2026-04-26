"""Pagina Home -- KPIs, metricas y treemap de segmentos."""

import os
import sys

sys.path.insert(0, os.getcwd())

import numpy as np
import streamlit as st

from src.dashboard.utils.data_loader import (
    load_clients, load_segments, load_profiles, load_transactions,
    load_havi, load_conv_intents,
)
from src.dashboard.utils.styling import (
    sparkline_kpi_card, hero_section, section_divider,
)
from src.dashboard.components.charts import segment_treemap, sparkline


def run_home() -> None:
    hero_section(
        "Havi Next",
        "Hey Banco  ·  DatathonTec 2026  ·  Segmentacion no supervisada + Chatbot RAG",
    )

    clients = load_clients()
    segments = load_segments()
    profiles = load_profiles()
    tx = load_transactions()
    havi = load_havi()

    n_users = clients.shape[0]
    n_hawi = havi.shape[0]
    n_convs = havi["conv_id"].n_unique()

    valid_clusters = [p for p in profiles if p["cluster_id"] != -1]
    n_segments = len(valid_clusters)

    n_hey_pro = int(clients["es_hey_pro"].sum())
    hey_pro_pct = n_hey_pro / n_users * 100

    sat_avg = clients["satisfaccion_1_10"].mean()
    sat_str = f"{sat_avg:.1f}/10" if sat_avg else "N/A"

    tx_vol = tx["monto"].sum()
    tx_avg = tx["monto"].mean()
    tx_no_proc_pct = int((tx["estatus"] == "no_procesada").sum()) / tx.shape[0] * 100

    st.markdown("### Metricas Clave")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sparkline_kpi_card("USUARIOS", f"{n_users:,}", "Base total de clientes")
        mock_sp = [10_000, 11_000, 12_000, 13_000, 14_000, n_users]
        sp = sparkline(mock_sp)
        st.plotly_chart(sp, use_container_width=True, config={"displayModeBar": False})
    with col2:
        sparkline_kpi_card("SEGMENTOS", f"{n_segments}", "Clusters identificados")
        mock_sp = [8, 10, 12, 14, 15, n_segments]
        sp = sparkline(mock_sp, color="#5B8FF9")
        st.plotly_chart(sp, use_container_width=True, config={"displayModeBar": False})
    with col3:
        sparkline_kpi_card("SATISFACCION PROMEDIO", sat_str,
                           f"{sat_avg:.1f}/10" if sat_avg else "")
        mock_sp = [7.0, 7.2, 7.5, 7.8, 8.0, float(sat_avg)] if sat_avg else []
        if mock_sp:
            sp = sparkline(mock_sp, color="#22C55E")
            st.plotly_chart(sp, use_container_width=True, config={"displayModeBar": False})
    with col4:
        sparkline_kpi_card("HEY PRO", f"{hey_pro_pct:.0f}%",
                           f"{hey_pro_pct:.0f}% de la base")
        mock_sp = [20, 25, 30, 35, 40, hey_pro_pct]
        sp = sparkline(mock_sp, color="#A855F7")
        st.plotly_chart(sp, use_container_width=True, config={"displayModeBar": False})

    st.markdown("")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sparkline_kpi_card("INTERACCIONES HAVI", f"{n_hawi:,}", "Total mensajes")
    with col2:
        sparkline_kpi_card("CONVERSACIONES", f"{n_convs:,}", "Hilos unicos")
    with col3:
        sparkline_kpi_card("VOLUMEN TOTAL TX", f"${tx_vol/1000000:,.2f} M", "Monto transaccionado")
    with col4:
        sparkline_kpi_card("TICKET PROMEDIO", f"${tx_avg:,.0f}", "Por transaccion")

    section_divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Distribucion de Segmentos")
        treemap = segment_treemap(profiles)
        st.plotly_chart(treemap, use_container_width=True)

    with col_r:
        st.subheader("Insights Rapidos")

        with st.container():
            st.metric(
                "% Transacciones no procesadas",
                f"{tx_no_proc_pct:.1f}%",
                border=True,
            )
            st.metric(
                "Cashback total generado",
                f"${tx['cashback_generado'].sum():,.0f}",
                border=True,
            )

        try:
            ci = load_conv_intents()
            resolved = int((ci["resolution"] == "resuelto").sum())
            conv_total = ci.shape[0]
            res_rate = resolved / conv_total * 100 if conv_total > 0 else 0
            st.metric(
                "Tasa de resolucion Havi",
                f"{res_rate:.1f}%",
                border=True,
                help="% de conversaciones resueltas satisfactoriamente",
            )
            neg = int((ci["sentiment"] == "negativo").sum())
            pct_neg = neg / conv_total * 100 if conv_total > 0 else 0
            st.metric(
                "% sentimiento negativo",
                f"{pct_neg:.1f}%",
                border=True,
                help="Conversaciones con tono negativo detectado",
            )
        except Exception:
            st.caption("Datos de intenciones no disponibles (5% sample)")
            st.metric("Tasa de resolucion Havi", "N/A", border=True)
            st.metric("% sentimiento negativo", "N/A", border=True)

    section_divider()

    st.subheader("Explorar")
    exp1, exp2, exp3 = st.columns(3)
    with exp1:
        with st.container(border=True):
            st.markdown("**Segmentos**")
            st.caption("Visualiza los 15 clusters de clientes identificados con UMAP + HDBSCAN.")
            if st.button("Ver segmentos", key="go_segments", use_container_width=True):
                st.switch_page("pages/segments.py")
    with exp2:
        with st.container(border=True):
            st.markdown("**Havi Next**")
            st.caption("Prueba el chatbot RAG con streaming y tool calling en tiempo real.")
            if st.button("Abrir chatbot", key="go_chatbot", use_container_width=True):
                st.switch_page("pages/chatbot.py")
    with exp3:
        with st.container(border=True):
            st.markdown("**Customer 360**")
            st.caption("Explora la ficha completa de cualquier cliente: DNA, transacciones, segmento.")
            if st.button("Buscar cliente", key="go_customer360", use_container_width=True):
                st.switch_page("pages/customer_360.py")


run_home()
