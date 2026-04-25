"""Herramientas del chatbot: account summary, transactions, recommendation.

Las tool definitions se exportan como lista de dicts en formato OpenAI.
"""


def get_account_summary(user_id: str) -> dict:
    """Retorna resumen de cuenta: productos, saldos, créditos, inversiones."""
    pass


def get_recent_transactions(user_id: str, n: int = 5) -> dict:
    """Retorna últimas N transacciones + alerta de cargos atípicos."""
    pass


def get_recommendation(user_id: str) -> dict:
    """Retorna recomendación personalizada según segmento."""
    pass


TOOLS_DICT: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_account_summary",
            "description": "Retorna el resumen de cuenta del usuario: productos activos con saldo/límite, créditos con utilización, inversiones, seguros activos y cashback acumulado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "El ID del usuario (ej. USR-00042)",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_transactions",
            "description": "Retorna las últimas N transacciones del usuario con fecha, monto, comercio, categoría, estatus y cashback. Incluye alerta si hay cargos atípicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "El ID del usuario (ej. USR-00042)",
                    },
                    "n": {
                        "type": "integer",
                        "description": "Número de transacciones a retornar (default 5)",
                        "default": 5,
                    },
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendation",
            "description": "Retorna una recomendación personalizada según el segmento y perfil del usuario: oferta segmentada, alerta de cargos, insight de gastos o promoción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "El ID del usuario (ej. USR-00042)",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
]
