"""Customer 360 -- Ficha completa de usuario con DNA, radar, gauge y donut."""

import os
import sys

sys.path.insert(0, os.getcwd())

import polars as pl
import streamlit as st

from src.dashboard.utils.data_loader import (
    load_clients, load_products, load_transactions,
    load_segments, load_profiles, load_feature_matrix,
    get_user_ids, get_profile_for_user, get_dna_for_user,
    get_action_for_user,
)
from src.dashboard.components.cards import (
    demographic_card, dna_card, product_card, score_gauge,
    action_cards,
)
from src.dashboard.components.charts import radar_chart, donut_chart, gauge_chart


def run_customer_360() -> None:
    st.title("Customer 360")

    user_ids = get_user_ids()

    preselected = st.session_state.pop("customer_360_preselected", None)
    default_idx = None
    if preselected and preselected in user_ids:
        default_idx = user_ids.index(preselected)

    selected = st.selectbox(
        "Buscar usuario",
        options=user_ids,
        index=default_idx,
        placeholder="Selecciona un USR-XXXXX...",
    )

    if not selected:
        st.info("Selecciona un usuario para ver su ficha completa.")
        return

    clients = load_clients()
    products = load_products()
    tx = load_transactions()
    profile = get_profile_for_user(selected)
    dna_text = get_dna_for_user(selected)

    user_row = clients.filter(pl.col("user_id") == selected)
    if user_row.shape[0] == 0:
        st.error("Usuario no encontrado.")
        return

    user_dict = {c: user_row[c][0] for c in clients.columns}

    # ── Hero Header ──────────────────────────────────────
    st.markdown("---")
    h1, h2, h3, h4 = st.columns([1, 3, 1.5, 1])

    with h1:
        import math
        initials = _make_initials(user_dict)
        st.markdown(
            f"""
            <div class="avatar-circle" style="width:64px;height:64px;font-size:1.5rem;">
            {initials}</div>
            """,
            unsafe_allow_html=True,
        )

    with h2:
        st.markdown(f"## {selected}")
        tags = []
        if user_dict.get("es_hey_pro"):
            tags.append('<span class="hey-tag pro">Hey Pro</span>')
        if user_dict.get("nomina_domiciliada"):
            tags.append('<span class="hey-tag teal">Nomina</span>')
        if user_dict.get("recibe_remesas"):
            tags.append('<span class="hey-tag teal">Remesas</span>')
        if user_dict.get("patron_uso_atipico"):
            tags.append('<span class="hey-tag alerta">Atipico</span>')
        if profile:
            tags.append(f'<span class="hey-tag cashback">{profile["nombre"]}</span>')
        if tags:
            st.markdown("".join(tags), unsafe_allow_html=True)

    with h3:
        score = _compute_health_score(user_dict)
        gauge_chart(score, "Salud Financiera", height=160)

    with h4:
        if st.button("Chat con Havi", key="goto_havi", use_container_width=True,
                     type="primary"):
            st.session_state.chatbot_preselected = selected
            st.switch_page("pages/chatbot.py")

    st.markdown("---")

    # ── Row 1: Demographic + Products ───────────────────
    col1, col2 = st.columns([1, 1.2])

    with col1:
        demographic_card(user_dict)

    with col2:
        user_prods = products.filter(pl.col("user_id") == selected)
        st.markdown("**Productos activos**")
        if user_prods.shape[0] == 0:
            st.caption("Sin productos registrados")
        else:
            for row in user_prods.iter_rows(named=True):
                product_card(
                    tipo=row.get("tipo_producto", ""),
                    saldo=float(row.get("saldo_actual", 0) or 0),
                    limite=float(row.get("limite_credito", 0) or 0),
                    utilizacion=float(row.get("utilizacion_pct", 0) or 0),
                    estatus=row.get("estatus", "activa"),
                    tasa=float(row.get("tasa_interes", 0) or 0),
                )

    # ── Row 2: DNA full width ──────────────────────────
    if dna_text:
        dna_card(dna_text)
    else:
        st.info("Customer DNA no disponible (menos de 2 conversaciones)")

    # ── Row 3: Radar (centered) + Accion proactiva ─────
    if profile:
        col_a, col_r, col_c = st.columns([1, 2, 1])
        with col_r:
            matrix = load_feature_matrix()
            seg_users = load_segments().filter(
                (pl.col("cluster") == profile["cluster_id"]) &
                (pl.col("user_id") != selected)
            )["user_id"].to_list()

            top_feats = profile.get("top_features", [])
            categories = []
            for f in top_feats:
                if len(categories) >= 5:
                    break
                col = f["feature"]
                if col in matrix.columns and col not in ("user_id", "cluster", "umap_x", "umap_y"):
                    categories.append(col)

            user_vals = {}
            seg_vals = {}
            for c in categories:
                if c in matrix.columns:
                    user_vals[c] = float(
                        matrix.filter(pl.col("user_id") == selected)[c].mean() or 0
                    )
                    seg_vals[c] = float(
                        matrix.filter(pl.col("user_id").is_in(seg_users))[c].mean() or 0
                    )

            for c in categories:
                max_c = max(user_vals.get(c, 0), seg_vals.get(c, 0), 0.01)
                user_vals[c] = user_vals.get(c, 0) / max_c
                seg_vals[c] = seg_vals.get(c, 0) / max_c

            radar = radar_chart(user_vals, seg_vals, categories)
            st.plotly_chart(radar, use_container_width=True)

        action = get_action_for_user(selected)
        if action:
            st.markdown("**Que haria Havi?**")
            action_cards(action)
    else:
        st.info("Segmento no disponible (ruido)")

    # ── Row 3: Transactions + Category Donut ────────────
    st.markdown("---")
    st.subheader("Actividad Reciente")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        user_tx = tx.filter(pl.col("user_id") == selected).sort(
            "fecha_hora", descending=True
        ).head(10)
        st.markdown("**Ultimas transacciones**")
        if user_tx.shape[0] == 0:
            st.caption("Sin transacciones registradas")
        else:
            tx_show = user_tx.select([
                "fecha_hora", "tipo_operacion", "monto",
                "categoria_mcc", "estatus",
            ]).to_pandas()
            st.dataframe(tx_show, use_container_width=True, hide_index=True)

    with col2:
        user_tx_all = tx.filter(pl.col("user_id") == selected)
        if user_tx_all.shape[0] > 0:
            cat_totals = (
                user_tx_all.group_by("categoria_mcc")
                .agg(pl.col("monto").sum())
                .sort("monto", descending=True)
                .head(7)
            )
            cat_labels = cat_totals["categoria_mcc"].to_list()
            cat_vals = cat_totals["monto"].to_list()
            donut = donut_chart(cat_labels, cat_vals,
                                "Gasto por Categoria", height=320)
            st.plotly_chart(donut, use_container_width=True)
        else:
            st.caption("Sin datos transaccionales")


def _make_initials(user_dict: dict) -> str:
    uid = user_dict.get("user_id", "U")
    parts = uid.split("-") if uid else []
    letters = "ABCDEFGH"
    if len(parts) >= 2 and parts[-1].isdigit():
        n = int(parts[-1])
        return f"{parts[0][0]}{letters[n % 8]}"
    return uid[:2].upper()


def _compute_health_score(user_dict: dict) -> float:
    score = 50.0
    if user_dict.get("es_hey_pro"):
        score += 8
    if user_dict.get("tiene_seguro"):
        score += 6
    score_buro = user_dict.get("score_buro_interno", 500) or 500
    score += (score_buro - 500) / 25
    sat = user_dict.get("satisfaccion_1_10", 5) or 5
    score += (sat - 5) * 3
    ingreso = user_dict.get("ingreso_mensual_mxn", 15000) or 15000
    score += min((ingreso - 15000) / 1000, 15)
    if user_dict.get("patron_uso_atipico"):
        score -= 8
    return max(5, min(97, score))


run_customer_360()
