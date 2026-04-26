"""Perfilamiento de segmentos: estadisticas, features discriminantes y labeling.

Template deterministico sin LLM — genera nombres, descripciones,
necesidades implicitas y acciones proactivas basadas en top features.
"""

import json
import os

import numpy as np
import polars as pl


def _top_discriminative(
    seg_df: pl.DataFrame,
    pop_df: pl.DataFrame,
    numeric_cols: list[str],
    top_k: int = 10,
) -> list[dict]:
    """Top features por diferencia absoluta estandarizada vs poblacion."""

    pop_mean = np.array([pop_df[c].mean() or 0.0 for c in numeric_cols])
    pop_std = np.array([pop_df[c].std() or 1.0 for c in numeric_cols])
    seg_mean = np.array([seg_df[c].mean() or 0.0 for c in numeric_cols])

    z = (seg_mean - pop_mean) / np.maximum(pop_std, 1e-8)
    abs_z = np.abs(z)
    top_indices = np.argsort(abs_z)[::-1][:top_k]

    return [
        {
            "feature": numeric_cols[i],
            "segment_mean": float(seg_mean[i]),
            "population_mean": float(pop_mean[i]),
            "z_score": float(z[i]),
            "direction": "mayor" if z[i] > 0 else "menor",
        }
        for i in top_indices
    ]


def _label_segment(
    seg_df: pl.DataFrame,
    cluster_id: int,
    size: int,
    pct: float,
    top_features: list[dict],
) -> dict:
    """Genera nombre, descripcion, necesidades y accion proactiva."""

    edad = seg_df["edad"].mean()
    ingreso = seg_df["ingreso_mensual_mxn"].mean()
    hey_pro_pct = seg_df["es_hey_pro"].mean() * 100
    score_avg = seg_df["score_buro"].mean()
    sat_avg = seg_df["satisfaccion_1_10"].mean()
    antiguedad = seg_df["antiguedad_dias"].mean()
    conv_count = seg_df["num_conversaciones"].mean()
    num_prods = seg_df["prod_cuenta_debito"].mean()
    has_tc = any(
        seg_df.get_column(f"prod_{p}").mean() > 0.05
        for p in [
            "tarjeta_credito_hey",
            "tarjeta_credito_garantizada",
            "tarjeta_credito_negocios",
        ]
        if f"prod_{p}" in seg_df.columns
    )
    pct_intl = seg_df["pct_internacional"].mean() * 100

    masc_pct = seg_df["sexo_H"].mean()
    fem_pct = seg_df["sexo_M"].mean()
    if masc_pct > 0.55:
        genero_str = "hombres"
    elif fem_pct > 0.55:
        genero_str = "mujeres"
    else:
        genero_str = "mixto"

    # --- Nombre base ---
    edad_tag = "Jovenes" if edad < 30 else ("Adultos" if edad < 45 else "Maduros")
    ingreso_tag = (
        "Alto Ingreso" if ingreso > 25000
        else ("Ingreso Medio" if ingreso > 12000 else "Ingreso Basico")
    )

    if hey_pro_pct > 70:
        perfil_tag = "Pro Digitales"
    elif has_tc:
        perfil_tag = "Crediticios"
    elif num_prods > 1.5:
        perfil_tag = "Diversificados"
    else:
        perfil_tag = "Basicos"

    nombre = f"{edad_tag} {ingreso_tag} {perfil_tag}"

    # --- Mejorar con top features discriminantes ---
    discriminators = []
    for f in top_features:
        feat = f["feature"]
        if abs(f["z_score"]) < 0.5:
            continue
        if "prod_" in feat:
            discriminators.append(feat.replace("prod_", "").replace("_", " "))
        elif "cat_" in feat:
            discriminators.append(feat.replace("cat_", "").replace("_", " "))
        elif "intent_" in feat:
            discriminators.append(feat.replace("intent_", "").replace("_", " "))
        elif feat in ("monto_promedio", "monto_total"):
            tag = "Alto Gasto" if f["direction"] == "mayor" else "Bajo Gasto"
            discriminators.append(tag)
        elif feat == "frecuencia_total":
            if f["direction"] == "mayor":
                discriminators.append("Transaccional")
        elif feat == "pct_internacional":
            if f["direction"] == "mayor":
                discriminators.append("Internacional")
    if discriminators:
        # Dedeplicate
        seen = set()
        unique_disc = []
        for d in discriminators:
            if d not in seen:
                seen.add(d)
                unique_disc.append(d)
        nombre = f"{nombre} ({', '.join(unique_disc[:3])})"

    # --- Descripcion ---
    desc = (
        f"Segmento de {size:,} clientes ({pct:.1f}%) mayoritariamente {genero_str}, "
        f"edad promedio {edad:.0f} anos, ingreso mensual promedio ${ingreso:,.0f} MXN. "
        f"Score buro promedio {score_avg:.0f}, satisfaccion {sat_avg:.1f}/10. "
        f"{hey_pro_pct:.0f}% son Hey Pro. "
        f"Antiguedad promedio {antiguedad:.0f} dias. "
        f"Promedio de {conv_count:.1f} conversaciones con Havi."
    )

    # --- Necesidades implicitas ---
    necesidades = []
    if not has_tc and score_avg > 650:
        necesidades.append("Acceso a credito: buen score buro sin tarjeta de credito")
    if ingreso > 20000 and hey_pro_pct > 60:
        necesidades.append("Optimizacion financiera: potencial para inversion con rendimientos")
    if sat_avg < 6.5:
        necesidades.append("Atencion prioritaria: satisfaccion por debajo del promedio")
    if pct_intl > 15:
        necesidades.append("Soluciones transfronterizas: alto porcentaje de transacciones internacionales")
    if not necesidades:
        necesidades.append("Fidelizacion y retencion: mantener nivel de satisfaccion actual")

    # --- Accion proactiva ---
    if not has_tc and score_avg > 650:
        accion = "Oferta segmentada: Tarjeta de Credito Hey con 5% cashback en categorias frecuentes"
    elif ingreso > 20000 and hey_pro_pct > 60:
        accion = "Promocion: Inversion Hey con tasa preferencial para clientes Hey Pro"
    elif sat_avg < 6.5:
        accion = "Alerta: Campana de seguimiento para mejorar satisfaccion y reducir churn"
    else:
        accion = "Insight: Envio de reporte mensual personalizado de gastos por categoria"

    return {
        "cluster_id": int(cluster_id),
        "nombre": nombre,
        "size": size,
        "pct": round(pct, 1),
        "descripcion": desc,
        "necesidades": necesidades,
        "accion_proactiva": accion,
        "estadisticas": {
            "edad_promedio": round(float(edad), 1),
            "ingreso_promedio": round(float(ingreso), 0),
            "hey_pro_pct": round(float(hey_pro_pct), 1),
            "score_buro_promedio": round(float(score_avg), 1),
            "satisfaccion_promedio": round(float(sat_avg), 1),
            "antiguedad_promedio": round(float(antiguedad), 0),
            "conversaciones_promedio": round(float(conv_count), 1),
            "genero_dominante": genero_str,
        },
        "top_features": top_features,
    }


