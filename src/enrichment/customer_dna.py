"""Customer DNA narrativo — perfil de ~150 palabras por usuario via template Python.

Template deterministico con logica condicional para necesidades implicitas
y oportunidades proactivas. Sin LLM, sin costo de API.

Output: customer_dna.parquet (user_id, dna_text).
"""

import os
import time

import polars as pl

SEXO_MAP = {"M": "Mujer", "H": "Hombre", "SE": "Sin especificar"}
OCUPACION_MAP = {
    "Empleado": "empleado", "Independiente": "independiente",
    "Estudiante": "estudiante", "Empresario": "empresario",
    "Desempleado": "desempleado", "Jubilado": "jubilado",
}
CATEGORIA_VERBOSE = {
    "supermercado": "supermercado", "restaurante": "restaurantes",
    "delivery": "delivery", "entretenimiento": "entretenimiento",
    "transporte": "transporte", "servicios_digitales": "servicios digitales",
    "salud": "salud", "educacion": "educacion",
    "ropa_accesorios": "ropa y accesorios", "tecnologia": "tecnologia",
    "viajes": "viajes", "gobierno": "pagos de gobierno",
    "hogar": "hogar", "transferencia": "transferencias",
}
CANAL_MAP = {
    "app_ios": "iOS", "app_android": "Android", "app_huawei": "Huawei",
}


def _genero_articulo(palabra: str) -> str:
    """Determina si usar 'el/la' basado en genero."""
    if palabra == "Mujer":
        return "la"
    return "el"


