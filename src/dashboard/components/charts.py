"""Visualizaciones Plotly reutilizables con tema Hey Banco."""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.utils.styling import (
    HEY_PRIMARY, HEY_TEAL, HEY_CORAL, HEY_BLACK,
    HEY_GRAY_BG, HEY_GRAY_TEXT, HEY_WHITE,
)


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convierte hex (#RRGGBB o #RGB) a rgba(r, g, b, alpha)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

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
        title="UMAP 2D -- Segmentacion de Clientes",
        custom_data=["user_id"],
    )
    fig.update_traces(marker=dict(size=4, opacity=0.7))
    fig.update_layout(**PLOT_LAYOUT, height=550, legend_title="Cluster",
                      clickmode="event+select")
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
    fig.update_layout(**PLOT_LAYOUT, height=450, title="Distribucion de Segmentos")
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
                      title="Actividad Transaccional -- Hora x Dia")
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
                      title="Flujo Transaccional -- Categoria a Operacion a Estatus")
    return fig


def radar_chart(user_vals: dict, segment_vals: dict, categories: list[str]) -> go.Figure:
    labels_map = {
        "es_hey_pro": "Hey Pro",
        "tiene_seguro": "Seguro",
        "pct_internacional": "Intl",
        "pct_no_procesada": "No Proc.",
        "pct_voz": "Voz",
        "ingreso_mensual_mxn": "Ingreso",
        "score_buro_interno": "Score Buro",
        "satisfaccion_1_10": "Satisfac.",
    }
    display_labels = [labels_map.get(c, c) for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[user_vals.get(c, 0) for c in categories],
        theta=display_labels,
        fill="toself",
        name="Usuario",
        line_color=HEY_PRIMARY,
        marker_color=HEY_PRIMARY,
    ))
    fig.add_trace(go.Scatterpolar(
        r=[segment_vals.get(c, 0) for c in categories],
        theta=display_labels,
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
        title="Distribucion de Intenciones",
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
        title="Top Categorias por Monto Total",
        labels={"monto": "Monto Total (MXN)", "categoria_mcc": ""},
    )
    fig.update_layout(**PLOT_LAYOUT, height=350)
    return fig


def sparkline(values: list[float], height: int = 55, color: str = HEY_PRIMARY) -> go.Figure:
    """Mini linea para tarjetas KPI (sparkline)."""
    fig = go.Figure(go.Scatter(
        y=values,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=_hex_to_rgba(color, 0.19),
        showlegend=False,
        hoverinfo="none",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def donut_chart(labels: list[str], values: list[float], title: str = "",
                height: int = 320) -> go.Figure:
    """Donut chart para distribuciones de gasto."""
    colors = HEY_COLORS[:len(labels)] if len(labels) <= len(HEY_COLORS) else HEY_COLORS * 3
    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors[:len(labels)]),
        textinfo="percent",
        textfont=dict(family="Inter, sans-serif", size=11),
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **PLOT_LAYOUT, height=height, title=title,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def gauge_chart(score: float, label: str = "Score", height: int = 200) -> go.Figure:
    """Gauge semicircular para scores (0-100)."""
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
        number={"font": {"size": 36, "family": "Inter, sans-serif", "color": HEY_BLACK}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickfont": {"size": 0}},
            "bar": {"color": color, "thickness": 0.15},
            "bgcolor": "#f0f0f0",
            "borderwidth": 0,
        },
        title={"text": label, "font": {"size": 13, "family": "Inter, sans-serif",
                                         "color": HEY_GRAY_TEXT}},
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def comparison_bars(seg_vals: dict, pop_vals: dict, label: str = "Feature",
                    height: int = 220) -> go.Figure:
    """Barras horizontales comparando segmento vs poblacion en varias features."""
    items = sorted(seg_vals.keys())
    seg_list = [seg_vals[k] for k in items]
    pop_list = [pop_vals[k] for k in items]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=items, x=seg_list, name="Segmento",
        orientation="h", marker_color=HEY_PRIMARY,
        text=[f"{v:.2f}" for v in seg_list], textposition="outside",
        textfont=dict(size=10),
    ))
    fig.add_trace(go.Bar(
        y=items, x=pop_list, name="Poblacion",
        orientation="h", marker_color=HEY_TEAL + "60",
        text=[f"{v:.2f}" for v in pop_list], textposition="outside",
        textfont=dict(size=10),
    ))
    fig.update_layout(
        **PLOT_LAYOUT, height=height, title=f"Segmento vs Poblacion: {label}",
        barmode="group", showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="center", x=0.5),
    )
    return fig


def export_chart_json(fig: go.Figure) -> str:
    """Exporta un chart como JSON para descarga (Plotly)."""
    return json.dumps(fig.to_dict(), indent=2, ensure_ascii=False)
