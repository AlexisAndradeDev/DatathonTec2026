"""Pipeline UMAP + HDBSCAN para clustering no supervisado.

Grid search sobre n_components y min_cluster_size maximizando DBCV.
Incluye reasignacion de ruido, validacion y guardado.
"""

import os
import time
import warnings

import numpy as np
import polars as pl
from sklearn.impute import KNNImputer
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import umap
import hdbscan

warnings.filterwarnings("ignore", category=FutureWarning)

BEST_UNSEEN = object()


def _progress_bar(current: int, total: int, width: int = 20) -> str:
    pct = current / total
    filled = int(width * pct)
    return "|" + "█" * filled + "░" * (width - filled) + "|"


def run_cluster(
    input_path: str = "data/processed/feature_matrix.parquet",
    output_path: str = "data/processed/user_segments.parquet",
    random_state: int = 42,
) -> None:
    """Ejecuta UMAP + HDBSCAN con grid search y reasignacion de ruido."""

    t_start = time.monotonic()

    # ── 1. Cargar feature matrix ───────────────────────────────────────
    print("[LOAD]  Cargando feature matrix...")
    df = pl.read_parquet(input_path)
    user_ids = df["user_id"].to_list()
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    non_emb_cols = [c for c in df.columns if not c.startswith("emb_")
                    and c != "user_id"]

    X_nonemb = df.select(non_emb_cols).to_numpy()
    X_emb = df.select(emb_cols).to_numpy().astype(np.float64)
    print(f"        {X_nonemb.shape[1]} cols no-embedding, {X_emb.shape[1]} cols embedding")
    print(f"        {X_nonemb.shape[0]:,} usuarios")

    # ── 2. Preprocesamiento ────────────────────────────────────────────
    print("[PREP]  KNN Imputer + StandardScaler...")
    imp = KNNImputer(n_neighbors=5)
    X_nonemb = imp.fit_transform(X_nonemb)
    scaler = StandardScaler()
    X_nonemb = scaler.fit_transform(X_nonemb)

    # Concatenar: escaladas + embeddings (sin escalar, ya en [-1,1])
    X = np.hstack([X_nonemb, X_emb.astype(np.float64)])
    print(f"        Matriz final: {X.shape}")

    # ── 3. Grid Search ─────────────────────────────────────────────────
    n_components_list = [5, 8, 10, 15]
    min_cluster_list = [50, 100, 150, 200]
    umap_metric = "euclidean"

    best_dbcv = -1.0
    best_params = {}
    best_labels = None
    best_umap_embedding = None

    total_combos = len(n_components_list)
    combo_i = 0
    umap_cache = {}

    print(f"\n[GRID]  Grid search: {len(n_components_list)} n_components × "
          f"{len(min_cluster_list)} min_cluster_size")
    print(f"        {total_combos * len(min_cluster_list)} combinaciones totales")

    grid_start = time.monotonic()

    for nc in n_components_list:
        # UMAP — expensive, do once per n_components
        print(f"\n  [UMAP] n_components={nc}...")
        reducer = umap.UMAP(
            n_components=nc,
            n_neighbors=30,
            min_dist=0.0,
            metric=umap_metric,
            random_state=random_state,
            n_jobs=1,
            verbose=False,
        )
        t0 = time.monotonic()
        X_umap = reducer.fit_transform(X)
        t1 = time.monotonic()
        umap_cache[nc] = X_umap
        print(f"         {t1 - t0:.0f}s | shape={X_umap.shape}")

        for mc in min_cluster_list:
            combo_i += 1
            print(f"    [{combo_i:>2}/{total_combos * len(min_cluster_list)}] "
                  f"nc={nc}, mc={mc}...", end="", flush=True)

            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=mc,
                min_samples=1,
                cluster_selection_epsilon=0.5,
                metric="euclidean",
                core_dist_n_jobs=1,
                prediction_data=False,
            )
            labels = clusterer.fit_predict(X_umap)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = int((labels == -1).sum())

            # Silhouette como metrica de grid search (DBCV inestable en UMAP space)
            if n_clusters >= 2:
                valid_mask = labels != -1
                try:
                    sil = silhouette_score(
                        X_umap[valid_mask], labels[valid_mask],
                        metric="euclidean",
                    )
                except Exception:
                    sil = -1.0
            else:
                sil = -1.0

            # Tiebreaker: preferir mas clusters con menos ruido
            score = sil + (n_clusters * 0.001) - (n_noise / len(labels) * 0.0001)

            bar = _progress_bar(combo_i, total_combos * len(min_cluster_list))
            print(f"\r    [{combo_i:>2}/{total_combos * len(min_cluster_list)}] "
                  f"nc={nc}, mc={mc}: {n_clusters} clusters, "
                  f"{n_noise} noise, Sil={sil:.4f} {bar}", flush=True)

            if score > best_dbcv:
                best_dbcv = score
                best_params = {"n_components": nc, "min_cluster_size": mc}
                best_labels = labels.copy()
                best_umap_embedding = X_umap.copy()

    grid_elapsed = time.monotonic() - grid_start
    print(f"\n[GRID]  Mejor: {best_params} | score={best_dbcv:.4f}")
    print(f"        Tiempo grid search: {grid_elapsed:.0f}s")

    # ── 4. Clustering final con mejores params ─────────────────────────
    X_final = umap_cache[best_params["n_components"]]
    labels = best_labels

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    print(f"\n[FINAL] {n_clusters} clusters, {n_noise} ruido "
          f"({n_noise/len(labels)*100:.1f}%)")

    # ── 5. Reasignacion de ruido ──────────────────────────────────────
    if n_noise > 0 and n_clusters > 0:
        print("[NOISE] Reasignando ruido...")
        valid_mask = labels != -1
        valid_labels = set(labels[valid_mask])

        # Centroides de clusters validos
        centroids = {}
        for cl in valid_labels:
            centroids[cl] = X_final[labels == cl].mean(axis=0)

        centroids_arr = np.array(list(centroids.values()))
        centroid_labels = np.array(list(centroids.keys()))

        # Distancias intra-cluster (para umbral percentil 95)
        intra_dists = []
        for i, cl in enumerate(centroid_labels):
            cluster_points = X_final[labels == cl]
            c = centroids_arr[i]
            dists = np.linalg.norm(cluster_points - c, axis=1)
            intra_dists.extend(dists.tolist())
        threshold = np.percentile(intra_dists, 95)

        # Para cada punto de ruido, encontrar centroide mas cercano
        noise_mask = labels == -1
        noise_points = X_final[noise_mask]
        nn = NearestNeighbors(n_neighbors=1, metric="euclidean")
        nn.fit(centroids_arr)
        distances, indices = nn.kneighbors(noise_points)
        distances = distances.flatten()
        indices = indices.flatten()

        reassigned = 0
        new_labels = labels.copy()
        for j, (dist, idx) in enumerate(zip(distances, indices)):
            if dist < threshold:
                new_labels[np.where(noise_mask)[0][j]] = centroid_labels[idx]
                reassigned += 1

        labels = new_labels
        new_noise = int((labels == -1).sum())
        print(f"        {reassigned} reasignados, {new_noise} ruido final "
              f"({new_noise/len(labels)*100:.1f}%) | umbral={threshold:.4f}")
    else:
        new_noise = n_noise

    # ── 6. Validacion ──────────────────────────────────────────────────
    print("[VALID] Calculando metricas...")
    valid_mask = labels != -1
    if valid_mask.sum() >= 2 and len(set(labels[valid_mask])) >= 2:
        sil = silhouette_score(
            X_final[valid_mask], labels[valid_mask],
            metric="euclidean",
        )
    else:
        sil = 0.0
    print(f"        Silhouette (UMAP space): {sil:.4f}")

    # ── 7. UMAP 2D para visualizacion ─────────────────────────────────
    print("[VIZ]   UMAP 2D para dashboard...")
    reducer_2d = umap.UMAP(
        n_components=2, n_neighbors=30, min_dist=0.1,
        metric=umap_metric, random_state=random_state,
    )
    X_2d = reducer_2d.fit_transform(X)
    print(f"        shape={X_2d.shape}")

    # ── 8. Guardar ─────────────────────────────────────────────────────
    df_out = pl.DataFrame({
        "user_id": user_ids,
        "cluster": labels.tolist(),
        "umap_x": X_2d[:, 0].tolist(),
        "umap_y": X_2d[:, 1].tolist(),
    })

    df_out.write_parquet(output_path, compression="snappy")
    t_total = time.monotonic() - t_start
    print(f"\n[SAVE]  {output_path} ({df_out.shape[0]:,} filas)")
    print(f"[TIME]  {t_total:.0f}s total")

    # Mostrar distribucion de clusters
    for row in df_out.group_by("cluster").len().sort("cluster").iter_rows():
        cl = int(row[0])
        cnt = row[1]
        pct = cnt / df_out.shape[0] * 100
        noise_tag = " [RUIDO]" if cl == -1 else ""
        print(f"        Cluster {cl}: {cnt:>6,} ({pct:5.1f}%){noise_tag}")


if __name__ == "__main__":
    run_cluster()