def run_segments(
    segments_path: str = "data/processed/user_segments.parquet",
    matrix_path: str = "data/processed/feature_matrix.parquet",
    output_path: str = "data/processed/segment_profiles.json",
    db_path: str = "data/features.db",
) -> None:
    """Genera perfiles de segmento con estadisticas y labeling."""

    segs = pl.read_parquet(segments_path)
    matrix = pl.read_parquet(matrix_path)

    df = matrix.join(segs.select(["user_id", "cluster"]), on="user_id", how="left")

    numeric_cols = [c for c in df.columns
                    if c not in ("user_id", "cluster", "umap_x", "umap_y")
                    and df[c].dtype in (pl.Float64, pl.Int64, pl.Boolean)]

    for c in numeric_cols:
        if df[c].dtype == pl.Boolean:
            df = df.with_columns(pl.col(c).cast(pl.Int64))

    n_total = df.shape[0]
    cluster_labels = sorted(set(df["cluster"].to_list()))
    valid_clusters = [cl for cl in cluster_labels if cl != -1]

    print(f"[LOAD]  {n_total:,} usuarios, {len(valid_clusters)} clusters validos "
          f"(+ {int((df['cluster'] == -1).sum())} ruido)")

    profiles = []
    for cl in valid_clusters:
        seg_df = df.filter(pl.col("cluster") == cl)
        pop_df = df
        size = seg_df.shape[0]
        pct = size / n_total * 100

        top_feats = _top_discriminative(seg_df, pop_df, numeric_cols, top_k=8)
        profile = _label_segment(seg_df, cl, size, pct, top_feats)
        profiles.append(profile)

        print(f"  Cluster {cl}: {profile['nombre']} ({size:,} usuarios, {pct:.1f}%)")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVE]  {output_path} ({len(profiles)} segmentos)")

    # SQLite — user_segments (flat columns)
    import sqlite3
    conn = sqlite3.connect(db_path)
    segs.to_pandas().to_sql("user_segments", conn, if_exists="replace", index=False)

    # segment_profiles — flatten nested columns
    flat_profiles = []
    for p in profiles:
        flat = {
            "cluster_id": p["cluster_id"],
            "nombre": p["nombre"],
            "size": p["size"],
            "pct": p["pct"],
            "descripcion": p["descripcion"],
            "accion_proactiva": p["accion_proactiva"],
            "necesidades": json.dumps(p["necesidades"], ensure_ascii=False),
            "top_features": json.dumps(p["top_features"], ensure_ascii=False),
        }
        for k, v in p["estadisticas"].items():
            flat[f"stats_{k}"] = v
        flat_profiles.append(flat)

    pl.DataFrame(flat_profiles).to_pandas().to_sql(
        "segment_profiles", conn, if_exists="replace", index=False
    )
    conn.close()
    print(f"[DB]    {db_path}: tablas 'user_segments' + 'segment_profiles'")


if __name__ == "__main__":
    run_segments()