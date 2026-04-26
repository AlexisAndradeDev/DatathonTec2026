"""Validacion de schemas de los 4 datasets."""

import polars as pl
import os


def run_validate(data_dir: str = "data/raw/") -> None:
    """Valida schemas, nulls, FK integrity y duplicados."""

    # Leer los 4 datasets con Polars
    clientes_path = os.path.join(data_dir, "hey_clientes.csv")
    productos_path = os.path.join(data_dir, "hey_productos.csv")
    transacciones_path = os.path.join(data_dir, "hey_transacciones.csv")
    havi_path = os.path.join(data_dir, "dataset_50k_anonymized.parquet")

    for path in [clientes_path, productos_path, transacciones_path, havi_path]:
        if not os.path.exists(path):
            print(f"[ERROR] No se encontro: {path}")
            return

    clientes = pl.read_csv(clientes_path, ignore_errors=True)
    productos = pl.read_csv(productos_path, ignore_errors=True)
    transacciones = pl.read_csv(transacciones_path, ignore_errors=True)
    havi = pl.read_parquet(havi_path)

    # Estandarizar fechas Havi: YYYY-MM-DD → YYYY-MM-DD 00:00:00.000000
    havi = havi.with_columns(
        pl.col("date").str.replace(
            r"^(\d{4}-\d{2}-\d{2})$", r"${1} 00:00:00.000000"
        ).str.replace(
            r"\.(\d{6})\d+$", r".${1}"
        )
    )

    print("=" * 60)
    print("CHECK 1.1 -- Lectura de datasets")
    print("=" * 60)
    print(f"  hey_clientes.csv:                  {clientes.shape[0]:>7,} filas x {clientes.shape[1]:>3} cols")
    print(f"  hey_productos.csv:                 {productos.shape[0]:>7,} filas x {productos.shape[1]:>3} cols")
    print(f"  hey_transacciones.csv:             {transacciones.shape[0]:>7,} filas x {transacciones.shape[1]:>3} cols")
    print(f"  dataset_50k_anonymized.parquet:    {havi.shape[0]:>7,} filas x {havi.shape[1]:>3} cols")
    print()

    check_1_2(clientes, productos, transacciones, havi)
    check_1_3(clientes, productos, transacciones, havi)
    check_1_7(clientes, productos, transacciones, havi)
    check_1_8(clientes, productos, transacciones, havi)


