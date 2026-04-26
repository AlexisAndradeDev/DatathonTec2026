"""Herramientas del chatbot: account summary, transactions, recommendation.

Implementación real usando datos de data/processed/.
"""

import os

import polars as pl

DATA_DIR = "data/processed/"


def _load_products() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "productos_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_productos.csv", ignore_errors=True)


def _load_transactions() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "transacciones_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_transacciones.csv", ignore_errors=True)


def _load_clients() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "clientes_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_clientes.csv", ignore_errors=True)


def _load_segments() -> pl.DataFrame:
    return pl.read_parquet(os.path.join(DATA_DIR, "user_segments.parquet"))


def _load_dna() -> pl.DataFrame:
    return pl.read_parquet(os.path.join(DATA_DIR, "customer_dna.parquet"))


def _load_profiles() -> list[dict]:
    import json
    with open(os.path.join(DATA_DIR, "segment_profiles.json"), encoding="utf-8") as f:
        return json.load(f)


def get_account_summary(user_id: str) -> dict:
    """Retorna resumen de cuenta: productos, saldos, créditos, inversiones."""
    products = _load_products()
    clients = _load_clients()

    user_prods = products.filter(pl.col("user_id") == user_id)
    user_client = clients.filter(pl.col("user_id") == user_id)

    if user_prods.shape[0] == 0:
        return {"productos": [], "total_deuda": 0, "total_inversiones": 0,
                "cashback_acumulado": 0, "hey_pro": False}

    prod_list = []
    total_deuda = 0.0
    total_inv = 0.0

    credit_types = {
        "tarjeta_credito_hey", "tarjeta_credito_garantizada",
        "tarjeta_credito_negocios", "credito_personal",
        "credito_auto", "credito_nomina",
    }

    for row in user_prods.iter_rows():
        cols = user_prods.columns
        tipo = row[cols.index("tipo_producto")]
        saldo = row[cols.index("saldo_actual")]
        limite = row[cols.index("limite_credito")]
        ut = row[cols.index("utilizacion_pct")]
        estatus = row[cols.index("estatus")]
        tasa = row[cols.index("tasa_interes_anual")]

        item = {"tipo": tipo, "saldo": saldo or 0, "estatus": estatus}
        if limite:
            item["limite"] = limite
            item["utilizado"] = saldo or 0
            item["utilizacion_pct"] = ut or 0
        if tasa:
            item["tasa_interes_anual"] = tasa

        if tipo in credit_types:
            total_deuda += (saldo or 0)
        elif tipo == "inversion_hey":
            total_inv += (saldo or 0)

        prod_list.append(item)

    hey_pro = False
    cashback = 0.0
    if user_client.shape[0] > 0:
        c = user_client
        hey_pro = c["es_hey_pro"][0]
        # approximate cashback from transactions
        tx = _load_transactions()
        user_tx = tx.filter(pl.col("user_id") == user_id)
        cashback = float(user_tx["cashback_generado"].sum() or 0)

    return {
        "productos": prod_list,
        "total_deuda": round(total_deuda, 2),
        "total_inversiones": round(total_inv, 2),
        "cashback_acumulado": round(cashback, 2),
        "hey_pro": hey_pro,
    }


def get_recent_transactions(user_id: str, n: int = 5) -> dict:
    """Retorna últimas N transacciones + alerta de cargos atípicos."""
    tx = _load_transactions()
    user_tx = tx.filter(pl.col("user_id") == user_id).sort(
        "fecha_hora", descending=True
    ).head(n)

    if user_tx.shape[0] == 0:
        return {"transacciones": [], "alerta": None}

    transacciones = []
    for row in user_tx.iter_rows():
        cols = user_tx.columns
        transacciones.append({
            "fecha": str(row[cols.index("fecha_hora")])[:19],
            "monto": float(row[cols.index("monto")] or 0),
            "comercio": row[cols.index("comercio_nombre")] or "—",
            "categoria": row[cols.index("categoria_mcc")] or "—",
            "estatus": row[cols.index("estatus")],
            "cashback": float(row[cols.index("cashback_generado")] or 0),
        })

    # Check for atypical activity
    has_atypical = any(
        row[user_tx.columns.index("patron_uso_atipico")] for row in user_tx.iter_rows()
    ) if "patron_uso_atipico" in user_tx.columns else False

    alerta = None
    if has_atypical:
        alerta = {
            "cargos_atipicos": True,
            "detalle": "Se detectaron movimientos con patrón de uso atípico en este período.",
        }

    return {"transacciones": transacciones, "alerta": alerta}


def get_recommendation(user_id: str) -> dict:
    """Retorna recomendacion personalizada desde Customer DNA."""
    dna_df = _load_dna()

    user_row = dna_df.filter(pl.col("user_id") == user_id)
    if user_row.shape[0] == 0:
        return {"tipo": "general", "titulo": "Explora Hey Banco",
                "descripcion": "Descubre todos los beneficios de Hey Banco.",
                "accion": "Conocer mas", "producto_relacionado": None}

    accion = user_row["accion_proactiva"][0] if "accion_proactiva" in dna_df.columns else ""
    if not accion:
        return {"tipo": "general", "titulo": "Cliente bien atendido",
                "descripcion": "Tus productos estan alineados a tu perfil financiero.",
                "accion": "Explorar Hey Shop", "producto_relacionado": None}

    return {
        "tipo": "recomendacion_personalizada",
        "titulo": accion,
        "descripcion": "Basado en tu perfil financiero y patron de uso.",
        "accion": "Activar beneficio",
        "producto_relacionado": "customer_dna",
    }


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

TOOL_EXECUTORS = {
    "get_account_summary": get_account_summary,
    "get_recent_transactions": get_recent_transactions,
    "get_recommendation": get_recommendation,
}

