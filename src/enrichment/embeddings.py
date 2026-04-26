"""Embeddings conversacionales — vectorizar mensajes de Havi por usuario.

Usa text-embedding-3-large via Azure OpenAI (3072 dimensiones).
"""

import os
import time

import numpy as np
import polars as pl

from .llm_client import get_embeddings, estimate_tokens


def run_embeddings(
    data_dir: str = "data/processed/",
    output_path: str = "data/processed/user_embeddings.parquet",
) -> None:
    """Genera embeddings conversacionales y mean-pool por usuario.

    Pipeline:
    1. Cargar Havi (prefiere havi_clean.parquet, fallback a raw).
    2. Concatenar mensajes input por conv_id en orden cronologico.
    3. Vectorizar textos en batches de 500 con text-embedding-3-large.
    4. Mean-pool de embeddings por user_id → 3072 dims.
    5. Guardar user_embeddings.parquet.
    """

    # --- 2.1.1 Cargar Havi ---
    havi_path = os.path.join(data_dir, "havi_clean.parquet")
    if not os.path.exists(havi_path):
        havi_path = os.path.join("data/raw/", "dataset_50k_anonymized.parquet")
    if not os.path.exists(havi_path):
        print(f"[ERROR] No se encontro Havi en {data_dir} ni data/raw/")
        return

    havi = pl.read_parquet(havi_path)
    print(f"[LOAD]  {havi_path}: {havi.shape[0]:,} interacciones, {havi['conv_id'].n_unique():,} conversaciones")

    # --- 2.1.2 Concatenar mensajes por conv_id ---
    conv_texts = (
        havi
        .sort("date")
        .group_by("conv_id")
        .agg([
            pl.col("input").str.join(" ").alias("conv_text"),
            pl.col("user_id").first().alias("user_id"),
        ])
    )

    n_convs = conv_texts.shape[0]
    n_users = conv_texts["user_id"].n_unique()
    print(f"[PREP]  {n_convs:,} textos de conversacion para {n_users:,} usuarios")

    # --- 2.1.3 Vectorizar en batches de 500 ---
    texts = conv_texts["conv_text"].to_list()
    user_ids_per_conv = conv_texts["user_id"].to_list()

    BATCH_SIZE = 500
    all_embeddings = []
    total_tokens_est = 0
    total_tokens_real = 0
    total_cost = 0.0
    COST_PER_1M = 0.13  # text-embedding-3-large: $0.13/1M tokens

    t_start = time.monotonic()

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_idx = i + 1
        batch_end = min(i + BATCH_SIZE, len(texts))
        n_batch = len(batch)

        batch_chars = sum(len(t) for t in batch)
        batch_est = estimate_tokens("\n".join(batch))
        total_tokens_est += batch_est

        t0 = time.monotonic()
        batch_embeddings = get_embeddings(batch)
        t1 = time.monotonic()

        all_embeddings.extend(batch_embeddings)
        total_tokens_real += batch_est  # embedding API no retorna usage

        # Budget approx usando estimacion (API de embeddings no retorna usage)
        batch_cost = batch_est / 1_000_000 * COST_PER_1M
        total_cost += batch_cost

        pct = batch_end / len(texts) * 100
        print(
            f"  [{batch_idx:>4}-{batch_end:>4}/{len(texts)}] "
            f"{n_batch:>3} textos, ~{batch_est:,} tok, "
            f"{t1 - t0:.1f}s  ({pct:5.1f}%)"
        )

    t_total = time.monotonic() - t_start
    print(f"[DONE]  {len(all_embeddings):,} embeddings en {t_total:.0f}s")
    print(f"  Tokens estimados: {total_tokens_est:,}")
    print(f"  Costo estimado:   ${total_cost:.4f} USD")

    # --- 2.1.4 Mean-pool por user_id ---
    from collections import defaultdict

    user_embs = defaultdict(list)
    for uid, emb in zip(user_ids_per_conv, all_embeddings):
        user_embs[uid].append(emb)

    user_ids_out = []
    user_embeddings = []
    for uid, embs in user_embs.items():
        mean_vec = np.array(embs, dtype=np.float32).mean(axis=0)
        user_ids_out.append(uid)
        user_embeddings.append(mean_vec.tolist())

    print(f"[POOL]  {len(user_ids_out):,} usuarios con mean-pool ({len(user_embeddings[0])} dims)")

    # --- 2.1.5 Guardar ---
    output = pl.DataFrame({
        "user_id": user_ids_out,
        "embedding": user_embeddings,
    })

    output.write_parquet(output_path, compression="snappy")
    print(f"[SAVE]  {output_path} ({output.shape[0]:,} filas x {output.shape[1]} cols)")
    print(f"  Vector dim: {len(user_embeddings[0])}")


if __name__ == "__main__":
    run_embeddings()
