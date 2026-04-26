"""Carga y limpieza de los 4 datasets raw → processed."""

import os
import polars as pl


def run_ingest(
    raw_dir: str = "data/raw/",
    processed_dir: str = "data/processed/",
) -> None:
    """Carga datasets, limpia y guarda versiones en Parquet."""

    clientes_path = os.path.join(raw_dir, "hey_clientes.csv")
    productos_path = os.path.join(raw_dir, "hey_productos.csv")
    transacciones_path = os.path.join(raw_dir, "hey_transacciones.csv")
    havi_path = os.path.join(raw_dir, "dataset_50k_anonymized.parquet")

    for path in [clientes_path, productos_path, transacciones_path, havi_path]:
        if not os.path.exists(path):
            print(f"[ERROR] No se encontro: {path}")
            return

    os.makedirs(processed_dir, exist_ok=True)

    # --- Cargar ---
    clientes = pl.read_csv(clientes_path, ignore_errors=True)
    productos = pl.read_csv(productos_path, ignore_errors=True)
    transacciones = pl.read_csv(transacciones_path, ignore_errors=True)
    havi = pl.read_parquet(havi_path)

    # --- Limpiar ---

    # Havi: estandarizar fechas a YYYY-MM-DD HH:MM:SS.ffffff
    havi = havi.with_columns(
        pl.col("date").str.replace(
            r"^(\d{4}-\d{2}-\d{2})$", r"${1} 00:00:00.000000"
        ).str.replace(
            r"\.(\d{6})\d+$", r".${1}"
        )
    )

    # Productos: dropear es_dato_sintetico
    if "es_dato_sintetico" in productos.columns:
        productos = productos.drop("es_dato_sintetico")

    # Transacciones: dropear es_dato_sintetico
    if "es_dato_sintetico" in transacciones.columns:
        transacciones = transacciones.drop("es_dato_sintetico")

    # Transacciones: meses_diferidos String → Int64
    transacciones = transacciones.with_columns(
        pl.col("meses_diferidos")
        .cast(pl.Float64, strict=False)
        .cast(pl.Int64, strict=False)
    )

    # --- Guardar ---
    clientes.write_parquet(
        os.path.join(processed_dir, "clientes_clean.parquet"),
        compression="snappy",
    )
    productos.write_parquet(
        os.path.join(processed_dir, "productos_clean.parquet"),
        compression="snappy",
    )
    transacciones.write_parquet(
        os.path.join(processed_dir, "transacciones_clean.parquet"),
        compression="snappy",
    )
    havi.write_parquet(
        os.path.join(processed_dir, "havi_clean.parquet"),
        compression="snappy",
    )

    print("Datasets guardados en data/processed/:")
    print(f"  clientes_clean.parquet:       {clientes.shape[0]:>7,} filas x {clientes.shape[1]:>2} cols")
    print(f"  productos_clean.parquet:      {productos.shape[0]:>7,} filas x {productos.shape[1]:>2} cols")
    print(f"  transacciones_clean.parquet:  {transacciones.shape[0]:>7,} filas x {transacciones.shape[1]:>2} cols")
    print(f"  havi_clean.parquet:           {havi.shape[0]:>7,} filas x {havi.shape[1]:>2} cols")


def load_all(
    processed_dir: str = "data/processed/",
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Retorna los 4 datasets limpios cargados en memoria."""
    return (
        pl.read_parquet(os.path.join(processed_dir, "clientes_clean.parquet")),
        pl.read_parquet(os.path.join(processed_dir, "productos_clean.parquet")),
        pl.read_parquet(os.path.join(processed_dir, "transacciones_clean.parquet")),
        pl.read_parquet(os.path.join(processed_dir, "havi_clean.parquet")),
    )


if __name__ == "__main__":
    run_ingest()
