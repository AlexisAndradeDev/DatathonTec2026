# HEY BANCO — DATATHON 2026
## Diccionario de Datos

### Archivos del dataset

| Archivo | Descripción |
|---------|-------------|
| `hey_clientes.csv` | Un registro por usuario. Demografía, relación con el banco y señales de comportamiento. |
| `hey_productos.csv` | Portafolio de productos por usuario.|
| `hey_transacciones.csv` | Historial de movimientos.|

---

### Relación entre tablas

```
hey_clientes.csv
    └── user_id ──┬──► hey_productos.csv    (user_id)
                  └──► hey_transacciones.csv (user_id)

hey_productos.csv
    └── producto_id ──► hey_transacciones.csv (producto_id)
```

---

### Diccionario — `hey_clientes.csv`

Un registro por usuario. Contiene información demográfica, relación con Hey Banco y señales de comportamiento digital.

| Columna | Tipo | Descripción | Valores posibles |
|---------|------|-------------|-----------------|
| `user_id` | str | Identificador único del usuario | `USR-00001`, `USR-00002`, … |
| `edad` | int | Edad del usuario en años |  |
| `genero` | str | Género del usuario | `M` (mujer) · `H` (hombre) · `SE` (sin especificar) |
| `estado` | str | Estado de la República Mexicana donde reside el usuario |  |
| `ciudad` | str | Ciudad de residencia del usuario dentro de su estado | |
| `nivel_educativo` | str | Último nivel de estudios del usuario | `Secundaria` · `Preparatoria` · `Licenciatura` · `Posgrado` |
| `ocupacion` | str | Situación laboral u ocupación del usuario | `Empleado` · `Independiente` · `Estudiante` · `Empresario` · `Desempleado` · `Jubilado` |
| `ingreso_mensual_mxn` | int | Ingreso mensual estimado en pesos mexicanos | |
| `antiguedad_dias` | int | Días transcurridos desde la apertura de cuenta | |
| `es_hey_pro` | bool | Indica si el usuario tiene suscripción Hey Pro activa (habilita cashback y beneficios) | `True` · `False` |
| `nomina_domiciliada` | bool | Indica si el usuario recibe su nómina directamente en su cuenta Hey Banco | `True` · `False` |
| `canal_apertura` | str | Canal por el que el usuario abrió su cuenta | `App` · `Fan Shop` |
| `score_buro` | int | Calificación crediticia del usuario (escala estándar de buró) | 295 – 850 |
| `dias_desde_ultimo_login` | int | Días transcurridos desde el último inicio de sesión del usuario en la app | 0 – 180 |
| `preferencia_canal` | str | Canal digital que el usuario utiliza con mayor frecuencia | `app_ios` · `app_android` · `app_huawei` |
| `satisfaccion_1_10` | int | Calificación de satisfacción registrada en encuesta NPS (escala 1 a 10) | 3 – 10 |
| `recibe_remesas` | bool | Indica si el usuario recibe remesas internacionales | `True` · `False` |
| `usa_hey_shop` | bool | Indica si el usuario ha realizado compras a través de Hey Shop | `True` · `False` |
| `idioma_preferido` | str | Idioma configurado en la app del usuario | `es_MX` · `en_US` |
| `tiene_seguro` | bool | Indica si el usuario tiene al menos un producto de seguro activo con Hey Banco | `True` · `False` |
| `num_productos_activos` | int | Cantidad de productos con estatus activo que tiene el usuario | |
| `patron_uso_atipico` | bool | Indica si se detectó un patrón de actividad inusual en el usuario | `True` · `False` |

---

### Diccionario — `hey_productos.csv`

Un registro por producto contratado. Un usuario puede tener múltiples productos.

