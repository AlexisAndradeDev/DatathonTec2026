"""Extracción estructurada de intenciones por conversación.

Usa DeepSeek-V3.2 con JSON mode via OpenAI-compatible endpoint.
Batch asimetrico: single-msg (200/llamada), multi-msg (50/llamada).
"""

import json
import os
import time

import polars as pl

from .llm_client import chat_completion, estimate_tokens

INTENTS = [
    "consulta_saldo", "reclamo_comision", "solicitud_credito",
    "bloqueo_tarjeta", "info_producto", "soporte_tecnico",
    "cancelacion", "transferencia", "queja", "aclaracion", "otro",
]

SENTIMENTS = ["positivo", "neutral", "negativo"]
URGENCIES = ["baja", "media", "alta"]
RESOLUTIONS = ["resuelto", "no_resuelto", "escalado"]

INTENT_ENUM = "|".join(INTENTS)
SENTIMENT_ENUM = "|".join(SENTIMENTS)
URGENCY_ENUM = "|".join(URGENCIES)
RESOLUTION_ENUM = "|".join(RESOLUTIONS)

SYSTEM_PROMPT = (
    "Eres un clasificador de conversaciones de servicio al cliente de Hey Banco, "
    "un banco digital mexicano. Analizas cada conversacion y extraes metadata estructurada.\n\n"
    "IMPORTANTE: Responde SOLO con un objeto JSON. No incluyas markdown ni texto extra."
)


def _format_conversation(conv_id: str, inputs: list[str], outputs: list[str]) -> str:
    """Convierte una conversacion en texto estructurado para el prompt."""
    lines = [f"ID: {conv_id}"]
    for i, (inp, out) in enumerate(zip(inputs, outputs), 1):
        lines.append(f"Usuario: {inp}")
        lines.append(f"Havi: {out}")
    return "\n".join(lines)


def _build_user_prompt(conv_ids: list[str], conv_texts: list[str]) -> str:
    """Construye el prompt con N conversaciones formateadas."""

    format_spec = (
        '{\n'
        + '  "conv_id": "string",\n'
        + f'  "intent": "{INTENT_ENUM}",\n'
        + f'  "sentiment": "{SENTIMENT_ENUM}",\n'
        + f'  "urgency": "{URGENCY_ENUM}",\n'
        + f'  "resolution": "{RESOLUTION_ENUM}",\n'
        + '  "summary": "Resumen en una oracion en espanol"\n'
        + '}'
    )

    parts = [
        f"Clasifica las siguientes {len(conv_ids)} conversaciones.",
        "Devuelve SOLO un objeto JSON con clave 'results' y un array de objetos.",
        f"Cada objeto debe tener este formato: {format_spec}",
        "",
        "Conversaciones:",
        "",
    ]
    for i, text in enumerate(conv_texts):
        parts.append(f"--- {i + 1} ---")
        parts.append(text)
        parts.append("")

    return "\n".join(parts)


def _parse_response(content: str) -> list[dict]:
    """Parsea la respuesta JSON del LLM, tolerando markdown."""
    text = content.strip()
    if text.startswith("```"):
        # Extract from markdown code block
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    data = json.loads(text)
    if "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected JSON structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")


def _validate_and_fix(item: dict, idx: int) -> dict:
    """Valida un item de resultado y lo normaliza."""

    valid: dict = {}

    valid["conv_id"] = str(item.get("conv_id", f"unknown_{idx}"))

    intent = item.get("intent", "otro")
    valid["intent"] = intent if intent in INTENTS else "otro"

    sentiment = item.get("sentiment", "neutral")
    valid["sentiment"] = sentiment if sentiment in SENTIMENTS else "neutral"

    urgency = item.get("urgency", "baja")
    valid["urgency"] = urgency if urgency in URGENCIES else "baja"

    resolution = item.get("resolution", "no_resuelto")
    valid["resolution"] = resolution if resolution in RESOLUTIONS else "no_resuelto"

    valid["summary"] = str(item.get("summary", ""))[:200]

    return valid


