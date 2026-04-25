"""Normalización de descripciones de transacciones via DeepSeek-V3.2 (o fallback regex)."""

from .llm_client import chat_completion, estimate_tokens


def run_descriptions(input_path: str = "data/raw/", output_path: str = "data/processed/tx_enriched.parquet") -> None:
    """Extrae merchant_name, category, is_subscription, is_recurring de descripcion_libre via DeepSeek-V3.2."""
    pass


if __name__ == "__main__":
    run_descriptions()
