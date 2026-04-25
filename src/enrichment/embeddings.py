"""Embeddings conversacionales — vectorizar mensajes de Havi por usuario.

Usa text-embedding-3-large via Azure OpenAI (3072 dimensiones).
"""

from .llm_client import get_embeddings, estimate_tokens


def run_embeddings(input_path: str = "data/raw/", output_path: str = "data/processed/user_embeddings.parquet") -> None:
    """Genera embeddings conversacionales con text-embedding-3-large via Azure OpenAI y mean-pool por usuario (3072 dims)."""
    pass


if __name__ == "__main__":
    run_embeddings()