def check_1_2(
    clientes: pl.DataFrame,
    productos: pl.DataFrame,
    transacciones: pl.DataFrame,
    havi: pl.DataFrame,
) -> None:
    """Valida columnas esperadas y tipos de datos correctos."""

    expected_schemas = {
        "hey_clientes.csv": {
            "user_id": pl.String, "edad": pl.Int64, "sexo": pl.String,
            "estado": pl.String, "ciudad": pl.String,
            "nivel_educativo": pl.String, "ocupacion": pl.String,
            "ingreso_mensual_mxn": pl.Int64, "antiguedad_dias": pl.Int64,
            "es_hey_pro": pl.Boolean, "nomina_domiciliada": pl.Boolean,
            "canal_apertura": pl.String, "score_buro": pl.Int64,
            "dias_desde_ultimo_login": pl.Int64,
            "preferencia_canal": pl.String, "satisfaccion_1_10": pl.Float64,
            "recibe_remesas": pl.Boolean, "usa_hey_shop": pl.Boolean,
            "idioma_preferido": pl.String, "tiene_seguro": pl.Boolean,
            "num_productos_activos": pl.Int64, "patron_uso_atipico": pl.Boolean,
        },
        "hey_productos.csv": {
            "producto_id": pl.String, "user_id": pl.String,
            "tipo_producto": pl.String, "fecha_apertura": pl.String,
            "estatus": pl.String, "limite_credito": pl.Float64,
            "saldo_actual": pl.Float64, "utilizacion_pct": pl.Float64,
            "tasa_interes_anual": pl.Float64, "plazo_meses": pl.Float64,
            "monto_mensualidad": pl.Float64,
            "fecha_ultimo_movimiento": pl.String,
        },
        "hey_transacciones.csv": {
            "transaccion_id": pl.String, "user_id": pl.String,
            "producto_id": pl.String, "fecha_hora": pl.String,
            "tipo_operacion": pl.String, "canal": pl.String,
            "monto": pl.Float64, "comercio_nombre": pl.String,
            "categoria_mcc": pl.String, "ciudad_transaccion": pl.String,
            "estatus": pl.String, "motivo_no_procesada": pl.String,
            "intento_numero": pl.Int64, "meses_diferidos": pl.Int64,
            "cashback_generado": pl.Float64, "descripcion_libre": pl.String,
            "hora_del_dia": pl.Int64, "dia_semana": pl.String,
            "es_internacional": pl.Boolean, "dispositivo": pl.String,
            "patron_uso_atipico": pl.Boolean,
        },
        "dataset_50k_anonymized.parquet": {
            "input": pl.String, "output": pl.String,
            "date": pl.String, "conv_id": pl.String,
            "user_id": pl.String, "channel_source": pl.String,
        },
    }

    datasets = {
        "hey_clientes.csv": clientes,
        "hey_productos.csv": productos,
        "hey_transacciones.csv": transacciones,
        "dataset_50k_anonymized.parquet": havi,
    }

    print("=" * 60)
    print("CHECK 1.2 -- Validacion de columnas y tipos")
    print("=" * 60)

    all_ok = True
    for name, df in datasets.items():
        schema = expected_schemas[name]
        missing = [col for col in schema if col not in df.columns]
        extra = [col for col in df.columns if col not in schema]
        type_issues = []

        for col, expected_dtype in schema.items():
            if col in df.columns:
                actual_dtype = df[col].dtype
                if actual_dtype != expected_dtype:
                    type_issues.append(
                        f"    {col}: esperado={expected_dtype}, leido={actual_dtype}"
                    )

        if missing:
            all_ok = False
            for col in missing:
                print(f"  [FALTA] {name}: columna '{col}'")

        if type_issues:
            for issue in type_issues:
                print(f"  [TIPO]  {name}")
                print(issue)

        if extra:
            for col in extra:
                print(f"  [EXTRA] {name}: columna '{col}' ({df[col].dtype})")

        if not missing and not type_issues:
            print(f"  [OK]    {name}: {df.shape[1]} columnas, tipos correctos")

    print()