def _classify_batch(
    conv_ids: list[str],
    conv_texts: list[str],
    batch_n: int,
    total_batches: int,
) -> tuple[list[dict], float]:
    """Envia un batch de conversaciones al LLM y retorna resultados + costo."""

    user_prompt = _build_user_prompt(conv_ids, conv_texts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    est_tokens_in = estimate_tokens(SYSTEM_PROMPT + user_prompt)
    cost_in = est_tokens_in / 1_000_000 * 0.27

    t0 = time.monotonic()
    response = chat_completion(
        messages=messages,
        json_mode=True,
        temperature=0.1,
        max_tokens=8192,
    )
    t1 = time.monotonic()

    usage = response.get("usage", {})
    real_tokens = usage.get("completion_tokens", 0)
    cost_out = real_tokens / 1_000_000 * 1.10
    batch_cost = cost_in + cost_out

    content = response.get("content", "")

    # Parse with retry
    for attempt in range(3):
        try:
            items = _parse_response(content)
            valid_items = [_validate_and_fix(item, i) for i, item in enumerate(items)]
            if len(valid_items) != len(conv_ids):
                print(f"\n  [WARN]  Batch {batch_n}: esperados {len(conv_ids)}, recibidos {len(valid_items)}")
            return valid_items[:len(conv_ids)], batch_cost
        except (json.JSONDecodeError, ValueError, KeyError):
            if attempt < 2:
                print(f"\n  [RETRY] Batch {batch_n}: parseo JSON fallido (intento {attempt + 1})")
                time.sleep(1)
    raise RuntimeError(f"Batch {batch_n}: no se pudo parsear respuesta tras 3 intentos")


def _progress_bar(current: int, total: int, width: int = 30) -> str:
    """Barra de progreso ASCII."""
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"|{bar}| {current}/{total} ({pct*100:5.1f}%)"


def _batch_worker(
    all_conv_ids: list[str],
    all_conv_texts: list[str],
    batch_size: int,
    label: str,
) -> tuple[list[dict], float]:
    """Procesa batches de conversaciones y acumula resultados."""

    results: list[dict] = []
    total_cost = 0.0
    total = len(all_conv_ids)
    n_batches = (total + batch_size - 1) // batch_size
    processed = 0

    print(f"  [{label}] {total:,} convs en {n_batches} batches (batch size: {batch_size})")

    for i in range(0, total, batch_size):
        batch_ids = all_conv_ids[i:i + batch_size]
        batch_texts = all_conv_texts[i:i + batch_size]
        batch_n = i // batch_size + 1

        items, cost = _classify_batch(batch_ids, batch_texts, batch_n, n_batches)
        results.extend(items)
        total_cost += cost
        processed += len(items)

        bar = _progress_bar(processed, total)
        print(f"\r  [{label}] {bar} | accum: ${total_cost:.4f}", end="", flush=True)

    print()  # newline after bar completes
    return results, total_cost


def _aggregate_users(
    conv_intents: pl.DataFrame,
    havi: pl.DataFrame,
) -> pl.DataFrame:
    """Agrega las metricas de intenciones por usuario."""

    # Per user: count per intent, urgency stats, sentiment stats, resolution rate
    # Encode urgency: baja=1, media=2, alta=3

    conv_agg = conv_intents.with_columns(
        pl.when(pl.col("urgency") == "alta").then(3)
        .when(pl.col("urgency") == "media").then(2)
        .when(pl.col("urgency") == "baja").then(1)
        .otherwise(2)
        .cast(pl.Int64)
        .alias("urgency_num"),
    )

    # Per user: count per intent, urgency stats, sentiment stats, resolution rate
    user_intents = conv_agg.group_by("user_id").agg([
        # Counts per intent
        pl.col("intent").str.count_matches("consulta_saldo").sum().alias("intent_consulta_saldo"),
    ])

    # Build all intent count columns dynamically
    intent_cols = []
    for intent in INTENTS:
        intent_cols.append(
            (pl.col("intent") == intent).cast(pl.Int64).sum().alias(f"intent_{intent}")
        )

    sentiment_cols = [
        (pl.col("sentiment") == "negativo").cast(pl.Int64).sum().alias("n_negativo"),
        (pl.col("sentiment") == "positivo").cast(pl.Int64).sum().alias("n_positivo"),
        (pl.col("sentiment") == "neutral").cast(pl.Int64).sum().alias("n_neutral"),
        pl.col("sentiment").len().alias("n_total"),
    ]

    urgency_cols = [
        pl.col("urgency_num").max().alias("urgency_max"),
        pl.col("urgency_num").mean().alias("urgency_avg"),
    ]

    resolution_cols = [
        (pl.col("resolution") == "resuelto").cast(pl.Int64).sum().alias("n_resuelto"),
        pl.col("resolution").len().alias("n_total_2"),
        ((pl.col("resolution") == "resuelto").cast(pl.Int64).sum()
         / pl.col("resolution").len()).alias("resolution_rate"),
    ]

    user_agg = conv_agg.group_by("user_id").agg(
        intent_cols + sentiment_cols + urgency_cols + resolution_cols
    )

    # Drop duplicate n_total columns
    columns_to_keep = [
        "user_id",
        *[f"intent_{i}" for i in INTENTS],
        "n_negativo", "n_positivo", "n_neutral",
        "urgency_max", "urgency_avg",
        "n_resuelto", "resolution_rate",
    ]
    user_agg = user_agg.select(columns_to_keep)

    # pct_negativo
    user_agg = user_agg.with_columns(
        (pl.col("n_negativo") / (pl.col("n_negativo") + pl.col("n_positivo") + pl.col("n_neutral")))
        .alias("pct_negativo")
    )

    # Conversation counts from Havi
    havi_agg = (
        havi
        .group_by("user_id")
        .agg([
            pl.col("conv_id").n_unique().alias("num_conversaciones"),
            pl.len().alias("total_msgs"),
            (pl.col("channel_source") == "2").cast(pl.Int64).sum().alias("n_voice"),
            pl.col("channel_source").len().alias("n_total_conv"),
        ])
    )

    user_agg = user_agg.join(havi_agg, on="user_id", how="left")
    user_agg = user_agg.with_columns([
        (pl.col("total_msgs") / pl.col("num_conversaciones")).alias("msgs_promedio"),
        (pl.col("n_voice") / pl.col("num_conversaciones")).alias("pct_voz"),
    ])

    # Drop intermediate columns
    user_agg = user_agg.drop(["total_msgs", "n_voice", "n_total_conv"])

    return user_agg


def run_intents(
    data_dir: str = "data/processed/",
    output_dir: str = "data/processed/",
    sample_pct: float = 1.0,
    random_seed: int = 42,
) -> None:
    """Clasifica cada conversacion por intent, sentiment, urgency y resolution.

    Pipeline:
    1. Cargar Havi y construir textos por conv_id.
    2. Muestrear si sample_pct < 1.0 (seleccion de conv_id, deterministica).
    3. Clasificar con LLM batches de 50.
    4. Unificar resultados y guardar conv_intents.parquet.
    5. Agregar por usuario y guardar user_intents.parquet.

    Args:
        data_dir: Directorio con havi_clean.parquet.
        output_dir: Directorio de salida.
        sample_pct: Fraccion de conversaciones a procesar (1.0 = todas, 0.05 = 5%).
        random_seed: Semilla para muestreo determinista.
    """

    havi_path = os.path.join(data_dir, "havi_clean.parquet")
    if not os.path.exists(havi_path):
        havi_path = os.path.join("data/raw/", "dataset_50k_anonymized.parquet")
    if not os.path.exists(havi_path):
        print(f"[ERROR] No se encontro Havi en {data_dir} ni data/raw/")
        return

    t_total_start = time.monotonic()

    # --- 1. Cargar y preparar conversaciones ---
    havi = pl.read_parquet(havi_path)
    print(f"[LOAD]  {havi.shape[0]:,} interacciones, {havi['conv_id'].n_unique():,} conversaciones")

    # Build conversation texts
    conv_data = (
        havi
        .sort("date")
        .group_by("conv_id")
        .agg([
            pl.col("user_id").first().alias("user_id"),
            pl.col("input").alias("inputs_list"),
            pl.col("output").alias("outputs_list"),
            pl.len().alias("msg_count"),
        ])
    )

    # Construct formatted texts per conversation
    conv_texts: list[str] = []
    conv_ids: list[str] = []
    user_ids: list[str] = []
    msg_counts: list[int] = []

    for row in conv_data.iter_rows():
        cid = row[0]
        uid = row[1]
        inputs = row[2]  # already a Python list
        outputs = row[3]  # already a Python list
        mc = row[4]

        text = _format_conversation(cid, inputs, outputs)
        conv_texts.append(text)
        conv_ids.append(cid)
        user_ids.append(uid)
        msg_counts.append(mc)

    total_convs = len(conv_texts)
    print(f"[PREP]  {total_convs:,} textos de conversacion listos para clasificar")

    # --- 2. Muestrear si sample_pct < 1.0 ---
    if sample_pct < 1.0:
        import random
        random.seed(random_seed)
        n_sample = max(1, int(total_convs * sample_pct))
        sampled_indices = sorted(random.sample(range(total_convs), n_sample))

        conv_texts = [conv_texts[i] for i in sampled_indices]
        conv_ids = [conv_ids[i] for i in sampled_indices]
        user_ids = [user_ids[i] for i in sampled_indices]
        msg_counts = [msg_counts[i] for i in sampled_indices]

        print(f"[SAMPLE] {n_sample:,} conversaciones ({sample_pct*100:.0f}%), seed={random_seed}")

    # --- 3. Aplanar: sin separacion single/multi, batch uniforme 50 ---
    BATCH_SIZE = 50
    total = len(conv_texts)
    print(f"[BATCH] {total:,} convs en {(total + BATCH_SIZE - 1)//BATCH_SIZE} batches de {BATCH_SIZE}")

    all_results: list[dict] = []
    budget_spent = 0.0

    results, cost = _batch_worker(conv_ids, conv_texts, BATCH_SIZE, "LLM")
    all_results.extend(results)
    budget_spent += cost

    t_total = time.monotonic() - t_total_start
    print(f"\n[DONE]  {len(all_results):,} conversaciones clasificadas en {t_total:.0f}s")
    print(f"  Budget total: ${budget_spent:.4f} USD")

    # --- 5. Guardar conv_intents ---
    conv_df = pl.DataFrame({
        "conv_id": [r["conv_id"] for r in all_results],
        "intent": [r["intent"] for r in all_results],
        "sentiment": [r["sentiment"] for r in all_results],
        "urgency": [r["urgency"] for r in all_results],
        "resolution": [r["resolution"] for r in all_results],
        "summary": [r["summary"] for r in all_results],
    })

    # Add user_id and msg_count
    conv_lookup = dict(zip(conv_ids, zip(user_ids, msg_counts)))
    conv_df = conv_df.with_columns([
        pl.Series("user_id", [conv_lookup[cid][0] if cid in conv_lookup else None for cid in conv_df["conv_id"].to_list()]),
        pl.Series("msg_count", [conv_lookup[cid][1] if cid in conv_lookup else None for cid in conv_df["conv_id"].to_list()]),
    ])

    conv_path = os.path.join(output_dir, "conv_intents.parquet")
    conv_df.write_parquet(conv_path, compression="snappy")
    print(f"[SAVE]  {conv_path} ({conv_df.shape[0]:,} filas x {conv_df.shape[1]} cols)")

    # --- 6. Agregar por usuario ---
    print("\n[POOL]  Agregando metricas por usuario...")
    user_agg = _aggregate_users(conv_df, havi)

    user_path = os.path.join(output_dir, "user_intents.parquet")
    user_agg.write_parquet(user_path, compression="snappy")
    print(f"[SAVE]  {user_path} ({user_agg.shape[0]:,} filas x {user_agg.shape[1]} cols)")
    print(f"  Columnas: {list(user_agg.columns)}")


if __name__ == "__main__":
    # 5% sample para desarrollo rapido — cambiar a 1.0 para pipeline completo
    run_intents(sample_pct=0.05)
