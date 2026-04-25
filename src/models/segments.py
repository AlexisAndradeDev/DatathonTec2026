"""Perfilamiento de segmentos y labeling con LLM via DeepSeek-V3.2."""

from ..enrichment.llm_client import chat_completion, estimate_tokens


def run_segments(input_path: str = "data/processed/user_segments.parquet", output_path: str = "data/processed/segment_profiles.json") -> None:
    """Genera estadísticas, SHAP, LLM labeling y acciones proactivas por segmento via DeepSeek-V3.2."""
    pass


if __name__ == "__main__":
    run_segments()
