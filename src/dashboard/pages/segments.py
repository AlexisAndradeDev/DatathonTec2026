"""Segment Explorer -- UMAP scatter + tarjeta de segmento + drill-down."""

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

    st.markdown("### Visualizacion UMAP 2D")
    st.caption(
        "Cada punto es un cliente. Los colores representan segmentos. "
        "Selecciona un segmento a la derecha para explorar sus usuarios."
    )

    col_left, col_right = st.columns([3, 2])

    with col_left:
        fig = umap_scatter(pdf)
        st.plotly_chart(fig, use_container_width=True, key="umap_scatter_main")

    with col_right:
        st.markdown("### Perfil de Segmento")

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

        col_a, col_b = st.columns(2)
        with col_a:
            show_compare = st.checkbox("Comparar con otro", key="cmp_checkbox")
        if show_compare:
            compare_sel = st.selectbox(
                "Segundo segmento",
                options=[k for k in opts if k != selected],
                key="segment_comparison",
            )
            with col_b:
                compare_profile = opts[compare_sel]
                segment_card(compare_profile)

        st.markdown("---")
        st.markdown("### Explorar Usuarios")
        cluster_id = profile["cluster_id"]
        cluster_users = segs.filter(pl.col("cluster") == cluster_id).select(
            "user_id", "cluster", "umap_x", "umap_y"
        )

        user_search = st.text_input(
            "Buscar usuario", placeholder="USR-...",
            key="seg_user_search",
        )
        if user_search:
            cluster_users = cluster_users.filter(
                pl.col("user_id").str.contains(user_search.upper())
            )

        st.dataframe(
            cluster_users.to_pandas().head(50),
            use_container_width=True,
            hide_index=True,
            column_config={
                "user_id": st.column_config.TextColumn("Usuario"),
                "cluster": st.column_config.NumberColumn("Cluster"),
            },
        )
        st.caption(f"Mostrando {min(50, cluster_users.shape[0])} de {cluster_users.shape[0]:,} usuarios")

        cu = st.selectbox(
            "Ir a ficha de usuario",
            options=cluster_users["user_id"].to_list()[:200],
            key="seg_user_pick",
        )
        if st.button("Ver Customer 360", key="goto_360_from_seg", use_container_width=True):
            st.session_state.customer_360_preselected = cu
            st.switch_page("pages/customer_360.py")


run_segments()
