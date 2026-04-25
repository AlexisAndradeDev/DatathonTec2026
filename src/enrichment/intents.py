"""Extracción estructurada de intenciones por conversación.

Usa DeepSeek-V3.2 con JSON structured output via OpenAI-compatible endpoint.
"""

from .llm_client import chat_completion, estimate_tokens


def run_intents(input_path: str = "data/raw/", output_dir: str = "data/processed/") -> None:
    """Clasifica cada conversación por intent, sentiment, urgency y resolution via DeepSeek-V3.2."""
    pass


if __name__ == "__main__":
    run_intents()
