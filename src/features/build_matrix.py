"""Construccion de la feature matrix para clustering.

Joins de todos los datasets por user_id, one-hot encoding,
agregaciones transaccionales, y flatten de embeddings.

Output: feature_matrix.parquet + data/features.db (SQLite).
"""

import os
import sqlite3
import time

import polars as pl

# ── Feature groups metadata ────────────────────────────────────────────

SEXO_VALUES = ["H", "M", "SE"]

ESTADO_VALUES = [
    "Baja California", "Chihuahua", "Ciudad de Mexico", "Coahuila",
    "Estado de Mexico", "Guanajuato", "Jalisco", "Nuevo Leon",
    "Oaxaca", "Otros", "Puebla", "Queretaro", "Sinaloa", "Sonora",
    "Tamaulipas", "Veracruz", "Yucatan",
]

EDUCACION_ORDINAL = {
    "Secundaria": 1, "Preparatoria": 2, "Licenciatura": 3, "Posgrado": 4,
}

OCUPACION_VALUES = [
    "Desempleado", "Empleado", "Empresario", "Estudiante",
    "Independiente", "Jubilado",
]

TIPO_PRODUCTO_VALUES = [
    "credito_auto", "credito_nomina", "credito_personal",
    "cuenta_debito", "cuenta_negocios", "inversion_hey",
    "seguro_compras", "seguro_vida", "tarjeta_credito_garantizada",
    "tarjeta_credito_hey", "tarjeta_credito_negocios",
]

CATEGORIA_MCC_VALUES = [
    "educacion", "entretenimiento", "gobierno", "hogar",
    "restaurante", "ropa_accesorios", "salud", "servicios_digitales",
    "supermercado", "tecnologia", "transferencia", "transporte", "viajes",
]

CANAL_VALUES = [
    "app_android", "app_huawei", "app_ios",
    "cajero_banregio", "cajero_externo", "codi",
    "farmacia_ahorro", "oxxo", "pos_fisico",
]

TIPO_OPERACION_VALUES = [
    "abono_inversion", "cargo_recurrente", "cashback", "compra",
    "deposito_farmacia", "deposito_oxxo", "pago_credito",
    "pago_servicio", "retiro_cajero", "retiro_inversion",
    "transf_entrada", "transf_salida",
]

DIA_SEMANA_VALUES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

MOTIVO_NO_PROCESADA_VALUES = [
    "codigo_incorrecto", "cuenta_destino_invalida",
    "datos_invalidos", "limite_excedido",
    "monto_excede_limite_diario", "saldo_insuficiente",
    "tarjeta_bloqueada", "timeout_banco",
]

PREFERENCIA_CANAL_VALUES = ["app_android", "app_huawei", "app_ios"]
CANAL_APERTURA_VALUES = ["App", "Fan Shop"]
IDIOMA_VALUES = ["es_MX", "en_US"]


def _onehot(series: pl.Series, values: list[str], prefix: str) -> pl.DataFrame:
    """One-hot encode a string series into a DataFrame with prefix_<value> columns."""
    cols = {}
    for v in values:
        cols[f"{prefix}_{v}"] = (series == v).cast(pl.Int64)
    return pl.DataFrame(cols)


def _normalize_accent(s: str) -> str:
    """Normaliza acentos para matching consistente."""
    if s is None:
        return s
    return (s.replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u")
            .replace("Á", "A").replace("É", "E").replace("Í", "I")
            .replace("Ó", "O").replace("Ú", "U"))


