"""Customer DNA narrativo — perfil de 150-200 palabras por usuario via DeepSeek-V3.2."""

from .llm_client import chat_completion, get_embeddings, estimate_tokens


def run_customer_dna(input_dir: str = "data/raw/", output_path: str = "data/processed/customer_dna.parquet") -> None:
    """Genera perfil narrativo + embedding por usuario via DeepSeek-V3.2 + text-embedding-3-large (3072 dims)."""
    pass


if __name__ == "__main__":
    run_customer_dna()