| Columna | Tipo | Descripción | Valores posibles |
|---------|------|-------------|-----------------|
| `producto_id` | str | Identificador único del producto | `PRD-00000001`, `PRD-00000002`, … |
| `user_id` | str | Identificador del usuario dueño del producto (FK a `hey_clientes`) | `USR-00001`, … |
| `tipo_producto` | str | Tipo de producto contratado | Ver catálogo de productos abajo |
| `fecha_apertura` | date | Fecha en que se contrató el producto | `YYYY-MM-DD` |
| `estatus` | str | Estado actual del producto ||
| `limite_credito` | float | Límite de crédito autorizado en MXN (solo productos de crédito) | *(nulo para no-crédito)* |
| `saldo_actual` | float | Saldo actual del producto: deuda utilizada (créditos), saldo disponible (débito/negocio) o monto invertido (inversión) | ≥ 0.0 · *(nulo para seguros)* |
| `utilizacion_pct` | float | Porcentaje de utilización del crédito respecto al límite (0 = sin uso, 1 = límite agotado) | 0.0 – 1.0 · *(nulo para no-crédito)* |
| `tasa_interes_anual` | float | Tasa de interés anual aplicada al producto en porcentaje | *(nulo para productos sin interés)* |
| `plazo_meses` | int | Plazo del crédito en meses (solo productos de préstamo) | `6` · `12` · `18` · `24` · `36` · `48` · `60` · *(nulo para no-préstamo)* |
| `monto_mensualidad` | float | Monto de la mensualidad calculada (solo productos de préstamo) | > 0.0 · *(nulo para no-préstamo)* |
| `fecha_ultimo_movimiento` | date | Fecha del último movimiento registrado en el producto | `YYYY-MM-DD` |

**Catálogo de tipos de producto (`tipo_producto`)**

| Valor | Descripción |
|-------|-------------|
| `cuenta_debito` | Cuenta de débito principal del usuario |
| `tarjeta_credito_hey` | Tarjeta de crédito Hey Banco |
| `tarjeta_credito_garantizada` | Tarjeta de crédito garantizada (requiere depósito en garantía) |
| `tarjeta_credito_negocios` | Tarjeta de crédito para negocios |
| `credito_personal` | Crédito personal |
| `credito_auto` | Crédito automotriz |
| `credito_nomina` | Crédito sobre nómina domiciliada |
| `inversion_hey` | Producto de inversión Hey Banco (genera rendimiento GAT) |
| `seguro_vida` | Seguro de vida |
| `seguro_compras` | Seguro de protección de compras |
| `cuenta_negocios` | Cuenta de depósito para personas morales o negocios |

---

### Diccionario — `hey_transacciones.csv`

Un registro por movimiento.