def run_build_matrix(
    data_dir: str = "data/processed/",
    output_path: str = "data/processed/feature_matrix.parquet",
    db_path: str = "data/features.db",
) -> None:
    """Construye la feature matrix final por user_id."""

    t_start = time.monotonic()

    # ── 1. Cargar datos ────────────────────────────────────────────────
    def _load(name: str) -> pl.DataFrame:
        p = os.path.join(data_dir, name)
        if os.path.exists(p):
            if name.endswith(".parquet"):
                return pl.read_parquet(p)
            return pl.read_csv(p, ignore_errors=True)
        raw = os.path.join("data/raw/", name.replace("_clean", ""))
        if name.endswith(".parquet"):
            return pl.read_parquet(raw)
        return pl.read_csv(raw, ignore_errors=True)

    clientes = _load("clientes_clean.parquet")
    productos = _load("productos_clean.parquet")
    transacciones = _load("transacciones_clean.parquet")
    havi = _load("havi_clean.parquet")

    all_users = clientes.select("user_id")
    n_users = all_users.shape[0]
    print(f"[LOAD]  {n_users:,} usuarios base")

    # ── 2. Demograficas ────────────────────────────────────────────────
    print("[FEAT]  Demograficas...")
    norm_estado = clientes["estado"].map_elements(
        _normalize_accent, return_dtype=pl.String
    )

    demo = pl.concat([
        clientes.select("user_id"),
        clientes.select(pl.col("edad")),
        _onehot(clientes["sexo"], SEXO_VALUES, "sexo"),
        _onehot(norm_estado, ESTADO_VALUES, "estado"),
        clientes.select(
            pl.col("nivel_educativo").map_elements(
                lambda x: EDUCACION_ORDINAL.get(x, 2), return_dtype=pl.Int64
            ).alias("educacion_ordinal"),
        ),
        _onehot(clientes["ocupacion"], OCUPACION_VALUES, "ocupacion"),
        clientes.select(pl.col("ingreso_mensual_mxn")),
        _onehot(clientes["idioma_preferido"], IDIOMA_VALUES, "idioma"),
    ], how="horizontal")

    # ── 3. Engagement ──────────────────────────────────────────────────
    print("[FEAT]  Engagement...")
    eng = pl.concat([
        clientes.select("user_id"),
        clientes.select(
            pl.col("antiguedad_dias"),
            pl.col("dias_desde_ultimo_login"),
            pl.col("satisfaccion_1_10"),
            pl.col("es_hey_pro").cast(pl.Int64).alias("es_hey_pro"),
            pl.col("nomina_domiciliada").cast(pl.Int64).alias("nomina_domiciliada"),
            pl.col("recibe_remesas").cast(pl.Int64).alias("recibe_remesas"),
            pl.col("usa_hey_shop").cast(pl.Int64).alias("usa_hey_shop"),
        ),
        _onehot(clientes["preferencia_canal"], PREFERENCIA_CANAL_VALUES, "pref_canal"),
        _onehot(clientes["canal_apertura"], CANAL_APERTURA_VALUES, "canal_apertura"),
    ], how="horizontal")

    # ── 4. Credito ─────────────────────────────────────────────────────
    print("[FEAT]  Credito...")
    cred = clientes.select(
        "user_id", "score_buro",
        pl.col("tiene_seguro").cast(pl.Int64).alias("tiene_seguro"),
        pl.col("patron_uso_atipico").cast(pl.Int64).alias("patron_uso_atipico"),
    )

    # ── 5. Productos (agregado) ────────────────────────────────────────
    print("[FEAT]  Productos...")
    prod_agg = (
        productos
        .group_by("user_id")
        .agg([
            pl.col("tipo_producto").alias("tipos"),
            pl.col("utilizacion_pct").mean().alias("utilizacion_pct_avg"),
            pl.col("saldo_actual").sum().alias("saldo_actual_total"),
            pl.col("tasa_interes_anual").mean().alias("tasa_interes_promedio"),
            pl.col("plazo_meses").mean().alias("plazo_meses_promedio"),
            pl.col("monto_mensualidad").sum().alias("monto_mensualidad_total"),
        ])
    )

    # One-hot tipo_producto per user (presence/absence via pivot)
    prod_onehot = (
        productos
        .select(["user_id", "tipo_producto"])
        .with_columns(pl.lit(1).alias("presente"))
        .pivot(values="presente", index="user_id",
               on="tipo_producto", aggregate_function="first")
        .fill_null(0)
    )
    # Rename columns: credito_auto -> prod_credito_auto
    current_cols = [c for c in prod_onehot.columns if c != "user_id"]
    prod_onehot = prod_onehot.rename({c: f"prod_{c}" for c in current_cols})
    # Add any missing product types as zero columns
    for v in TIPO_PRODUCTO_VALUES:
        cname = f"prod_{v}"
        if cname not in prod_onehot.columns:
            prod_onehot = prod_onehot.with_columns(pl.lit(0).alias(cname))
    # Select only needed columns in order
    prod_onehot = prod_onehot.select(
        ["user_id"] + [f"prod_{v}" for v in TIPO_PRODUCTO_VALUES]
    )

    prod_feat = (
        prod_agg.select(["user_id", "utilizacion_pct_avg", "saldo_actual_total",
                          "tasa_interes_promedio", "plazo_meses_promedio",
                          "monto_mensualidad_total"])
        .join(prod_onehot, on="user_id", how="left")
    )

    # ── 6. Transaccionales ─────────────────────────────────────────────
    print("[FEAT]  Transaccionales...")
    tx = transacciones

    tx_agg = (
        tx.group_by("user_id")
        .agg([
            pl.len().alias("frecuencia_total"),
            pl.col("monto").mean().alias("monto_promedio"),
            pl.col("monto").sum().alias("monto_total"),
            pl.col("cashback_generado").sum().alias("cashback_total"),
            pl.col("intento_numero").mean().alias("intentos_promedio"),
            pl.col("es_internacional").mean().alias("pct_internacional"),
            (pl.col("estatus") == "no_procesada").mean().alias("pct_no_procesada"),
            pl.col("hora_del_dia").mode().first().alias("hora_pico"),
            pl.col("categoria_mcc").alias("cats"),
            pl.col("canal").alias("canales"),
            pl.col("tipo_operacion").alias("ops"),
            pl.col("dia_semana").alias("dias"),
            pl.col("motivo_no_procesada").alias("motivos"),
        ])
    )

    # Frequencies per category/canal/tipo/dia/motivo
    def _freq_onehot(tx: pl.DataFrame, col: str, values: list[str],
                     prefix: str) -> pl.DataFrame:
        counts = (
            tx.group_by(["user_id", col])
            .len()
            .pivot(values=col, index="user_id", on=col,
                   aggregate_function="len")
            .fill_null(0)
        )
        # Ensure all expected columns exist
        for v in values:
            if v not in counts.columns:
                counts = counts.with_columns(pl.lit(0).alias(v))
        renamed = counts.rename({v: f"{prefix}_{v}" for v in values})
        return renamed.select(["user_id"] + [f"{prefix}_{v}" for v in values])

    cat_freq = _freq_onehot(tx, "categoria_mcc", CATEGORIA_MCC_VALUES, "cat")
    canal_freq = _freq_onehot(tx, "canal", CANAL_VALUES, "canal")
    op_freq = _freq_onehot(tx, "tipo_operacion", TIPO_OPERACION_VALUES, "op")
    dia_freq = _freq_onehot(tx, "dia_semana", DIA_SEMANA_VALUES, "dia")
    motivo_freq = _freq_onehot(tx, "motivo_no_procesada",
                                MOTIVO_NO_PROCESADA_VALUES, "motivo")

    tx_feat = (
        tx_agg.select(["user_id", "frecuencia_total", "monto_promedio",
                        "monto_total", "cashback_total", "intentos_promedio",
                        "pct_internacional", "pct_no_procesada", "hora_pico"])
        .join(cat_freq, on="user_id", how="left")
        .join(canal_freq, on="user_id", how="left")
        .join(op_freq, on="user_id", how="left")
        .join(dia_freq, on="user_id", how="left")
        .join(motivo_freq, on="user_id", how="left")
    )

    # ── 7. Conversacionales ────────────────────────────────────────────
    print("[FEAT]  Conversacionales...")
    # Diversity: number of unique intents per user from conv_intents
    conv_agg = (
        havi.group_by("user_id")
        .agg([
            pl.col("conv_id").n_unique().alias("num_conversaciones"),
            pl.len().alias("total_msgs"),
            (pl.col("channel_source") == "2").mean().alias("pct_voz"),
        ])
    )
    conv_feat = conv_agg.select([
        "user_id", "num_conversaciones",
        (pl.col("total_msgs") / pl.col("num_conversaciones")).alias("msgs_promedio"),
        "pct_voz",
    ])

    # Diversidad de interacciones: unique conv_id count as proxy
    conv_feat = conv_feat.with_columns(
        pl.col("num_conversaciones").truediv(pl.col("num_conversaciones").max())
        .alias("diversidad_intents")
    )

    # ── 8. Embeddings Havi ─────────────────────────────────────────────
    print("[FEAT]  Embeddings Havi...")
    try:
        emb = pl.read_parquet(os.path.join(data_dir, "user_embeddings.parquet"))
        # Flatten embedding list into individual columns
        emb_ids = emb["user_id"].to_list()
        emb_vectors = emb["embedding"].to_list()
        dim = len(emb_vectors[0])
        emb_cols = {}
        for d in range(dim):
            emb_cols[f"emb_{d}"] = [v[d] for v in emb_vectors]
        emb_feat = pl.DataFrame({"user_id": emb_ids, **emb_cols})
        print(f"       {dim} dimensiones")
    except FileNotFoundError:
        print("       [SKIP] user_embeddings.parquet no encontrado")
        emb_feat = pl.DataFrame({"user_id": []})

    # ── 9. Intenciones ─────────────────────────────────────────────────
    print("[FEAT]  Intenciones...")
    try:
        intents = pl.read_parquet(os.path.join(data_dir, "user_intents.parquet"))
        intent_cols = [c for c in intents.columns
                       if c.startswith("intent_") or c in
                       ("urgency_avg", "resolution_rate", "pct_negativo")]
        intents_feat = intents.select(["user_id"] + intent_cols)
        print(f"       {len(intent_cols)} columnas")
    except FileNotFoundError:
        print("       [SKIP] user_intents.parquet no encontrado")
        intents_feat = pl.DataFrame({"user_id": []})

    # ── 10. Join final ─────────────────────────────────────────────────
    print(f"\n[JOIN]  Consolidando por user_id...")

    # Collect all feature DFs
    feature_dfs = [
        demo, eng, cred, prod_feat, tx_feat, conv_feat,
    ]
    if emb_feat.shape[0] > 0:
        feature_dfs.append(emb_feat)
    if intents_feat.shape[0] > 0:
        feature_dfs.append(intents_feat)

    # Start with all users, left join each feature set
    matrix = all_users
    for feat_df in feature_dfs:
        matrix = matrix.join(feat_df, on="user_id", how="left")

    # Fill nulls with 0 for numeric columns
    numeric_cols = [c for c in matrix.columns if c != "user_id"]
    matrix = matrix.with_columns([
        pl.col(c).fill_null(0) for c in numeric_cols
    ])

    n_cols = len(matrix.columns) - 1  # minus user_id
    print(f"[DONE]  {matrix.shape[0]:,} filas x {n_cols:,} columnas")

    # ── 11. Guardar ────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    matrix.write_parquet(output_path, compression="snappy")
    print(f"[SAVE]  {output_path}")

    # SQLite — la matriz tiene >2000 columnas, SQLite tiene limite de 2000.
    # Guardamos como Parquet (ya hecho) + tabla reducida sin embeddings.
    print(f"[DB]    Guardando tabla reducida (sin embeddings) en {db_path}...")
    import pandas as pd
    non_emb_cols = ["user_id"] + [c for c in matrix.columns
                                    if not c.startswith("emb_") and c != "user_id"]
    pdf_reduced = matrix.select(non_emb_cols).to_pandas()
    conn = sqlite3.connect(db_path)
    pdf_reduced.to_sql("feature_matrix", conn, if_exists="replace", index=False)
    conn.close()
    print(f"[DB]    Tabla 'feature_matrix' ({len(non_emb_cols)-1} cols, sin embeddings) lista")

    t_total = time.monotonic() - t_start
    print(f"\n[TIME]  {t_total:.1f}s total")


if __name__ == "__main__":
    run_build_matrix()