def _build_dna(
    uid: str,
    demo: dict,
    prods: list[dict],
    tx_categories: list[str],
    tx_count: int,
    conv_count: int,
    channel_source_counts: dict,
) -> str:
    """Construye el perfil narrativo con template + logica condicional."""

    sexo_txt = SEXO_MAP.get(demo.get("sexo", ""), "Persona")
    art = _genero_articulo(sexo_txt)
    edad = demo.get("edad", "?")
    estado = demo.get("estado")
    ciudad = demo.get("ciudad")
    ocupacion = OCUPACION_MAP.get(demo.get("ocupacion", ""), "")
    ingreso = demo.get("ingreso_mensual_mxn", 0)
    educacion = (demo.get("nivel_educativo") or "").lower()
    hey_pro = demo.get("es_hey_pro", False)
    nomina = demo.get("nomina_domiciliada", False)
    score = demo.get("score_buro", 0)
    satisfaccion = demo.get("satisfaccion_1_10", 0)
    antiguedad = demo.get("antiguedad_dias", 0)
    ultimo_login = demo.get("dias_desde_ultimo_login", 0)
    canal = CANAL_MAP.get(demo.get("preferencia_canal", ""), "digital")
    patron_atipico = demo.get("patron_uso_atipico", False)
    tiene_seguro = demo.get("tiene_seguro", False)
    recibe_remesas = demo.get("recibe_remesas", False)
    usa_hey_shop = demo.get("usa_hey_shop", False)
    idioma = demo.get("idioma_preferido", "es_MX")

    # --- Parrafo 1: Demografia ---
    ubicacion = ""
    if ciudad and estado:
        ubicacion = f", reside en {ciudad}, {estado}"
    elif estado:
        ubicacion = f", reside en {estado}"

    lines = [
        f"{sexo_txt}, {edad} años {ubicacion}. "
        f"{art.capitalize()} {ocupacion} con ingreso mensual de ${ingreso:,} MXN"
        + (f", nivel educativo {educacion}" if educacion else "") + ".",
    ]

    # --- Parrafo 2: Relacion con el banco ---
    eng = []
    if hey_pro:
        eng.append("Hey Pro")
    if nomina:
        eng.append("nomina domiciliada")
    if recibe_remesas:
        eng.append("recibe remesas")
    if tiene_seguro:
        eng.append("tiene seguros activos")
    if usa_hey_shop:
        eng.append("usa Hey Shop")

    score_desc = "excelente" if score >= 700 else ("bueno" if score >= 600 else "en desarrollo")
    sat = satisfaccion
    sat_desc = "satisfecho" if sat and sat >= 8 else ("neutral" if sat and sat >= 6 else "insatisfecho")

    lines.append(
        f"Cliente con {antiguedad} dias de antiguedad, "
        f"score buro {score_desc} ({score}), {sat_desc} ({sat}/10). "
        + (f"Cuenta con {', '.join(eng)}. " if eng else "")
        + f"Prefiere canal {canal}, ultimo login hace {ultimo_login} dias."
    )

    # --- Parrafo 3: Productos ---
    if prods:
        prod_names = []
        for p in prods:
            tipo = p.get("tipo_producto", "").replace("_", " ")
            if p.get("saldo_actual") is not None:
                prod_names.append(f"{tipo} (saldo ${p['saldo_actual']:,.0f})")
            else:
                prod_names.append(tipo)
        lines.append(f"Productos activos: {', '.join(prod_names)}.")
    else:
        lines.append("Sin productos financieros activos.")

    # --- Parrafo 4: Gastos ---
    if tx_categories:
        top_cats = tx_categories[:3]
        cat_str = ", ".join(CATEGORIA_VERBOSE.get(c, c) for c in top_cats)
        lines.append(
            f"Patron de gasto concentrado en {cat_str}. "
            f"Total de {tx_count} movimientos registrados."
        )
    else:
        lines.append("Sin movimientos transaccionales registrados.")

    # --- Parrafo 5: Conversaciones ---
    if conv_count > 0:
        txt_msgs = channel_source_counts.get("1", 0)
        voice_msgs = channel_source_counts.get("2", 0)
        canal_txt = f"({txt_msgs} texto, {voice_msgs} voz)" if voice_msgs > 0 else "(solo texto)"
        lines.append(
            f"Ha contactado a Havi en {conv_count} ocasiones {canal_txt}."
        )
    else:
        lines.append("No ha contactado al asistente virtual Havi.")

    # --- Parrafo 6: Necesidades implicitas y oportunidades ---
    oportunidades = []

    # TC para buen score sin tarjeta de credito
    tiene_tc = any(
        "tarjeta_credito" in p.get("tipo_producto", "")
        for p in prods
    )
    if score >= 680 and not tiene_tc and hey_pro:
        oportunidades.append(
            "ofrecer Tarjeta de Credito Hey con 5% cashback"
        )

    # Inversion para ingreso alto con saldo en debito
    saldo_debito = sum(
        p.get("saldo_actual", 0) or 0
        for p in prods
        if "debito" in p.get("tipo_producto", "")
    )
    tiene_inversion = any(
        "inversion" in p.get("tipo_producto", "")
        for p in prods
    )
    if saldo_debito > 10000 and not tiene_inversion:
        oportunidades.append(
            "sugerir abrir Inversion Hey para generar rendimientos"
        )

    # Seguro para quien no tiene
    if not tiene_seguro and hey_pro:
        oportunidades.append(
            "recomendar seguro de proteccion de compras Hey"
        )

    # Alerta por patron atipico
    if patron_atipico:
        oportunidades.append(
            "revisar actividad inusual detectada en su cuenta"
        )

    # Reactivacion si no loguea hace mucho
    if ultimo_login and ultimo_login > 30:
        oportunidades.append(
            "campana de reactivacion digital"
        )

    # Satisfaccion baja → atencion prioritaria
    if sat is not None and sat <= 5:
        oportunidades.append(
            "llamada de seguimiento para mejorar satisfaccion"
        )

    # Hey Shop si no lo usa
    if not usa_hey_shop and hey_pro:
        oportunidades.append("invitar a conocer Hey Shop")

    if oportunidades:
        lines.append(
            "Oportunidades proactivas: " + "; ".join(oportunidades) + "."
        )
    else:
        lines.append(
            "Cliente bien atendido con productos alineados a su perfil."
        )

    return " ".join(lines), "; ".join(oportunidades).capitalize() if oportunidades else ""