| Columna | Tipo | Descripción | Valores posibles |
|---------|------|-------------|-----------------|
| `transaccion_id` | str | Identificador del movimiento | `TXN-0000000001`, … |
| `user_id` | str | Identificador del usuario que realizó el movimiento (FK a `hey_clientes`) | `USR-00001`, … |
| `producto_id` | str | Identificador del producto con el que se realizó el movimiento (FK a `hey_productos`) | `PRD-00000001`, … |
| `fecha_hora` | datetime | Fecha y hora exacta del movimiento | `YYYY-MM-DD HH:MM:SS` |
| `tipo_operacion` | str | Tipo de operación realizada | Ver catálogo de operaciones abajo |
| `canal` | str | Canal por el que se realizó el movimiento | Ver catálogo de canales abajo |
| `monto` | float | Monto del movimiento en pesos mexicanos | > 0.0 |
| `comercio_nombre` | str | Nombre del comercio donde se realizó la compra | Nombre del establecimiento · *(nulo para operaciones sin comercio)* |
| `categoria_mcc` | str | Categoría del comercio según clasificación MCC | `supermercado` · `restaurante` · `delivery` · `entretenimiento` · `transporte` · `servicios_digitales` · `salud` · `educacion` · `ropa_accesorios` · `tecnologia` · `viajes` · `gobierno` · `hogar` · `transferencia` |
| `ciudad_transaccion` | str | Ciudad donde se registró el movimiento | |
| `estatus` | str | Estado final del movimiento | `completada` · `no_procesada` · `en_disputa` · `revertida` |
| `motivo_no_procesada` | str | Razón por la que el movimiento no fue procesado | `saldo_insuficiente` · `tarjeta_bloqueada` · `limite_excedido` · `datos_invalidos` · `timeout_banco` · `codigo_incorrecto` · `cuenta_destino_invalida` · `monto_excede_limite_diario` · *(nulo si estatus ≠ no_procesada)* |
| `intento_numero` | int | Número de intento de la operación (mayor a 1 indica reintentos) | `1` · `2` · `3` |
| `meses_diferidos` | int | Meses sin intereses aplicados a la compra (MSI) | `3` · `6` · `9` · `12` · `24` · *(nulo si no aplica MSI)* |
| `cashback_generado` | float | Monto de cashback generado por la compra (1% del monto, solo usuarios Hey Pro con compra completada) | > 0.0 · *(nulo si no aplica)* |
| `descripcion_libre` | str | Descripción de texto libre del movimiento, tal como fue capturada en el sistema | Texto libre |
| `hora_del_dia` | int | Hora del día en que ocurrió el movimiento (formato 24 hrs) | 0 – 23 |
| `dia_semana` | str | Día de la semana en que ocurrió el movimiento (en inglés) | `Monday` · `Tuesday` · `Wednesday` · `Thursday` · `Friday` · `Saturday` · `Sunday` |
| `es_internacional` | bool | Indica si el movimiento se realizó fuera de México | `True` · `False` |
| `dispositivo` | str | Dispositivo desde el que se realizó el movimiento (solo aplica a canales de app) | `app_ios` · `app_android` · `app_huawei` · *(nulo si el canal no es app)* |
| `patron_uso_atipico` | bool | Indica si el movimiento pertenece a una ventana de actividad inusual del usuario | `True` · `False` |

**Catálogo de tipos de operación (`tipo_operacion`)**

| Valor | Descripción |
|-------|-------------|
| `compra` | Pago en comercio físico o en línea |
| `transf_salida` | Transferencia enviada a otra cuenta (SPEI saliente) |
| `transf_entrada` | Transferencia recibida de otra cuenta (SPEI entrante) |
| `retiro_cajero` | Retiro de efectivo en cajero automático |
| `deposito_oxxo` | Depósito de efectivo realizado en tienda OXXO |
| `deposito_farmacia` | Depósito de efectivo realizado en farmacia |
| `pago_servicio` | Pago de servicio (luz, agua, teléfono, gobierno, etc.) |
| `pago_credito` | Pago a un producto de crédito del usuario |
| `abono_inversion` | Depósito de recursos al producto de inversión |
| `retiro_inversion` | Retiro de recursos del producto de inversión |
| `cargo_recurrente` | Cargo automático periódico (suscripciones, membresías digitales) |
| `cashback` | Devolución de cashback acumulado por compras |
| `devolucion` | Devolución de un cargo previo por disputa o cancelación |

**Catálogo de canales (`canal`)**

| Valor | Descripción |
|-------|-------------|
| `app_ios` | Aplicación móvil Hey Banco en dispositivo iOS |
| `app_android` | Aplicación móvil Hey Banco en dispositivo Android |
| `app_huawei` | Aplicación móvil Hey Banco en dispositivo Huawei |
| `cajero_banregio` | Cajero automático de la red Banregio |
| `cajero_externo` | Cajero automático de red externa |
| `pos_fisico` | Terminal punto de venta física (tarjeta presente) |
| `codi` | Pago mediante CoDi (Cobro Digital, plataforma SPEI móvil de Banxico) |
| `oxxo` | Depósito en tienda OXXO |
| `farmacia_ahorro` | Depósito en Farmacias del Ahorro |

---

*Hey Banco — Datathon 2026 · Datos 100% sintéticos*
