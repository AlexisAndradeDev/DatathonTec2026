"""Pagina Home — KPIs, metricas y treemap de segmentos."""

import os
import sys

sys.path.insert(0, os.getcwd())

import streamlit as st

from src.dashboard.utils.data_loader import (
    load_clients, load_segments, load_profiles, load_transactions,
    load_havi, load_conv_intents,
)
from src.dashboard.utils.styling import kpi_card
from src.dashboard.components.charts import segment_treemap


def run_home() -> None:
    st.title("Motor de Inteligencia & Atencion Personalizada")
    st.caption("Hey Banco · DatathonTec 2026")

    clients = load_clients()
    segments = load_segments()
    profiles = load_profiles()
    tx = load_transactions()
    havi = load_havi()

    n_users = clients.shape[0]
    n_heal = havi.shape[0]
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("USUARIOS", f"{n_users:,}")
    with col2:
        kpi_card("SEGMENTOS", f"{n_segments}")
    with col3:
        kpi_card("SATISFACCION PROMEDIO", sat_str)
    with col4:
        kpi_card("HEY PRO", f"{hey_pro_pct:.0f}%")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("INTERACCIONES HAVI", f"{n_heal:,}")
    with col2:
        kpi_card("CONVERSACIONES", f"{n_convs:,}")
    with col3:
        kpi_card("VOLUMEN TOTAL TX", f"${tx_vol:,.0f}")
    with col4:
        kpi_card("TICKET PROMEDIO", f"${tx_avg:,.0f}")

    st.markdown("---")

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Distribucion de Segmentos")
        treemap = segment_treemap(profiles)
        st.plotly_chart(treemap, use_container_width=True)
    with col_r:
        st.subheader("Metricas Adicionales")
        st.metric("% Transacciones no procesadas", f"{tx_no_proc_pct:.1f}%")
        st.metric("Cashback total generado", f"${tx['cashback_generado'].sum():,.0f}")

        try:
            ci = load_conv_intents()
            resolved = int((ci["resolution"] == "resuelto").sum())
            conv_total = ci.shape[0]
            res_rate = resolved / conv_total * 100 if conv_total > 0 else 0
            st.metric("Tasa de resolucion Havi", f"{res_rate:.1f}%")
            neg = int((ci["sentiment"] == "negativo").sum())
            pct_neg = neg / conv_total * 100 if conv_total > 0 else 0
            st.metric("% sentimiento negativo", f"{pct_neg:.1f}%")
        except Exception:
            st.caption("Datos de intenciones no disponibles (5% sample)")
            st.metric("Tasa de resolucion Havi", "N/A")
            st.metric("% sentimiento negativo", "N/A")


run_home()