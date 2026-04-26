"""Carga cacheada de datasets para el dashboard Streamlit."""

import json
import os
from datetime import datetime

import polars as pl
import streamlit as st

DATA_DIR = "data/processed/"


@st.cache_data(ttl=3600)
def load_clients() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "clientes_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_clientes.csv", ignore_errors=True)


@st.cache_data(ttl=3600)
def load_products() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "productos_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_productos.csv", ignore_errors=True)


@st.cache_data(ttl=3600)
def load_transactions() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "transacciones_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_csv("data/raw/hey_transacciones.csv", ignore_errors=True)


@st.cache_data(ttl=3600)
def load_havi() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "havi_clean.parquet")
    if os.path.exists(p):
        return pl.read_parquet(p)
    return pl.read_parquet("data/raw/dataset_50k_anonymized.parquet")


@st.cache_data(ttl=3600)
def load_segments() -> pl.DataFrame:
    return pl.read_parquet(os.path.join(DATA_DIR, "user_segments.parquet"))


@st.cache_data(ttl=3600)
def load_feature_matrix() -> pl.DataFrame:
    p = os.path.join(DATA_DIR, "feature_matrix.parquet")
    df = pl.read_parquet(p)
    non_emb = [c for c in df.columns if not c.startswith("emb_")]
    return df.select(non_emb)


@st.cache_data(ttl=3600)
def load_profiles() -> list[dict]:
    with open(os.path.join(DATA_DIR, "segment_profiles.json"), encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def load_customer_dna() -> pl.DataFrame:
    return pl.read_parquet(os.path.join(DATA_DIR, "customer_dna.parquet"))


@st.cache_data(ttl=3600)
def load_conv_intents() -> pl.DataFrame:
    return pl.read_parquet(os.path.join(DATA_DIR, "conv_intents.parquet"))


def get_user_ids() -> list[str]:
    clients = load_clients()
    return sorted(clients["user_id"].to_list())


def get_profile_for_user(user_id: str) -> dict | None:
    segs = load_segments()
    profiles = load_profiles()
    user_row = segs.filter(pl.col("user_id") == user_id)
    if user_row.shape[0] == 0:
        return None
    cluster = user_row["cluster"][0]
    if cluster == -1:
        return None
    for p in profiles:
        if p["cluster_id"] == cluster:
            return p
    return None


def get_dna_for_user(user_id: str) -> str | None:
    dna = load_customer_dna()
    row = dna.filter(pl.col("user_id") == user_id)
    if row.shape[0] == 0:
        return None
    return row["dna_text"][0]


def get_action_for_user(user_id: str) -> str | None:
    dna = load_customer_dna()
    if "accion_proactiva" not in dna.columns:
        return None
    row = dna.filter(pl.col("user_id") == user_id)
    if row.shape[0] == 0:
        return None
    val = row["accion_proactiva"][0]
    return val if val else None


def get_data_timestamp() -> str:
    """Fecha de la ultima actualizacion de datos procesados."""
    files = [
        os.path.join(DATA_DIR, "clientes_clean.parquet"),
        os.path.join(DATA_DIR, "user_segments.parquet"),
        os.path.join(DATA_DIR, "feature_matrix.parquet"),
        os.path.join(DATA_DIR, "customer_dna.parquet"),
        os.path.join(DATA_DIR, "segment_profiles.json"),
    ]
    mtimes = [os.path.getmtime(f) for f in files if os.path.exists(f)]
    if not mtimes:
        return "N/A"
    latest = max(mtimes)
    return datetime.fromtimestamp(latest).strftime("%d/%m/%Y %H:%M")


def filter_by_segments(df: pl.DataFrame, segment_ids: list[int],
                       segments_df: pl.DataFrame | None = None) -> pl.DataFrame:
    """Filtra un DataFrame por los user_id pertenecientes a los segmentos indicados."""
    if not segment_ids:
        return df
    if segments_df is None:
        segments_df = load_segments()
    seg_users = segments_df.filter(
        pl.col("cluster").is_in(segment_ids)
    )["user_id"].to_list()
    if "user_id" in df.columns:
        return df.filter(pl.col("user_id").is_in(seg_users))
    return df


def filter_by_date_range(df: pl.DataFrame,
                         date_col: str = "fecha_hora",
                         start_date=None,
                         end_date=None) -> pl.DataFrame:
    """Filtra un DataFrame por rango de fechas."""
    if date_col not in df.columns:
        return df
    if start_date is not None:
        df = df.filter(pl.col(date_col) >= start_date)
    if end_date is not None:
        df = df.filter(pl.col(date_col) <= end_date)
    return df
