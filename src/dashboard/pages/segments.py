"""Segment Explorer — UMAP scatter + tarjeta de segmento."""

import os
import sys

sys.path.insert(0, os.getcwd())

import polars as pl
import streamlit as st

from src.dashboard.utils.data_loader import load_segments, load_profiles
from src.dashboard.components.charts import umap_scatter
from src.dashboard.components.cards import segment_card


def run_segments() -> None:
    st.title("Segment Explorer")

    segs = load_segments()
    profiles = load_profiles()

    segs_clean = segs.filter(pl.col("cluster") != -1)
    cluster_names = {}
    for p in profiles:
        cluster_names[p["cluster_id"]] = p["nombre"]

    pdf = segs_clean.to_pandas()
    pdf["cluster_label"] = pdf["cluster"].apply(
        lambda x: cluster_names.get(x, f"Cluster {x}")
    )

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Visualizacion UMAP 2D")
        fig = umap_scatter(pdf)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Perfil de Segmento")
        sorted_profiles = sorted(profiles, key=lambda p: p.get("size", 0), reverse=True)
        opts = {f"{p['nombre']} ({p['size']:,})": p for p in sorted_profiles}
        selected = st.selectbox(
            "Seleccionar segmento",
            options=list(opts.keys()),
            key="segment_selector",
        )
        profile = opts[selected]
        segment_card(profile)

        st.markdown("---")
        st.subheader("Usuarios del Segmento")
        cluster_id = profile["cluster_id"]
        cluster_users = segs.filter(pl.col("cluster") == cluster_id).select(
            "user_id", "cluster", "umap_x", "umap_y"
        )
        st.dataframe(
            cluster_users.to_pandas().head(50),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Mostrando 50 de {cluster_users.shape[0]:,} usuarios")


run_segments()