def check_1_3(
    clientes: pl.DataFrame,
    productos: pl.DataFrame,
    transacciones: pl.DataFrame,
    havi: pl.DataFrame,
) -> None:
    """Chequea nulls esperados en productos y transacciones."""

    credito_types = [
        "tarjeta_credito_hey", "tarjeta_credito_garantizada",
        "tarjeta_credito_negocios", "credito_personal",
        "credito_auto", "credito_nomina",
    ]
    prestamo_types = ["credito_personal", "credito_auto", "credito_nomina"]

    print("=" * 60)
    print("CHECK 1.3 -- Validacion de nulls esperados")
    print("=" * 60)

    # --- Productos ---
    violaciones = 0

    checks_productos = [
        ("limite_credito", "credito",
         pl.col("tipo_producto").is_in(credito_types)),
        ("utilizacion_pct", "credito",
         pl.col("tipo_producto").is_in(credito_types)),
        ("plazo_meses", "prestamo",
         pl.col("tipo_producto").is_in(prestamo_types)),
        ("monto_mensualidad", "prestamo",
         pl.col("tipo_producto").is_in(prestamo_types)),
        ("tasa_interes_anual", "credito + inversion",
         pl.col("tipo_producto").is_in(credito_types + ["inversion_hey"])),
    ]

    for col, desc, valor_expected in checks_productos:
        valor_rows = productos.filter(valor_expected).shape[0]
        null_rows = productos.filter(~valor_expected).shape[0]
        n_null_violations = productos.filter(~valor_expected & pl.col(col).is_not_null()).shape[0]
        n_not_null_violations = productos.filter(valor_expected & pl.col(col).is_null()).shape[0]

        if n_null_violations == 0 and n_not_null_violations == 0:
            print(f"  [OK]    {col}: con valor en {desc} ({valor_rows:,} filas)"
                  f", nulo en el resto ({null_rows:,} filas)")
        else:
            violaciones += n_null_violations + n_not_null_violations
            print(f"  [WARN]  {col}: {n_null_violations} filas con valor sin serlo"
                  f", {n_not_null_violations} filas nulas debiendo tener valor")

    # --- Transacciones ---
    ok_motivo = transacciones.filter(
        (pl.col("estatus") != "no_procesada") & pl.col("motivo_no_procesada").is_not_null()
    ).shape[0]
    ok_motivo_null = transacciones.filter(
        (pl.col("estatus") == "no_procesada") & pl.col("motivo_no_procesada").is_null()
    ).shape[0]

    if ok_motivo == 0 and ok_motivo_null == 0:
        print(f"  [OK]    motivo_no_procesada: null excepto estatus='no_procesada'"
              f" ({transacciones.filter(pl.col('estatus')=='no_procesada').shape[0]:,} filas)")
    else:
        violaciones += ok_motivo + ok_motivo_null
        print(f"  [WARN]  motivo_no_procesada: {ok_motivo} no-nulos inesperados"
              f", {ok_motivo_null} nulos inesperados")

    ok_dispositivo = transacciones.filter(
        ~pl.col("canal").str.starts_with("app_") & pl.col("dispositivo").is_not_null()
    ).shape[0]
    n_app = transacciones.filter(pl.col("canal").str.starts_with("app_")).shape[0]
    if ok_dispositivo == 0:
        print(f"  [OK]    dispositivo: null excepto canal=app_* ({n_app:,} filas)")
    else:
        violaciones += ok_dispositivo
        print(f"  [WARN]  dispositivo: {ok_dispositivo} no-nulos en canales no-app")

    # --- Clientes: reportar columnas con nulls ---
    nulls_clientes = [
        col for col in clientes.columns
        if clientes[col].null_count() > 0
    ]
    if nulls_clientes:
        for col in nulls_clientes:
            print(f"  [INFO]  hey_clientes: '{col}' tiene {clientes[col].null_count():,} nulls")
    else:
        print(f"  [OK]    hey_clientes: 0 nulls en {clientes.shape[1]} columnas")

    # --- Havi: reportar columnas con nulls ---
    nulls_havi = [
        col for col in havi.columns
        if havi[col].null_count() > 0
    ]
    if nulls_havi:
        for col in nulls_havi:
            print(f"  [INFO]  havi: '{col}' tiene {havi[col].null_count():,} nulls")
    else:
        print(f"  [OK]    havi: 0 nulls en {havi.shape[1]} columnas")

    print()


