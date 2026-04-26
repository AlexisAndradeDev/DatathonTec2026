"""Visualizaciones Plotly y Altair reutilizables con tema Hey Banco."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc

from src.dashboard.utils.styling import (
    HEY_PRIMARY, HEY_TEAL, HEY_CORAL, HEY_BLACK,
    HEY_GRAY_BG, HEY_GRAY_TEXT, HEY_WHITE,
)

HEY_COLORS = [HEY_PRIMARY, HEY_TEAL, HEY_CORAL, "#5B8FF9", "#FF9845",
              "#A855F7", "#22C55E", "#EC4899", "#14B8A6", "#F43F5E"]

PLOT_LAYOUT = dict(
    paper_bgcolor=HEY_GRAY_BG,
    plot_bgcolor=HEY_WHITE,
    font=dict(family="Inter, sans-serif", color=HEY_BLACK, size=12),
    title_font_size=16,
    margin=dict(l=20, r=20, t=40, b=20),
    hoverlabel=dict(font_family="Inter, sans-serif"),
)


def umap_scatter(segments_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        segments_df,
        x="umap_x", y="umap_y",
        color=segments_df["cluster"].astype(str),
        hover_data={"user_id": True, "cluster": True, "umap_x": False, "umap_y": False},
        color_discrete_sequence=HEY_COLORS,
        title="UMAP 2D — Segmentación de Clientes",
    )
    fig.update_traces(marker=dict(size=4, opacity=0.7))
    fig.update_layout(**PLOT_LAYOUT, height=550, legend_title="Cluster")
    return fig


def segment_treemap(profiles: list[dict]) -> go.Figure:
    names = [p["nombre"] for p in profiles]
    sizes = [p["size"] for p in profiles]
    pcts = [p["pct"] for p in profiles]
    labels = [f"{n}<br>{s:,} ({p}%)" for n, s, p in zip(names, sizes, pcts)]

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=[""] * len(labels),
        values=sizes,
        textinfo="label",
        marker=dict(colors=HEY_COLORS[:len(labels)]),
        hoverinfo="text",
        textfont=dict(family="Inter, sans-serif", size=13),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=450, title="Distribución de Segmentos")
    return fig


def heatmap_hora_dia(tx_df: pd.DataFrame) -> go.Figure:
    group = tx_df.groupby(["hora_del_dia", "dia_semana"])["monto"].mean().reset_index()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_es = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    pivot = group.pivot(index="dia_semana", columns="hora_del_dia", values="monto")
    pivot = pivot.reindex(days).fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=list(range(24)),
        y=days_es,
        colorscale=[[0, HEY_WHITE], [1, HEY_PRIMARY]],
        hoverongaps=False,
        colorbar=dict(title="Monto prom. (MXN)"),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=350,
                      title="Actividad Transaccional — Hora × Día")
    return fig


def sankey_categories(tx_df: pd.DataFrame) -> go.Figure:
    flows = (
        tx_df.groupby(["categoria_mcc", "tipo_operacion", "estatus"])
        .size()
        .reset_index(name="count")
        .head(50)
    )

    all_nodes = (
        list(flows["categoria_mcc"].unique())
        + list(flows["tipo_operacion"].unique())
        + list(flows["estatus"].unique())
    )
    node_map = {n: i for i, n in enumerate(all_nodes)}

    fig = go.Figure(data=go.Sankey(
        node=dict(
            pad=15, thickness=15,
            line=dict(color=HEY_BLACK, width=0.5),
            label=all_nodes,
            color=HEY_TEAL,
        ),
        link=dict(
            source=[node_map[r["categoria_mcc"]] for _, r in flows.iterrows()],
            target=[node_map[r["tipo_operacion"]] for _, r in flows.iterrows()],
            value=[r["count"] for _, r in flows.iterrows()],
        ),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=450,
                      title="Flujo Transaccional — Categoría → Operación → Estatus")
    return fig


def radar_chart(user_vals: dict, segment_vals: dict, categories: list[str]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[user_vals.get(c, 0) for c in categories],
        theta=categories,
        fill="toself",
        name="Usuario",
        line_color=HEY_PRIMARY,
        marker_color=HEY_PRIMARY,
    ))
    fig.add_trace(go.Scatterpolar(
        r=[segment_vals.get(c, 0) for c in categories],
        theta=categories,
        fill="toself",
        name="Segmento",
        line_color=HEY_TEAL,
        marker_color=HEY_TEAL,
        opacity=0.4,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        **PLOT_LAYOUT, height=400, title="Usuario vs. Segmento",
    )
    return fig


def sunburst_intents(intents_df: pd.DataFrame) -> go.Figure:
    counts = intents_df["intent"].value_counts().reset_index()
    fig = px.sunburst(
        counts,
        path=["intent"],
        values="count",
        color="count",
        color_continuous_scale=[
            (0, HEY_GRAY_BG), (0.5, HEY_TEAL), (1, HEY_PRIMARY)
        ],
        title="Distribución de Intenciones",
    )
    fig.update_layout(**PLOT_LAYOUT, height=400)
    return fig


def category_bars(tx_df: pd.DataFrame) -> go.Figure:
    cats = tx_df.groupby("categoria_mcc")["monto"].sum().reset_index()
    cats = cats.sort_values("monto", ascending=False).head(10)
    fig = px.bar(
        cats, x="monto", y="categoria_mcc", orientation="h",
        color="monto", color_continuous_scale=[
            (0, HEY_TEAL), (1, HEY_PRIMARY)
        ],
        title="Top Categorías por Monto Total",
        labels={"monto": "Monto Total (MXN)", "categoria_mcc": ""},
    )
    fig.update_layout(**PLOT_LAYOUT, height=350)
    return fig