def run_customer_dna(
    data_dir: str = "data/processed/",
    output_path: str = "data/processed/customer_dna.parquet",
    min_convs: int = 1,
) -> None:
    """Genera perfil narrativo por usuario via template Python.

    Pipeline:
    1. Cargar clientes, productos, transacciones, Havi.
    2. Extraer estadisticas agregadas por usuario (categorias top, canales, etc.).
    3. Filtrar usuarios con >= min_convs conversaciones.
    4. Template → texto narrativo de ~150 palabras.
    5. Guardar customer_dna.parquet (user_id, dna_text).

    Args:
        data_dir: Directorio con datos limpios o raw.
        output_path: Ruta del Parquet de salida.
        min_convs: Minimo de conversaciones Havi para incluir al usuario.
    """

    t_start = time.monotonic()

    # --- 1. Cargar datos ---
    def _load_parquet(name: str, csv_name: str) -> pl.DataFrame:
        pq_path = os.path.join(data_dir, name)
        if os.path.exists(pq_path):
            return pl.read_parquet(pq_path)
        csv_path = os.path.join("data/raw/", csv_name)
        return pl.read_csv(csv_path, ignore_errors=True)

    clientes = _load_parquet("clientes_clean.parquet", "hey_clientes.csv")
    productos = _load_parquet("productos_clean.parquet", "hey_productos.csv")
    transacciones = _load_parquet("transacciones_clean.parquet", "hey_transacciones.csv")
    havi = _load_parquet("havi_clean.parquet", "dataset_50k_anonymized.parquet")

    print(f"[LOAD]  Clientes: {clientes.shape[0]:,} | Productos: {productos.shape[0]:,} | "
          f"Transacciones: {transacciones.shape[0]:,} | Havi: {havi.shape[0]:,}")

    # --- 2. Agregaciones por usuario ---

    # Conversaciones por usuario
    user_conv_agg = (
        havi
        .group_by("user_id")
        .agg([
            pl.col("conv_id").n_unique().alias("conv_count"),
            pl.len().alias("msg_count"),
            (pl.col("channel_source") == "1").sum().alias("n_text"),
            (pl.col("channel_source") == "2").sum().alias("n_voice"),
        ])
    )

    # Filtrar usuarios elegibles
    eligible = user_conv_agg.filter(pl.col("conv_count") >= min_convs)
    eligible_ids = set(eligible["user_id"].to_list())
    print(f"[FILTER] {len(eligible_ids):,} usuarios con >= {min_convs} conversaciones")

    # Categorias top por usuario desde transacciones
    tx_agg = (
        transacciones
        .filter(pl.col("user_id").is_in(eligible_ids))
        .group_by("user_id", "categoria_mcc")
        .len()
        .sort(["user_id", "len"], descending=[False, True])
        .group_by("user_id")
        .agg(pl.col("categoria_mcc").head(5).alias("top_categories"))
    )
    tx_counts = (
        transacciones
        .filter(pl.col("user_id").is_in(eligible_ids))
        .group_by("user_id")
        .len()
    )

    # Indexar
    clients_map = {}
    for row in clientes.iter_rows():
        uid = row[clientes.columns.index("user_id")]
        if uid in eligible_ids:
            clients_map[uid] = {col: row[clientes.columns.index(col)] for col in clientes.columns}

    prods_map: dict[str, list[dict]] = {}
    for row in productos.iter_rows():
        uid = row[productos.columns.index("user_id")]
        if uid in eligible_ids:
            prods_map.setdefault(uid, []).append({
                col: row[productos.columns.index(col)] for col in productos.columns
            })

    tx_cats_map = {}
    for row in tx_agg.iter_rows():
        uid = row[0]
        tx_cats_map[uid] = row[1] if row[1] is not None else []

    tx_count_map = {}
    for row in tx_counts.iter_rows():
        tx_count_map[row[0]] = row[1]

    conv_stats_map = {}
    for row in eligible.iter_rows():
        uid = row[0]
        conv_stats_map[uid] = {
            "conv_count": row[1],
            "msg_count": row[2],
            "n_text": row[3],
            "n_voice": row[4],
        }

    # --- 3. Generar DNA narrativo ---
    results: list[dict] = []

    def _progress_bar(current: int, total: int, width: int = 30) -> str:
        pct = current / total
        filled = int(width * pct)
        return "|" + "█" * filled + "░" * (width - filled) + f"| {current}/{total} ({pct*100:5.1f}%)"

    n_total = len(eligible_ids)
    print(f"[DNA]   Generando {n_total:,} perfiles narrativos...")

    for i, uid in enumerate(eligible_ids):
        demo = clients_map.get(uid, {})
        prods = prods_map.get(uid, [])
        top_cats = tx_cats_map.get(uid, [])
        tx_n = tx_count_map.get(uid, 0)
        cs = conv_stats_map.get(uid, {})
        conv_n = cs.get("conv_count", 0)
        ch_counts = {"1": cs.get("n_text", 0), "2": cs.get("n_voice", 0)}

        dna, accion = _build_dna(uid, demo, prods, top_cats, tx_n, conv_n, ch_counts)
        results.append({"user_id": uid, "dna_text": dna, "accion_proactiva": accion})

        if (i + 1) % 500 == 0:
            bar = _progress_bar(i + 1, n_total)
            print(f"\r  [DNA]   {bar}", end="", flush=True)

    bar = _progress_bar(n_total, n_total)
    print(f"\r  [DNA]   {bar}")

    # --- 4. Guardar ---
    df = pl.DataFrame(results)
    df.write_parquet(output_path, compression="snappy")
    t_total = time.monotonic() - t_start
    print(f"[SAVE]  {output_path} ({df.shape[0]:,} filas x {df.shape[1]} cols)")
    print(f"  Tiempo: {t_total:.1f}s | Costo: $0.00 USD")


if __name__ == "__main__":
    run_customer_dna()
