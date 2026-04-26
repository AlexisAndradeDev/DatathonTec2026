# Dashboard Havi Motor -- Guia de Usuario

> **Hey Banco · DatathonTec 2026**  
> Motor de Inteligencia & Atencion Personalizada  
> Pipeline: segmentacion no supervisada + chatbot RAG con streaming

---

## Indice

1. [Sidebar & Navegacion](#1-sidebar--navegacion)
2. [Home](#2-home)
3. [Segmentos](#3-segmentos)
4. [Customer 360](#4-customer-360)
5. [Havi Next (Chatbot)](#5-havi-next-chatbot)
6. [Analytics](#6-analytics)
7. [Pipeline de Datos](#7-pipeline-de-datos)
8. [Glosario](#8-glosario)

---

## 1. Sidebar & Navegacion

### Marca
En la parte superior del sidebar aparece el titulo **"Hey Banco"** con el subtitulo **"Havi Motor - Inteligencia & Atencion"**. Es la cabecera de marca del proyecto.

### Navegacion
Cinco paginas accesibles desde el sidebar:

| Pagina | Icono | Proposito |
|--------|-------|-----------|
| Home | `home` | Vista general con KPIs, treemap de segmentos, acceso rapido |
| Segmentos | `donut_small` | Visualizacion UMAP de clusters, perfiles de segmento, comparacion |
| Customer 360 | `person` | Ficha completa de un cliente: demografia, productos, DNA, transacciones |
| Havi Next | `forum` | Chatbot RAG con streaming, tool calling, asistencia personalizada |
| Analytics | `monitoring` | Heatmaps, Sankey, intenciones, adopcion de productos |

### Timestamp
Al fondo del sidebar aparece un indicador verde con la fecha y hora de la ultima ejecucion del pipeline de datos. Te dice que tan frescos estan los datos que estas viendo. Ejemplo: `Datos: 25/04/2026 22:50`.

---

## 2. Home

> **Que ves:** el panel principal de entrada. Resumen ejecutivo de todo el proyecto.

### 2.1 Hero Section
El banner superior con titulo **"Motor de Inteligencia & Atencion Personalizada"** y subtitulo contextual. Fondo oscuro, texto blanco. Te situa en el proposito del dashboard.

### 2.2 Metricas Clave (KPIs con Sparklines)

Ocho tarjetas distribuidas en dos filas de cuatro. Cada tarjeta incluye una mini-grafica de tendencia (sparkline) debajo del valor.

| KPI | Que mide | Fuente de datos | Como interpretarlo |
|-----|----------|-----------------|--------------------|
| **USUARIOS** | Total de clientes en la base | `clientes_clean.parquet` (15,025 registros) | Base sintetica completa de clientes Hey Banco |
| **SEGMENTOS** | Numero de clusters descubiertos | `segment_profiles.json` | 15 segmentos identificados por el algoritmo HDBSCAN. Un numero mayor indicaria granularidad mas fina |
| **SATISFACCION PROMEDIO** | Media de la columna `satisfaccion_1_10` | Campo en `clientes_clean` | Escala 1-10. Ej: 7.8/10 significa clientes generalmente satisfechos |
| **HEY PRO** | Porcentaje de usuarios con membresia premium | Campo `es_hey_pro` en clientes | Proporcion de la base que paga el servicio premium. Indicador de adopcion del producto estrella |
| **INTERACCIONES HAVI** | Total de mensajes en conversaciones | `havi_clean.parquet` (~50K registros) | Cada fila es un mensaje individual del chat. Mide volumen de uso del asistente virtual |
| **CONVERSACIONES** | Hilos de conversacion unicos | `conv_id` en havi (~24K hilos) | Varios mensajes forman una conversacion. Mide cuantas interacciones completas hubo |
| **VOLUMEN TOTAL TX** | Suma de todos los montos transaccionados | `monto` en `transacciones_clean` | Dinero total movido en la plataforma. Indicador de escala del negocio |
| **TICKET PROMEDIO** | Monto promedio por transaccion | `monto.mean()` en transacciones | Gasto tipico por operacion. Util para comparar segmentos |

**Nota sobre los sparklines:** las mini-lineas son indicativas de tendencia (se construyen con datos simulados proporcionales al valor final). Sirven como guia visual, no como serie historica real.

### 2.3 Distribucion de Segmentos (Treemap)

Un grafico de rectangulos anidados (treemap) donde:
- **Cada rectangulo** = un segmento de clientes
- **El tamano** es proporcional a la cantidad de usuarios en ese segmento
- **La etiqueta** muestra: nombre del segmento + cantidad + porcentaje

Ejemplo: `Adultos Alto Ingreso Pro Digitales (Alto Gasto) -- 3,179 (21.2%)` significa que ese segmento tiene 3,179 usuarios, representando el 21.2% de la base total.

Los segmentos mas grandes dominan visualmente. Sirve para identificar rapidamente que tipos de clientes son mayoria.

### 2.4 Insights Rapidos

Cuatro metricas complementarias en tarjetas con borde:

| Metrica | Que significa |
|---------|--------------|
| **% Transacciones no procesadas** | Proporcion de operaciones que fallaron. Alto = problemas tecnicos o de fondos |
| **Cashback total generado** | Dinero devuelto a clientes por recompensas. Indicador de costo del programa de lealtad |
| **Tasa de resolucion Havi** | % de conversaciones donde el chatbot resolvio la consulta. Métrica de efectividad del asistente |
| **% sentimiento negativo** | Proporcion de conversaciones con tono negativo detectado. Alerta temprana de insatisfaccion |

Si ves "N/A" o "no disponible" en resolucion/sentimiento, significa que los datos de intenciones no se generaron (el pipeline de intents.py usa solo un 5% de sample).

### 2.5 Seccion "Explorar"

Tres tarjetas de acceso rapido que redirigen a otras paginas del dashboard. Cada una tiene un boton para navegar directamente.

---

## 3. Segmentos

> **Que ves:** el mapa visual de todos los clientes agrupados por similitud, con capacidad de explorar cada grupo a detalle.

### 3.1 Visualizacion UMAP 2D

Un grafico de dispersion (scatter plot) donde:

- **Cada PUNTO** = un cliente individual (15,025 puntos)
- **Cada COLOR** = un segmento (cluster) asignado por HDBSCAN
- **Ejes X e Y** = coordenadas UMAP: el algoritmo toma las 3,209 caracteristicas de cada cliente y las reduce a 2 dimensiones preservando la estructura de similitud

**Como leerlo:**
- Puntos del mismo color CERCANOS entre si = clientes muy similares
- Grupos de colores SEPARADOS = segmentos claramente diferenciados
- Puntos dispersos o solitarios = clientes con comportamiento atipico (posible ruido)

**Limitacion:** el grafico no es clickeable directamente. Para explorar un cliente especifico, usa la pagina Customer 360.

#### Por que hay puntos de un cluster en areas de otro cluster

Esta es una de las preguntas mas frecuentes. La respuesta esta en como funciona el pipeline de clustering:

**El clustering NO se hace en el espacio 2D que ves en pantalla.** El UMAP 2D es exclusivamente para visualizacion. El proceso real es:

1. **La feature matrix tiene 3,209 columnas por cliente** (137 features estructuradas + 3,072 embeddings de conversaciones). Este es el espacio real de trabajo.

2. **UMAP reduce a 8 dimensiones** — el grid search probo 5, 8, 10 y 15 componentes. El mejor resultado se obtuvo con una de estas configuraciones. En esas 8 dimensiones es donde HDBSCAN hace el clustering real.

3. **UMAP 2D es una reduccion INDEPENDIENTE** — se ejecuta desde las 3,209 features originales directamente a 2 dimensiones. NO se hace desde las 8D del clustering. Es como tener dos mapas distintos del mismo territorio: ambos son validos pero muestran la informacion de manera diferente.

4. **Perdida de informacion** — comprimir 8 dimensiones en 2 implica perder aproximadamente el 75% de la estructura espacial. Puntos que en 8D estan perfectamente separados pueden colapsar visualmente en 2D. El color del cluster es la "verdad" (el resultado del clustering en 8D), la posicion en el plano 2D es una aproximacion.

5. **Reasignacion de ruido** — HDBSCAN inicialmente marca algunos puntos como ruido (cluster -1). Estos puntos se reasignan al centroide mas cercano si su distancia es menor al percentil 95 de las distancias intra-cluster. Algunos de estos puntos fronterizos pueden aparecer visualmente cerca de otros clusters.

**Analogia:** imagina 15 grupos de personas en un edificio de 8 pisos. Cada piso es una dimension. HDBSCAN agrupa correctamente en los 8 pisos. Despues, para hacer una foto, aplastas los 8 pisos en una hoja de papel 2D. En la hoja, personas del piso 3 pueden aparecer al lado de personas del piso 7, aunque en el edificio real esten separadas por 4 pisos. El color te dice la verdad, la posicion en el papel es la mejor aproximacion posible.

#### Como se determinaron los 15 clusters

El pipeline ejecuta un **grid search** con 16 combinaciones:

| Parametro | Valores probados |
|-----------|-----------------|
| `n_components` (UMAP) | 5, 8, 10, 15 |
| `min_cluster_size` (HDBSCAN) | 50, 100, 150, 200 |

Para cada combinacion:
- UMAP reduce la feature matrix a `n_components` dimensiones
- HDBSCAN agrupa en ese espacio (con `min_samples=1`, `cluster_selection_epsilon=0.5`)
- Se calcula un score compuesto: **Silhouette + 0.001 × n_clusters - 0.0001 × proporcion_ruido**

Gana la combinacion con mayor score. El resultado optimo fue **15 clusters con Silhouette = 0.77**, lo que indica una muy buena separacion entre segmentos. Un Silhouette cercano a 1.0 significa clusters compactos y bien diferenciados; 0.77 esta en el rango alto.

### 3.2 Perfil de Segmento (Panel Derecho)

El selector muestra todos los segmentos ordenados de mayor a menor tamano. Al seleccionar uno ves:

1. **Nombre del segmento** -- generado automaticamente con reglas: grupo etario + nivel de ingreso + perfil + discriminador top. Ej: "Jovenes Ingreso Medio Pro Digitales (Bajo Gasto)"

2. **Estadisticas del segmento** (8 metricas en 2 columnas):

| Metrica | Descripcion |
|---------|-------------|
| Tamano | Cantidad de usuarios + % del total |
| Edad promedio | Media de edad en el segmento |
| Ingreso promedio | Media de `ingreso_mensual_mxn` en MXN |
| Hey Pro | % de miembros con membresia premium |
| Score Buro | Promedio de `score_buro_interno` (rango tipico 300-850) |
| Satisfaccion | Promedio de `satisfaccion_1_10` |
| Antiguedad | Dias promedio desde registro |
| Conversaciones | Promedio de conversaciones Havi por usuario |

3. **Descripcion** -- texto generado que resume el perfil demografico y financiero del segmento.

4. **Necesidades implicitas** -- lista de oportunidades detectadas. Ej: "Acceso a credito", "Potencial de inversion", "Seguimiento por baja satisfaccion".

5. **Accion proactiva** -- sugerencia concreta de que hacer con este segmento. Ej: "Ofrecer tarjeta de credito con 0% interes 6 meses".

6. **Top features discriminantes** -- grafico de barras mostrando las 8 caracteristicas que mas diferencian a este segmento del promedio de la poblacion. Usa |Z-score|:
   - Z-score alto (ej: 8.5) = el segmento se desvia mucho del promedio en esa caracteristica
   - "mayor" = el segmento esta por encima del promedio
   - "menor" = el segmento esta por debajo del promedio

### 3.3 Comparacion entre Segmentos

El checkbox **"Comparar con otro"** despliega un selector y el perfil completo del segundo segmento debajo del primero. Util para contrastar dos grupos (ej: "Pro Digitales" vs "Tradicionales").

> **Nota:** para explorar usuarios individuales de un segmento, usa la pagina **Customer 360** — ahi podes buscar cualquier USR-XXXXX y ver su ficha completa.

**Datos que consume esta pagina:**
- `data/processed/user_segments.parquet` -- asignacion cluster + coordenadas UMAP por usuario
- `data/processed/segment_profiles.json` -- metadata de cada segmento (nombre, stats, descripcion, top features)

---

## 4. Customer 360

> **Que ves:** la ficha completa de un cliente individual. Es la vista mas detallada del dashboard.

### 4.1 Selector de Usuario

Dropdown con todos los clientes en formato `USR-XXXXX`. Si llegaste desde Segmentos, el usuario ya viene pre-seleccionado.

### 4.2 Hero Header

La franja superior de la pagina contiene:

| Elemento | Que muestra |
|----------|-------------|
| **Avatar** | Circulo con 2 iniciales derivadas del user_id. Gradiente oscuro, texto blanco |
| **User ID** | Identificador del cliente en grande |
| **Badges** | Etiquetas contextuales que aparecen SOLO si aplican: `Hey Pro` (verde), `Nomina`, `Remesas`, `Atipico` (rojo), y el nombre del segmento al que pertenece (azul) |
| **Gauge de Salud Financiera** | Score 0-100 en un medidor semicircular |

#### Como se calcula el Score de Salud Financiera

El score parte de 50 puntos y se ajusta con:

| Factor | Ajuste | Razon |
|--------|--------|-------|
| Es Hey Pro | +8 | Indica compromiso financiero y acceso a beneficios |
| Tiene seguro | +6 | Senal de planificacion financiera |
| Score Buro | +(score-500)/25 | Mejor historial crediticio = mejor salud |
| Satisfaccion | +(sat-5)*3 | Clientes satisfechos tienden a mejor salud financiera |
| Ingreso mensual | +min((ingreso-15000)/1000, 15) | Mayor ingreso = mayor capacidad, max +15 |
| Patron atipico | -8 | Comportamiento irregular = riesgo |

**Interpretacion del color:**
- Verde (≥70): salud financiera buena
- Amarillo (40-69): salud financiera regular
- Rojo (<40): salud financiera debil, requiere atencion

**Boton "Chat con Havi"** -- navega al chatbot con este cliente pre-seleccionado.

### 4.3 Fila 1: Demografia + Productos

**Demographic Card (izquierda):**

Ocho campos extraidos directamente de `clientes_clean.parquet`:

| Campo | Columna original | Ejemplo |
|-------|-----------------|---------|
| Edad | `edad` | 34 |
| Genero | `sexo` | M |
| Estado | `estado` | DF |
| Ciudad | `ciudad` | -- |
| Ocupacion | `ocupacion` | Empleado |
| Educacion | `nivel_educativo` | Licenciatura |
| Ingreso | `ingreso_mensual_mxn` | $25,000/mes |
| Idioma | `idioma_preferido` | es_MX |

**Productos activos (derecha):**

Cards individuales por cada producto financiero del cliente. Cada card muestra:

| Dato | Significado |
|------|-------------|
| **Icono (C/D/I/N)** | C=Credito, D=Debito, I=Inversion, N=Nomina |
| **Tipo de producto** | Ej: "Tarjeta De Credito" |
| **Saldo** | Balance actual en MXN |
| **Limite** | Limite de credito (solo aplica en TDC) |
| **Tasa** | Tasa de interes (solo aplica en creditos) |
| **Estatus** | `activa` (teal) o `inactiva` (gris) |
| **Uso %** | Porcentaje de utilizacion del limite (solo TDC) |

### 4.4 Fila 2: DNA + Radar

**Customer DNA (izquierda):**

Narrativa generada por `src/enrichment/customer_dna.py` usando un template Python (sin LLM, costo $0). Es un texto de 6 parrafos que cubre:

1. **Perfil demografico** -- edad, ubicacion, ocupacion, nivel educativo
2. **Relacion con el banco** -- antiguedad, nivel de satisfaccion, score buro
3. **Productos financieros** -- que tiene contratado, saldos, utilizacion
4. **Patrones de gasto** -- categorias principales, frecuencia, montos
5. **Conversaciones con Havi** -- temas frecuentes, canal preferido, tasa de resolucion
6. **Necesidades y oportunidades** -- recomendaciones personalizadas, alertas

**Condicion:** el DNA solo se genera para usuarios con 2 o mas conversaciones en Havi. Si el cliente tiene menos, veras un mensaje "Customer DNA no disponible".

**Radar: Usuario vs Segmento (derecha):**

Grafico de radar (spider chart) con 5 ejes que comparan al cliente contra el promedio de su segmento:

| Eje | Columna en feature_matrix | Que representa |
|-----|---------------------------|----------------|
| Hey Pro | `es_hey_pro` | 1 si es premium, 0 si no |
| Seguro | `tiene_seguro` | 1 si tiene seguro, 0 si no |
| Intl | `pct_internacional` | % de transacciones internacionales |
| No Proc. | `pct_no_procesada` | % de transacciones rechazadas |
| Voz | `pct_voz` | % de conversaciones por canal voz vs texto |

Todos los valores estan normalizados 0-1 para ser comparables. Si el area azul (usuario) es mayor que el area teal (segmento), el cliente esta por encima del promedio de su grupo en esas dimensiones.

**Accion proactiva:** recuadro info con la sugerencia del segmento. Ej: "Que haria Havi? Ofrecer tarjeta de credito con 0% interes 6 meses".

### 4.5 Fila 3: Actividad Reciente

**Ultimas transacciones (izquierda):**

Tabla con las 10 transacciones mas recientes del cliente:

| Columna | Origen | Ejemplo |
|---------|--------|---------|
| `fecha_hora` | `fecha_hora` en transacciones | 2026-04-25 14:32:00 |
| `tipo_operacion` | `tipo_operacion` | compra, retiro, transferencia |
| `monto` | `monto` en MXN | $1,250 |
| `categoria_mcc` | `categoria_mcc` | restaurantes, supermercados |
| `estatus` | `estatus` | procesada, no_procesada |

**Donut de gasto por categoria (derecha):**

Grafico de dona con el top 7 de categorias donde el cliente mas gasta. Los valores son montos absolutos (suma de `monto` agrupado por `categoria_mcc`). Sirve para entender rapidamente en que gasta su dinero este cliente.

---

## 5. Havi Next (Chatbot)

> **Que ves:** el asistente virtual conversacional. Podes chatear con Havi como si fueras el cliente seleccionado.

### 5.1 Selector de Cliente

Igual que en Customer 360. Si navegaste desde ahi, el cliente ya esta pre-seleccionado.

**Importante:** al cambiar de cliente, el historial de chat se borra automaticamente. Cada cliente tiene su propia conversacion independiente.

### 5.2 Chips de Accion Rapida

Cuatro botones arriba del input de chat que disparan preguntas predefinidas:

| Boton | Prompt enviado | Herramienta ejecutada |
|-------|---------------|----------------------|
| **Ver saldo** | "Cual es el saldo de mis cuentas y productos?" | `get_account_summary(user_id)` |
| **Ultimos gastos** | "Muestrame mis ultimas transacciones" | `get_recent_transactions(user_id, n=5)` |
| **Mi recomendacion** | "Que recomendacion tienes para mi?" | `get_recommendation(user_id)` |
| **Sobre mi segmento** | "Pertenezco al segmento 'X', que significa eso para mis finanzas?" | Ninguna (pregunta abierta al LLM) |

El cuarto chip solo aparece si el cliente tiene segmento asignado.

### 5.3 Area de Chat

- **Burbuja del usuario** (derecha): fondo negro, texto blanco. Muestra lo que vos escribiste.
- **Burbuja de Havi** (izquierda): fondo blanco, borde gris, texto negro. Muestra la respuesta del asistente.
- **Typing indicator**: cuando Havi esta generando la respuesta, ves tres puntos animados (rebotando). Desaparecen cuando empieza a llegar texto.

### 5.4 Streaming

Las respuestas de Havi aparecen en tiempo real, palabra por palabra, usando `st.write_stream()`. Esto significa que no tenes que esperar a que se genere toda la respuesta para empezar a leer.

### 5.5 Tool Calls (Herramientas)

Cuando Havi necesita datos concretos (saldos, transacciones), invoca herramientas automaticamente. Estas llamadas se muestran como **expanders colapsables** debajo de cada mensaje, con:

- **Parametros** (JSON) -- que le pidio Havi a la herramienta
- **Resultado** (JSON) -- que devolvio la herramienta

Las 3 herramientas disponibles son:

| Herramienta | Que hace | Datos que devuelve |
|-------------|----------|-------------------|
| `get_account_summary` | Resumen de cuentas | Productos, saldos, limites, deudas, cashback, Hey Pro |
| `get_recent_transactions` | Ultimas transacciones | Fecha, monto, comercio, categoria, estatus + alerta atipico |
| `get_recommendation` | Recomendacion personalizada | Texto con sugerencia basada en el segmento del cliente |

### 5.6 Sistema (System Prompt)

Cada conversacion incluye un prompt de sistema invisible que define la personalidad de Havi:

- **Contexto:** DNA del cliente (si disponible) como `[PERFIL DEL CLIENTE USR-XXXXX]`
- **Personalidad:** empatica, proactiva, experta en finanzas personales
- **Tono:** calido y profesional, usa "tu" en espanol mexicano
- **Limite:** respuestas concisas (maximo 2 parrafos), no inventa informacion
- **Herramientas:** acceso a las 3 funciones para datos concretos

### 5.7 Modelo y Costo

- **Modelo:** DeepSeek-V3.2 via Azure AI Foundry (serverless)
- **Streaming:** habilitado, respuesta progresiva
- **Costo estimado:** ~$0.50-$1.00 por sesion de chat (dentro del presupuesto de $20 USD)

---

## 6. Analytics

> **Que ves:** visualizaciones avanzadas para analisis de datos agregados. Dividido en 3 pestanas.

### 6.1 Metricas Superiores

Cuatro KPIs en la parte superior que resumen los datos cargados:

| Metrica | Fuente |
|---------|--------|
| Transacciones | Conteo de filas en `transacciones_clean` |
| Volumen Total | Suma de `monto` en transacciones |
| Interacciones Havi | Conteo de filas en `havi_clean` |
| % Canal Voz | Proporcion de mensajes con `channel_source=2` (voz) |

### 6.2 Tab 1: Actividad Transaccional

#### Heatmap Hora x Dia

Mapa de calor donde:
- **Eje X:** horas del dia (0-23)
- **Eje Y:** dias de la semana (Lun-Dom)
- **Color:** blanco (bajo) a negro (alto) = monto promedio transaccionado

**Como leerlo:**
- Zonas oscuras = horarios de alta actividad transaccional
- Zonas claras = baja actividad (ej: madrugada)
- Compara dias habiles (Lun-Vie) vs fin de semana (Sab-Dom) para ver patrones de consumo

#### Sankey: Categoria -> Operacion -> Estatus

Diagrama de flujo donde:
- **Columna izquierda:** categorias MCC (restaurantes, supermercados, etc.)
- **Columna central:** tipo de operacion (compra, retiro, transferencia...)
- **Columna derecha:** estatus (procesada, no_procesada)
- **Ancho de las bandas:** proporcional a la cantidad de transacciones

Muestra los 50 flujos mas frecuentes. Sirve para entender como se mueve el dinero: que categorias generan que tipos de operacion y cual es la tasa de exito.

### 6.3 Tab 2: Conversaciones

#### Sunburst de Intenciones

Grafico solar (anillos concentricos) con la distribucion de intenciones extraidas por `intents.py`. Cada seccion representa una intencion detectada (ej: `consulta_saldo`, `queja`, `solicitud_producto`).

**Dato importante:** estas intenciones vienen de un 5% de sample de las conversaciones (el pipeline de intenciones usa `sample_pct=0.05` por control de presupuesto). Si no se ejecuto, veras "Datos de intenciones no disponibles".

#### Canales de Conversacion

Tabla simple con la distribucion de mensajes por canal:

| Canal | Interpretacion |
|-------|---------------|
| Texto | `channel_source=1` -- chat escrito |
| Voz | `channel_source=2` -- mensajes de voz |

Acompanado del % de canal voz como metrica.

#### Sentimiento

Tres tarjetas con el conteo de conversaciones por sentimiento detectado (positivo, negativo, neutral). El sentimiento lo extrae el LLM en `intents.py`. Un % alto de negativo puede indicar problemas con el servicio.

### 6.4 Tab 3: Adopcion de Productos

Tabla con la cantidad de usuarios por tipo de producto (tarjeta de credito, debito, cuenta de inversion, nomina, etc.). Ordenada de mayor a menor adopcion.

Tres metricas complementarias:

| Metrica | Que indica |
|---------|-----------|
| Usuarios Hey Pro | Cuantos clientes pagan la membresia premium y que % representan |
| Usuarios con Seguro | Cuantos tienen seguro contratado |
| Patron Atipico | Cuantos clientes tienen `patron_uso_atipico=1` (comportamiento irregular detectado) |

---

## 7. Pipeline de Datos

> **Como se generan los datos que alimentan el dashboard.**

### 7.1 Flujo de Procesamiento

```
data/raw/
  ├── hey_clientes.csv           (15,025 clientes)
  ├── hey_productos.csv          (productos financieros)
  ├── hey_transacciones.csv      (transacciones)
  └── dataset_50k_anonymized.parquet  (conversaciones Havi, ~50K)
          │
          ▼  make validate
          │  Valida schemas, tipos de datos, FK integrity
          │
          ▼  make ingest
          │  Limpia fechas, elimina columnas sinteticas, guarda Parquet
          │
data/processed/
  ├── clientes_clean.parquet
  ├── productos_clean.parquet
  ├── transacciones_clean.parquet
  └── havi_clean.parquet
          │
          ▼  make enrich  (3 etapas)
          │
          ├─1. embeddings.py     → user_embeddings.parquet
          │   Modelo: text-embedding-3-large (Azure OpenAI)
          │   Dimensiones: 3072 por usuario
          │   Metodo: mean-pool de embeddings de conversaciones
          │   Costo: ~$1.30 USD (full) / ~$0.08 (5% sample)
          │
          ├─2. intents.py        → user_intents.parquet, conv_intents.parquet
          │   Modelo: DeepSeek-V3.2 (Azure AI Foundry)
          │   Extrae: intencion, sentimiento, urgencia, resolucion
          │   Por defecto: sample_pct=0.05 (5%)
          │   Costo: ~$3.60 USD (full) / ~$0.18 (5% sample)
          │
          └─3. customer_dna.py   → customer_dna.parquet
             Metodo: template Python (sin LLM)
             Requisito: usuario con ≥2 conversaciones
             Genera: narrativa de 6 parrafos por cliente
             Costo: $0.00
          │
          ▼  make features
          │  Construye feature matrix: 15,025 usuarios × 3,209 columnas
          │  137 features estructuradas (demografia, productos, tx, havi, intents)
          │  + 3,072 embeddings
          │  Guarda: feature_matrix.parquet + SQLite (sin embeddings, limite 2000 cols)
          │
          ▼  make cluster
          │
          ├─1. cluster.py        → user_segments.parquet
          │   UMAP: reduce 3,209 dims → 8 dims, luego → 2 dims (visualizacion)
          │   HDBSCAN: grid search sobre n_components × min_cluster_size
          │   Score: Silhouette + cluster bonus - noise penalty
          │   Mejor config: 15 clusters, Silhouette=0.77
          │   Total: 106 segundos de computo
          │
          └─2. segments.py       → segment_profiles.json
             Metodo: template Python (sin LLM)
             Genera: nombre, descripcion, necesidades, accion, top features
             Reglas: grupo etario + nivel ingreso + perfil + discriminadores
             Costo: $0.00
          │
          ▼  make dashboard
          │  Streamlit lee data/processed/ directamente
          │  Caché: st.cache_data con TTL de 1 hora
          │
```

### 7.2 Comandos del Makefile

| Comando | Que ejecuta |
|---------|-------------|
| `make validate` | Validacion de schemas |
| `make ingest` | Limpieza y carga inicial |
| `make enrich` | Las 3 etapas LLM (embeddings, intents, dna) |
| `make features` | Construccion de feature matrix |
| `make cluster` | UMAP + HDBSCAN + segment labeling |
| `make dashboard` | Inicia Streamlit en `src/dashboard/app.py` |
| `make all` | `validate` + `enrich` + `features` + `cluster` |
| `make clean` | Borra `data/processed/*` y `data/*.db` |

### 7.3 Datasets Originales

| Dataset | Filas | Columnas | Contenido |
|---------|-------|----------|-----------|
| `hey_clientes.csv` | 15,025 | 22 | Datos demograficos, financieros, de engagement |
| `hey_productos.csv` | variable | 15 | Productos contratados (1:N con clientes) |
| `hey_transacciones.csv` | variable | 17 | Transacciones financieras (N:1 con clientes) |
| `dataset_50k_anonymized.parquet` | 49,999 | 6 | Conversaciones Havi: input, output, date, conv_id, user_id, channel |

### 7.4 15 Segmentos

Los segmentos son generados por `segments.py` usando reglas de Python (sin LLM). El nombre sigue el patron:

```
{Grupo Etario} {Nivel Ingreso} {Perfil Digital} ({Discriminador Top})
```

Ejemplos reales de los datos procesados:

- "Adultos Alto Ingreso Pro Digitales (Alto Gasto)" -- 3,179 usuarios (21.2%)
- "Jovenes Ingreso Medio Pro Digitales (Bajo Gasto)" -- 1,318 usuarios (8.8%)
- "Adultos Ingreso Medio Digitales" -- segmento intermedio tipico

Cada segmento incluye en `segment_profiles.json`:
- **estadisticas**: edad, ingreso, hey_pro_pct, score_buro, satisfaccion, antiguedad, conversaciones promedio
- **top_features**: 8 caracteristicas con mayor z-score vs poblacion
- **necesidades**: lista de oportunidades detectadas
- **accion_proactiva**: sugerencia concreta de negocio

---

## 8. Glosario

| Termino | Significado |
|---------|-------------|
| **Havi** | Asistente virtual de Hey Banco (el chatbot) |
| **Hey Pro** | Membresia premium de Hey Banco |
| **UMAP** | Uniform Manifold Approximation and Projection -- algoritmo de reduccion de dimensionalidad |
| **HDBSCAN** | Hierarchical Density-Based Spatial Clustering -- algoritmo de clustering no supervisado |
| **Z-score** | Cuantas desviaciones estandar se aleja un valor del promedio. Z>2 = significativamente diferente |
| **Silhouette Score** | Metrica de calidad de clustering. Rango -1 a 1. 0.77 = buena separacion entre segmentos |
| **MCC** | Merchant Category Code -- codigo que clasifica el tipo de comercio |
| **RAG** | Retrieval-Augmented Generation -- el chatbot combina busqueda de datos + generacion de texto |
| **Tool Calling** | Capacidad del LLM de invocar funciones externas para obtener datos |
| **DNA** | Perfil narrativo completo del cliente generado por template |
| **Feature Matrix** | Matriz de caracteristicas: una fila por usuario, columnas con atributos numericos |
| **Embedding** | Vector numerico que representa semanticamente un texto (3072 dimensiones) |
| **Parquet** | Formato de archivo columnar eficiente para analytics |
| **Snappy** | Algoritmo de compresion usado en los archivos Parquet |
