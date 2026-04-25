"""Pipeline UMAP + HDBSCAN para clustering no supervisado."""

def run_cluster(input_path: str = "data/processed/feature_matrix.parquet", output_path: str = "data/processed/user_segments.parquet") -> None:
    """Ejecuta KNN Imputer → StandardScaler → UMAP → HDBSCAN → reasignación de ruido."""
    pass


if __name__ == "__main__":
    run_cluster()