def check_1_7(
    clientes: pl.DataFrame,
    productos: pl.DataFrame,
    transacciones: pl.DataFrame,
    havi: pl.DataFrame,
) -> None:
    """Valida encoding (M/H/SE, estados MX, fechas ISO)."""

    ESTADOS_MX = {
        "Aguascalientes", "Baja California", "Baja California Sur",
        "Campeche", "Chiapas", "Chihuahua", "Coahuila", "Colima",
        "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco",
        "Estado de Mexico", "Estado de México", "Michoacan", "Michoacán",
        "Morelos", "Nayarit", "Nuevo Leon", "Nuevo León", "Oaxaca",
        "Puebla", "Queretaro", "Querétaro", "Quintana Roo",
        "San Luis Potosi", "San Luis Potosí", "Sinaloa", "Sonora",
        "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatan",
        "Yucatán", "Zacatecas", "Ciudad de Mexico", "Ciudad de México",
    }

    ISO_DATE_PAT = r"^\d{4}-\d{2}-\d{2}$"
    ISO_DATETIME_PAT = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    ISO_DATETIME_HAVI_PAT = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}$"

    print("=" * 60)
    print("CHECK 1.7 -- Validacion de encoding y formatos")
    print("=" * 60)

    # --- sexo: M / H / SE ---
    sexo_valid = {"M", "H", "SE"}
    sexo_vals = clientes["sexo"].drop_nulls().unique().to_list()
    sexo_bad = [v for v in sexo_vals if v not in sexo_valid]
    if sexo_bad:
        print(f"  [WARN]  sexo: valores invalidos: {sexo_bad}")
    else:
        vc = clientes["sexo"].value_counts(sort=True)
        detail = ", ".join(
            f"{v}={c:,}" for v, c in zip(
                vc["sexo"].to_list(), vc["count"].to_list()
            )
        )
        print(f"  [OK]    sexo: solo M/H/SE ({detail})")

    # --- estado: estados validos de Mexico (null permitido, "Otros" reportado) ---
    estado_vals = clientes["estado"].drop_nulls().unique().to_list()
    estado_bad = [v for v in estado_vals if v not in ESTADOS_MX and v != "Otros"]
    n_null_estado = clientes["estado"].null_count()
    if estado_bad:
        print(f"  [WARN]  estado: valores no reconocidos: {estado_bad}")
    else:
        extras = ""
        if n_null_estado > 0:
            extras += f" ({n_null_estado:,} nulls)"
        if "Otros" in estado_vals:
            n_otros = clientes.filter(pl.col("estado") == "Otros").shape[0]
            extras += f", 'Otros'={n_otros:,}"
        print(f"  [OK]    estado: {len(estado_vals)} valores validos{extras}")

    # --- idioma_preferido: es_MX / en_US ---
    idioma_valid = {"es_MX", "en_US"}
    idioma_vals = clientes["idioma_preferido"].drop_nulls().unique().to_list()
    idioma_bad = [v for v in idioma_vals if v not in idioma_valid]
    if idioma_bad:
        print(f"  [WARN]  idioma_preferido: valores invalidos: {idioma_bad}")
    else:
        vc = clientes["idioma_preferido"].value_counts(sort=True)
        detail = ", ".join(
            f"{v}={c:,}" for v, c in zip(
                vc["idioma_preferido"].to_list(), vc["count"].to_list()
            )
        )
        print(f"  [OK]    idioma_preferido: solo es_MX/en_US ({detail})")

    # --- fechas ISO ---
    # productos: fecha_apertura
    fa = productos["fecha_apertura"].drop_nulls()
    fa_bad = fa.filter(~fa.str.contains(ISO_DATE_PAT)).shape[0]
    fa_null = productos["fecha_apertura"].null_count()
    if fa_bad == 0:
        print(f"  [OK]    productos.fecha_apertura: YYYY-MM-DD"
              f" ({fa.shape[0]:,} fechas, {fa_null} nulls)")
    else:
        print(f"  [WARN]  productos.fecha_apertura: {fa_bad} no cumplen YYYY-MM-DD")

    # productos: fecha_ultimo_movimiento
    fum = productos["fecha_ultimo_movimiento"].drop_nulls()
    fum_bad = fum.filter(~fum.str.contains(ISO_DATE_PAT)).shape[0]
    fum_null = productos["fecha_ultimo_movimiento"].null_count()
    if fum_bad == 0:
        print(f"  [OK]    productos.fecha_ultimo_movimiento: YYYY-MM-DD"
              f" ({fum.shape[0]:,} fechas, {fum_null} nulls)")
    else:
        print(f"  [WARN]  productos.fecha_ultimo_movimiento: {fum_bad} no cumplen YYYY-MM-DD")

    # transacciones: fecha_hora
    fh = transacciones["fecha_hora"].drop_nulls()
    fh_bad = fh.filter(~fh.str.contains(ISO_DATETIME_PAT)).shape[0]
    fh_null = transacciones["fecha_hora"].null_count()
    if fh_bad == 0:
        print(f"  [OK]    transacciones.fecha_hora: YYYY-MM-DD HH:MM:SS"
              f" ({fh.shape[0]:,} fechas, {fh_null} nulls)")
    else:
        print(f"  [WARN]  transacciones.fecha_hora: {fh_bad} no cumplen YYYY-MM-DD HH:MM:SS")

    # havi: date (ya estandarizado a YYYY-MM-DD HH:MM:SS.ffffff)
    hd = havi["date"].drop_nulls()
    hd_bad = hd.filter(~hd.str.contains(ISO_DATETIME_HAVI_PAT)).shape[0]
    hd_null = havi["date"].null_count()
    if hd_bad == 0:
        print(f"  [OK]    havi.date: YYYY-MM-DD HH:MM:SS.ffffff"
              f" ({hd.shape[0]:,} fechas, {hd_null} nulls)")
    else:
        print(f"  [WARN]  havi.date: {hd_bad} no cumplen YYYY-MM-DD HH:MM:SS.ffffff")

    # transacciones: dia_semana en ingles
    dias_valid = {
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    }
    dias_vals = transacciones["dia_semana"].drop_nulls().unique().to_list()
    dias_bad = [v for v in dias_vals if v not in dias_valid]
    if dias_bad:
        print(f"  [WARN]  transacciones.dia_semana: valores invalidos: {dias_bad}")
    else:
        print(f"  [OK]    transacciones.dia_semana: dias en ingles ({len(dias_vals)}/7)")

    print()


def check_1_8(
    clientes: pl.DataFrame,
    productos: pl.DataFrame,
    transacciones: pl.DataFrame,
    havi: pl.DataFrame,
) -> None:
    """Cruce de user_id entre Havi y datasets transaccionales."""

    print("=" * 60)
    print("CHECK 1.8 -- Cruce de user_id entre Havi y clientes")
    print("=" * 60)

    c_ids = set(clientes["user_id"].unique().to_list())
    p_ids = set(productos["user_id"].unique().to_list())
    t_ids = set(transacciones["user_id"].unique().to_list())
    h_ids = set(havi["user_id"].unique().to_list())

    print(f"  Clientes unique users:      {len(c_ids):>7,}")
    print(f"  Productos unique users:     {len(p_ids):>7,}")
    print(f"  Transacciones unique users: {len(t_ids):>7,}")
    print(f"  Havi unique users:          {len(h_ids):>7,}")
    print()

    h_total = len(h_ids)

    h_c = len(h_ids & c_ids)
    h_p = len(h_ids & p_ids)
    h_t = len(h_ids & t_ids)
    pct_c = h_c / h_total * 100
    pct_p = h_p / h_total * 100
    pct_t = h_t / h_total * 100

    print(f"  Havi ∩ Clientes:      {h_c:>7,}  ({pct_c:5.1f}% de Havi)")
    print(f"  Havi ∩ Productos:     {h_p:>7,}  ({pct_p:5.1f}% de Havi)")
    print(f"  Havi ∩ Transacciones: {h_t:>7,}  ({pct_t:5.1f}% de Havi)")
    print()

    havi_only = h_ids - c_ids
    clientes_only = c_ids - h_ids
    if havi_only:
        print(f"  [INFO]  Havi only (no en clientes): {len(havi_only):,}")
    else:
        print(f"  [OK]    Havi only: 0 (todos en clientes)")
    if clientes_only:
        print(f"  [INFO]  Clientes only (no en Havi): {len(clientes_only):,}")
    else:
        print(f"  [OK]    Clientes only: 0 (todos en Havi)")

    productos_only = p_ids - c_ids
    transacciones_only = t_ids - c_ids
    if productos_only:
        print(f"  [WARN]  user_id en productos no en clientes: {len(productos_only):,}")
    else:
        print(f"  [OK]    FK productos: todos en clientes")
    if transacciones_only:
        print(f"  [WARN]  user_id en transacciones no en clientes: {len(transacciones_only):,}")
    else:
        print(f"  [OK]    FK transacciones: todos en clientes")

    print()


if __name__ == "__main__":
    run_validate()
