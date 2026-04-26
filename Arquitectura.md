# Arquitectura End-to-End — Motor de Inteligencia & Atención Personalizada

> **DatathonTec 2026 — Hey Banco**
> Pipeline de IA que integra logs conversacionales + registros transaccionales para segmentación no supervisada y atención personalizada con chatbot RAG + streaming.

---

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Data Layer](#2-data-layer)
3. [Feature Enrichment (LLM)](#3-feature-enrichment-layer)
4. [Unsupervised Learning](#4-unsupervised-learning-layer)
5. [Chatbot Agent (RAG + Streaming)](#5-chatbot-agent-layer)
6. [Streamlit Dashboard](#6-streamlit-dashboard)
7. [Infraestructura & DevOps](#7-infraestructura--devops)
8. [Estructura del Repositorio](#8-estructura-del-repositorio)
9. [Plan de Implementación](#9-plan-de-implementación)
10. [Estimación de Costos](#10-estimación-de-costos-azure-ai-foundry)
11. [Alineación con Rúbrica](#11-alineación-con-rúbrica-de-evaluación)
12. [Decisiones de Arquitectura](#12-decisiones-de-arquitectura)

---

## 1. Visión General

### Diagrama de Alto Nivel

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               DATA LAYER                                      │
│                                                                               │
│  hey_clientes.csv         hey_productos.csv         hey_transacciones.csv     │
│  (15K usuarios)           (1:N por usuario)         (historial de movimientos) │
│                                                                               │
│               dataset_50k_anonymized.parquet                                  │
│               (24K conversaciones · 50K interacciones)                        │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   FEATURE ENRICHMENT           │
                    │   Azure AI Foundry + Python     │
                    │                                  │
                    │  ① Embeddings Conversacionales   │
                    │     (text-embedding-3-large)     │
                    │  ② Extraccion de Intenciones     │
                    │     (DeepSeek-V3.2)              │
                    │  ③ [STUB] Normalizacion Desc.    │
                    │  ④ Customer DNA (template, $0)   │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   UNSUPERVISED LEARNING          │
                    │                                  │
                    │  Feature Matrix (15K x ~3,200)   │
                    │  StandardScaler + KNN Imputer    │
                    │  UMAP (n_components=8)           │
                    │  HDBSCAN (min_cluster=100)       │
                    │  Segment Labeling (reglas, $0)   │
                    └───────────────┬────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
┌──────────▼──────────┐  ┌─────────▼─────────┐  ┌──────────▼──────────┐
│   STREAMLIT APP     │  │   DATA STORE      │  │   CHATBOT AGENT     │
│                     │  │                   │  │                      │
│ • Home / KPIs       │  │ • SQLite (consulta│  │ • Tool Calling (3)  │
│ • Segment Explorer  │  │   rapida)         │  │ • Customer DNA como │
│ • Customer 360      │  │ • Parquet (ETL)   │  │   system prompt     │
│ • Havi Next (Chat)  │  │ • JSON (perfiles) │  │ • Streaming via     │
│ • Analytics         │  │   segment_profiles│  │   st.write_stream() │
└─────────────────────┘  └───────────────────┘  └─────────────────────┘
```

### Flujo End-to-End

```
Ingesta → Validacion → Enrichment (LLM + template) → Feature Engineering
→ Clustering No Supervisado → Perfilamiento de Segmentos
→ Dashboard Streamlit + Chatbot con Tool Calling + Streaming
```

### Principios de Diseño

| Principio                                  | Implementación                                                                             |
| ------------------------------------------ | ------------------------------------------------------------------------------------------ |
| **Sandbox sin restricciones regulatorias** | Datos 100% sintéticos. Sin compliance de CNBV/LFPDPPP. Libertad para APIs externas.        |
| **Cloud**                                  | Azure for Students. Servicios: Azure AI Foundry (DeepSeek-V3.2) + Azure OpenAI (text-embedding-3-large). |
| **Presupuesto**                            | $20 USD máximo para APIs de IA.                                                            |
| **Lenguaje**                               | Python 3.11+                                                                               |
| **Modularidad**                            | Cada etapa es un script independiente con entrada/salida clara para migrar a orquestación. |
| **Seguridad**                              | Keys en `.env`. `.gitignore` cubre datos y secretos. Ejecución 100% local.                 |

---

## 2. Data Layer

### 2.1 Datasets

| Dataset                          | Formato | Rows              | Clave Primaria    | FK                         |
| -------------------------------- | ------- | ----------------- | ----------------- | -------------------------- |
| `hey_clientes.csv`               | CSV     | ~15K usuarios     | `user_id`         | —                          |
| `hey_productos.csv`              | CSV     | 1:N por usuario   | `producto_id`     | `user_id` → `hey_clientes` |
| `hey_transacciones.csv`          | CSV     | alta cardinalidad | `transaccion_id`  | `user_id`, `producto_id`   |
| `dataset_50k_anonymized.parquet` | Parquet | 50K interacciones | `conv_id` + orden | `user_id` → `hey_clientes` |

### 2.2 Relaciones

```
hey_clientes.csv
    └── user_id ──┬──► hey_productos.csv       (user_id)
                   ├──► hey_transacciones.csv   (user_id)
                   └──► dataset_50k_anonymized  (user_id) [15,025 usuarios]

hey_productos.csv
    └── producto_id ──► hey_transacciones.csv   (producto_id)
```

> **Nota importante**: Los 15,025 usuarios de conversaciones están contenidos en el dataset transaccional. Existe relación por `user_id` con el mismo formato `USR-XXXXX`. El análisis puede ser 360° (cliente completo).

### 2.3 Estrategia de Almacenamiento

| Entorno           | Formato                                | Justificación                                                     |
| ----------------- | -------------------------------------- | ----------------------------------------------------------------- |
| **Raw**           | CSV / Parquet original                 | Inmutables, en `data/raw/`                                        |
| **Processed**     | Parquet comprimido (snappy)            | Intermedios enriquecidos, `data/processed/`                       |
| **In-Memory**     | Polars DataFrame (>100K rows) / Pandas | Procesamiento vectorizado                                         |
| **Feature Store** | SQLite (`data/features.db`)            | Feature matrix + segmentos para consultas rápidas desde Streamlit |

### 2.4 Validación de Datos (`src/data/validate.py`)

```python
# Checks implementados en validate.py:
# check_1_2: Schema — columnas esperadas, tipos correctos para los 4 datasets
# check_1_3: Nulls esperados — limite_credito/utilizacion_pct nulos para no-credito,
#            plazo_meses/monto_mensualidad nulos para no-prestamo,
#            motivo_no_procesada solo cuando estatus='no_procesada'
# check_1_7: Encoding — M/H/SE, estados validos de Mexico, fechas ISO,
#            dia_semana en ingles, idioma es_MX/en_US
# check_1_8: Cross-reference — user_id de Havi vs. datasets transaccionales
#            (interseccion, usuarios Havi sin match, usuarios transaccionales sin Havi)
```

---

## 3. Feature Enrichment Layer

> **Modelo chat**: DeepSeek-V3.2 via Azure AI Foundry (serverless endpoint, OpenAI-compatible).
> **Modelo embeddings**: text-embedding-3-large via Azure OpenAI.
> **Modo**: Batch sincrono con rate limiting (60 RPM). JSON Mode para intenciones. Template Python para Customer DNA ($0). STUB para descripciones.

### 3.1 Embeddings Conversacionales (`src/enrichment/embeddings.py`)

**Objetivo**: Vectorizar la semántica de lo que cada usuario pregunta a Havi.

| Parámetro                  | Valor                                                                 |
| -------------------------- | --------------------------------------------------------------------- |
| **Modelo** | `text-embedding-3-large` (via Azure OpenAI) |
| **Dimensionalidad** | 3072 |
| **Entrada** | Campo `input` de cada interaccion (mensaje del usuario) |
| **Preprocesamiento** | Concatenar mensajes del usuario por conversacion en orden cronologico |
| **Agregacion por usuario** | Mean-pooling → vector de 3072 dimensiones |
| **Batch size** | 500 textos por llamada |
| **Estimacion tokens** | ~10M tokens totales |
| **Costo estimado** | ~$0.20 USD |

**Output**: `data/processed/user_embeddings.parquet` — un vector de 3072 dimensiones por `user_id`.

### 3.2 Extracción Estructurada de Intenciones (`src/enrichment/intents.py`)

**Objetivo**: Clasificar cada conversación por intención, sentimiento y urgencia usando LLM.

**Prompt estructurado (JSON mode)**:

```json
{
  "intent": "consulta_saldo|reclamo_comision|solicitud_credito|bloqueo_tarjeta|info_producto|soporte_tecnico|cancelacion|transferencia|queja|aclaracion|otro",
  "sentiment": "positivo|neutral|negativo",
  "urgency": "baja|media|alta",
  "resolution": "resuelto|no_resuelto|escalado",
  "summary": "Resumen de 1 oración de la conversación"
}
```

| Parámetro             | Valor                                                      |
| --------------------- | ---------------------------------------------------------- |
| **Agrupación**        | Por `conv_id`, mensajes ordenados cronológicamente         |
| **Batch**             | 50 conversaciones por llamada (optimiza tokens y latencia) |
| **Estimación tokens** | ~12M in / ~3M out                                          |
| **Costo estimado**    | $6.54 USD (100% conversaciones). Menor si se usa `sample_pct` (default 5% en dev). |

**Agregacion por usuario**:

- Conteo por tipo de intencion (11 columnas)
- Urgencia promedio (`urgency_avg`)
- Tasa de resolucion (`resolution_rate`)
- Proporcion de sentimiento negativo (`pct_negativo`)

**Output**: `data/processed/user_intents.parquet` + `data/processed/conv_intents.parquet`.

### 3.3 Normalizacion de Descripciones (`src/enrichment/descriptions.py`)

> **ESTADO: STUB — No implementado.** El archivo contiene solo la firma de funcion `run_descriptions()` con cuerpo `pass`. Se deja como punto de extension futura.

**Objetivo**: Extraer informacion estructurada del campo `descripcion_libre` en transacciones (texto libre no estandarizado).

**Plan original (no ejecutado)**:

| Parametro             | Valor                                                        |
| --------------------- | ------------------------------------------------------------ |
| **Entrada**           | `descripcion_libre` de `hey_transacciones` donde no sea nulo |
| **Batch**             | 100 descripciones por llamada                                |
| **Estimacion tokens** | ~5M in / ~2M out                                             |
| **Costo estimado**    | $2.00 USD (LLM) o $0 (reglas regex como fallback)            |

**Output esperado**: `data/processed/tx_enriched.parquet`. Actualmente no se genera.


### 3.4 Customer DNA Narrativo (`src/enrichment/customer_dna.py`)

> **ESTADO: Implementado con template deterministico (Python, sin LLM).** Costo real: $0.00 USD. Tiempo de ejecucion: <1 segundo para ~5,600 usuarios.

**Objetivo**: Generar un perfil narrativo de ~150 palabras por usuario que describa necesidades implicitas, comportamiento financiero y oportunidades de atencion proactiva.

**Metodo**: Template deterministico en Python (`_build_dna()`) que construye 6 parrafos:
1. **Demografia**: edad, genero, ubicacion, ocupacion, ingreso, educacion
2. **Relacion bancaria**: Hey Pro, nomina, remesas, seguros, Hey Shop, score buro, satisfaccion, antiguedad, ultimo login, canal preferido
3. **Productos activos**: lista con saldos
4. **Patrones de gasto**: top 3 categorias, conteo de transacciones
5. **Interacciones Havi**: conteo de conversaciones, desglose texto/voz
6. **Necesidades implicitas y oportunidades proactivas** (logica condicional):
   - Buen score + sin TC + Hey Pro → ofrecer Tarjeta de Credito Hey
   - Saldo debito alto + sin inversion → sugerir Inversion Hey
   - Sin seguro + Hey Pro → recomendar seguro
   - Patron atipico → revisar actividad
   - Ultimo login > 30 dias → campana de reactivacion
   - Satisfaccion <= 5 → llamada de seguimiento
   - No usa Hey Shop + Hey Pro → invitar a Hey Shop

| Parametro             | Valor                                              |
| --------------------- | -------------------------------------------------- |
| **Entrada**           | Datos agregados por usuario (clientes, productos, transacciones, Havi) |
| **Filtro**            | Usuarios con >= `min_convs` conversaciones (default: 1) |
| **Costo**             | **$0.00 USD** (template deterministico, sin llamadas a LLM) |

**Output**: `data/processed/customer_dna.parquet` (`user_id`, `dna_text`, `accion_proactiva`).

### 3.5 Optimizaciones de Costo y Rendimiento

| Estrategia            | Detalle                                                                         |
| --------------------- | ------------------------------------------------------------------------------- |
| **Cache**             | Embeddings cacheados por texto. Si un input ya fue procesado, no se re-consume. |
| **Rate Limiting**     | 60 RPM (Azure OpenAI Student tier). Control sincrono con `time.sleep`.          |
| **Retry con backoff** | 3 reintentos con exponential backoff (1s, 2s, 4s) para rate limits.             |
| **Batching**          | Agrupar textos para minimizar llamadas (500 por batch en embeddings, 50 convs en intenciones). |
| **JSON Mode**         | Structured output en lugar de parseo libre. Reduce tokens de salida y errores.  |

---

## 4. Unsupervised Learning Layer

### 4.1 Feature Matrix Final (~3,209 columnas)

| Grupo                  | Features                                                                                                                                                                                                                                                                                                           | Cardinalidad | Origen              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | ------------------- |
| **Demograficas**       | edad, genero (one-hot), estado (one-hot), nivel_educativo (ordinal), ocupacion (one-hot), ingreso_mensual_mxn, idioma_preferido                                                                                                                                                                                    | ~40          | `hey_clientes`      |
| **Engagement**         | antiguedad_dias, dias_desde_ultimo_login, preferencia_canal (one-hot), satisfaccion_1_10, es_hey_pro, nomina_domiciliada, recibe_remesas, usa_hey_shop                                                                                                                                                             | ~10          | `hey_clientes`      |
| **Credito**            | score_buro, tiene_seguro, patron_uso_atipico                                                                                                                                                                                                                                                                       | 3            | `hey_clientes`      |
| **Productos**          | tipo_producto (one-hot 11), utilizacion_pct_avg, saldo_actual_total, tasa_interes_promedio, plazo_meses_promedio, monto_mensualidad_total                                                                                                                                                                          | ~20          | `hey_productos`     |
| **Transaccionales**    | frecuencia_total, frecuencia_por_categoria_mcc (one-hot 13), frecuencia_por_canal (one-hot 9), frecuencia_por_tipo_operacion (one-hot 12), monto_promedio, monto_total, hora_pico, dia_semana (one-hot 7), pct_internacional, cashback_total, intentos_promedio, pct_no_procesada, motivo_no_procesada (one-hot 8) | ~55          | `hey_transacciones` |
| **Conversacionales**   | num_conversaciones, msgs_promedio, pct_voz, diversidad_intents                                                                                                                                                                                                                                                     | 4            | Dataset Havi        |
| **Embeddings (Havi)**  | Mean-pooled vector                                                                                                                                                                                                                                                                                                 | 3072         | §3.1                |
| **Intenciones**        | Conteo por intent (11), urgency_avg, resolution_rate, pct_negativo                                                                                                                                                                                                                                                 | 14            | §3.2                |

> **Total real**: ~3,209 columnas (137 estructuradas + 3,072 embeddings) para ~15,000 usuarios.
> Los embeddings dominan dimensionalidad (>95% de features) — UMAP es critico para reduccion efectiva.
> No se incluyen features de enriquecimiento TX (§3.3 — no implementado) ni embedding de Customer DNA (§3.4 — template deterministico, sin embedding).

### 4.2 Pipeline de Clustering (`src/models/cluster.py`)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. FEATURE MATRIX                                            │
│    - Join de todos los features por user_id                   │
│    - Usuarios sin conversaciones: embeddings = 0, intents = 0│
│    - Usuarios sin Customer DNA: embedding = 0                │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 2. PREPROCESAMIENTO                                          │
│    - KNN Imputer (k=5) para valores nulos                    │
│    - StandardScaler (media=0, std=1)                         │
│    - Columnas de embedding NO se escalan (ya están [-1,1])   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 3. REDUCCIÓN DE DIMENSIONALIDAD (UMAP)                       │
│    - n_components = 8 (experimentar 5-15)                    │
│    - n_neighbors = 30 (balance local/global)                 │
│    - min_dist = 0.0 (clustering)                             │
│    - metric = 'euclidean' para embeddings,                    │
│               'cosine' alternativo                           │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 4. CLUSTERING (HDBSCAN)                                      │
│    - min_cluster_size = 100  (~0.67% de la población)        │
│    - min_samples = 1                                         │
│    - cluster_selection_epsilon = 0.5                         │
│    - metric = 'euclidean'                                    │
│    - ~87% cobertura esperada (resto → cluster -1 = "ruido")  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 5. ASIGNACION DE RUIDO A CLUSTER CERCANO                     │
│    - KNN (k=1) desde puntos de ruido a centroides de cluster │
│    - Asignar al cluster del vecino mas cercano si distancia  │
│      < percentil 95 de distancias intra-cluster              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 6. VALIDACION                                                │
│    - Silhouette Score (sobre UMAP embedding)                 │
│    - DBCV descartado (inestable en espacio UMAP)             │
│    - Estabilidad: grid search sobre 16 combinaciones de      │
│      n_components x min_cluster_size                         │
└──────────────────────────────────────────────────────────────┘
```

**Hyperparametros usados (grid search)**:

| Parametro | Valores probados | Seleccionado | Criterio |
|-----------|-----------------|-------------|----------|
| `n_components` UMAP | [5, 8, 10, 15] | 8 | Maximizar Silhouette + penalizacion de ruido |
| `min_cluster_size` HDBSCAN | [50, 100, 150, 200] | 100 | Balance granularidad vs. interpretabilidad |
| `metric` UMAP | `euclidean` | `euclidean` | Unica metrica usada |
| `random_state` | 42 | 42 | Fijo para reproducibilidad |

### 4.3 Perfilamiento de Segmentos (`src/models/segments.py`)

> **ESTADO: Implementado con etiquetado deterministico (Python, sin LLM).** Costo real: $0.00 USD.

**Para cada segmento descubierto, se computa**:

1. **Estadisticas descriptivas**: Media de features demograficas, engagement, credito, transaccionales y conversacionales
2. **Top features discriminantes**: Z-score de cada feature numerica del segmento vs. poblacion general. Se seleccionan las 8 con mayor |z-score|
3. **Etiquetado deterministico** (`_label_segment()`): Genera nombre en espanol concatenando:
   - **Tag de edad**: "Jovenes" (<30), "Adultos" (<45), "Maduros"
   - **Tag de ingreso**: "Alto Ingreso" (>$25K), "Ingreso Medio" (>$12K), "Ingreso Basico"
   - **Tag de perfil**: "Pro Digitales" (>70% Hey Pro), "Crediticios" (tiene TC), "Diversificados" (>1.5 productos), "Basicos"
   - **Sufijos discriminantes** (max 3): de las top features con z-score > 0.5
   - Ejemplo: `"Jovenes Ingreso Medio Crediticios Alto Gasto Internacional"`
4. **Accion proactiva** (mapeo condicional priorizado):
   - Buen score crediticio + sin tarjeta de credito → `"Oferta segmentada: Tarjeta de Credito Hey con 5% cashback"`
   - Alto ingreso + alta adopcion Hey Pro → `"Promocion: Inversion Hey con tasa preferencial"`
   - Baja satisfaccion → `"Alerta: Campana de seguimiento para mejorar satisfaccion"`
   - Default → `"Insight: Envio de reporte mensual personalizado"`

**Output**: `data/processed/segment_profiles.json` + `data/processed/user_segments.parquet`.

---

## 5. Chatbot Agent Layer

> **Arquitectura**: Tool calling + Customer DNA como system prompt. Sin RAG vectorial (FAISS no se usa en el chatbot; solo tool calling para datos concretos).
> **Modelo**: DeepSeek-V3.2 con streaming habilitado.
> **SDK**: `openai` (compatible con endpoint OpenAI de Azure AI Foundry).

### 5.1 Arquitectura del Agente

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHATBOT AGENT                                    │
│                                                                          │
│  ┌──────────────┐    ┌───────────────────────┐                          │
│  │ SYSTEM PROMPT│    │     TOOL CALLING      │                          │
│  │              │    │                       │                          │
│  │ Customer DNA │    │ get_account_summary   │                          │
│  │ narrativo    │    │ get_recent_transactions                          │
│  │ (§3.4)       │    │ get_recommendation    │                          │
│  │              │    │                       │                          │
│  │ Voz: empatico│    │ Todas retornan datos  │                          │
│  │ y proactivo  │    │ del usuario desde     │                          │
│  │              │    │ Parquet/SQLite        │                          │
│  └──────────────┘    └───────────────────────┘                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    STREAMING RESPONSE (two-step)                  │   │
│  │  1. chat_completion (non-streaming) → detecta tool calls         │   │
│  │  2. Si hay tool calls: ejecuta tools, agrega resultados,         │   │
│  │     luego chat_completion_stream para respuesta final            │   │
│  │  3. st.write_stream() renderiza chunk por chunk                  │   │
│  │  4. Tool calls visibles en UI como cards colapsables             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 System Prompt

```
Eres Havi, el asistente virtual inteligente de Hey Banco. Tu personalidad es
empática, proactiva y experta en finanzas personales.

PERFIL DEL CLIENTE:
{customer_dna}

INFORMACIÓN DE CONTEXTO:
- Segmento: {segment_name} — {segment_description}
- Productos activos: {productos_activos}
- Última interacción: {ultima_interaccion}
- Necesidades detectadas: {necesidades_implicitas}

REGLAS:
1. Siempre personaliza tus respuestas con el contexto del cliente.
2. Sé proactivo: sugiere acciones relevantes sin que el cliente las pida.
3. Si el cliente pregunta por datos concretos (saldo, movimientos, ofertas),
   usa las herramientas disponibles.
4. No inventes información financiera. Si no tienes el dato, sé transparente.
5. Mantén un tono cálido y profesional. Usa "tú" en español mexicano.
6. Las respuestas deben ser concisas (máximo 3 párrafos cortos).
```

### 5.3 Herramientas (Tool Calling)

#### Tool 1: `get_account_summary(user_id: str)`

```python
def get_account_summary(user_id: str) -> dict:
    """Resumen de cuenta con productos activos, deudas, inversiones y cashback."""
    # Lee hey_productos y hey_clientes desde Parquet (con fallback a CSV)
    # Calcula total_deuda (credito), total_inversiones (inversion_hey),
    # cashback_acumulado, hey_pro status
    return {
        "productos": [
            {"tipo": "cuenta_debito", "saldo": 12345.67, "limite": None, ...},
            {"tipo": "tarjeta_credito_hey", "saldo": 15000, "limite": 50000,
             "utilizacion_pct": 0.30, "tasa_interes_anual": 45.0, "estatus": "activa"},
        ],
        "total_deuda": 15000,
        "total_inversiones": 50000,
        "cashback_acumulado": 340.50,
        "hey_pro": True,
    }
```

#### Tool 2: `get_recent_transactions(user_id: str, n: int = 5)`

```python
def get_recent_transactions(user_id: str, n: int = 5) -> dict:
    """Ultimas N transacciones ordenadas por fecha descendente mas alerta de patron atipico."""
    # Lee hey_transacciones, filtra por user_id, ordena por fecha_hora DESC
    # Detecta patron_uso_atipico desde hey_clientes
    return {
        "transacciones": [
            {"fecha": "2026-04-20", "monto": 850.00,
             "comercio": "Superama", "categoria": "supermercado",
             "estatus": "completada", "cashback": 8.50},
        ],
        "alerta": {
            "cargos_atipicos": True,
            "detalle": "Se ha detectado un patron de uso atipico en tu cuenta."
        } if user_has_atypical else None,
    }
```

#### Tool 3: `get_recommendation(user_id: str)`

```python
def get_recommendation(user_id: str) -> dict:
    """Recomendacion personalizada desde Customer DNA. Fallback generico si no hay DNA."""
    # Lee accion_proactiva desde customer_dna.parquet
    dna = load_dna().filter(pl.col("user_id") == user_id)
    if dna is not None and "accion_proactiva" in dna:
        return {"tipo": "oferta_segmentada", "titulo": "Recomendacion personalizada",
                "descripcion": dna["accion_proactiva"], "accion": "Consultar detalles",
                "producto_relacionado": "tarjeta_credito_hey"}
    # Fallback generico
    return {"tipo": "insight", "titulo": "Bienvenido a Hey Banco",
            "descripcion": "Te invitamos a explorar los beneficios...",
            "accion": "Explorar productos", "producto_relacionado": "cuenta_debito"}
```

### 5.4 Flujo de Conversación con Tool Calling

```
1. Usuario: "¿Cuánto debo en mi tarjeta de crédito?"
2. System: [Evalúa que necesita tool calling]
3. Agent: Invoca get_account_summary(user_id)
4. System: [Recibe datos estructurados]
5. Agent: "Tu tarjeta de crédito Hey tiene un saldo de $15,000 de $50,000
   disponibles. Tu fecha de corte es el 15 de mayo. ¿Quieres que
   revisemos tus últimos cargos para ver en qué se fue ese saldo?"
6. Usuario: "Sí, por favor"
7. Agent: Invoca get_recent_transactions(user_id, n=5)
8. Agent: "Veo que este mes tuviste compras en Superama ($850), Uber Eats ($320),
   y un cargo atípico en VivaAerobus por $4,500. Por cierto, ese vuelo te generó
   $45 de cashback. ¿Necesitas ayuda para planear el pago de tu tarjeta?"
```

### 5.5 Streaming en Streamlit (Two-Step)

```python
# src/chatbot/agent.py — enfoque real (two-step)
from openai import OpenAI

def chat_with_tools(messages, tools) -> Generator:
    """Generador de eventos (texto o tool_call) para streaming en Streamlit."""
    client = OpenAI(
        base_url=os.environ["AZURE_CHAT_BASE_URL"],
        api_key=os.environ["AZURE_CHAT_API_KEY"],
    )
    # Paso 1: Detectar tool calls (non-streaming)
    response = client.chat.completions.create(
        model="DeepSeek-V3.2",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    if response.choices[0].message.tool_calls:
        # Ejecutar tools, yield resultados como eventos
        for tc in response.choices[0].message.tool_calls:
            result = _execute_tool(tc.function.name, tc.function.arguments)
            yield {"type": "tool_call", "name": tc.function.name, "result": result}
        # Paso 2: Respuesta final con streaming
        messages.append(...)  # tool results como mensajes
        response_stream = client.chat.completions.create(
            model="DeepSeek-V3.2",
            messages=messages,
            tools=tools,
            stream=True,
        )
        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                yield {"type": "text", "content": chunk.choices[0].delta.content}
    else:
        yield {"type": "text", "content": response.choices[0].message.content}

# src/dashboard/components/chatbot_ui.py
def render_chat_ui(user_id, ...):
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        for event in chat_with_tools(messages, tools):
            if event["type"] == "tool_call":
                with st.status("Consultando tus datos..."):
                    st.caption(f"Tool: {event['name']}")
            elif event["type"] == "text":
                full += event["content"]
                placeholder.markdown(full)
    st.rerun()
```

---

## 6. Streamlit Dashboard

### 6.1 Páginas

```
🏠 Home / Overview
├── KPIs: Total usuarios, segmentos, Satisfaccion Promedio, usuarios Hey Pro %
├── Metricas de conversaciones: Interacciones Havi, Conversaciones, Resolution Rate, % sentimiento negativo
├── Metricas transaccionales: Volumen Total TX, Ticket Promedio, % no procesadas, Cashback Total
├── Quick insights y navegacion rapida a otras paginas
└── Distribucion de segmentos (treemap)

🔍 Segment Explorer
├── UMAP 2D scatter plot (coloreado por segmento, interactivo con Plotly)
├── Tarjeta de segmento seleccionado:
│   ├── Nombre, descripcion (generado deterministicamente)
│   ├── Tamano (# usuarios, %)
│   ├── Top 8 features discriminantes (bar chart horizontal Altair, |z-score|)
│   ├── Necesidades implicitas (lista de bullets)
│   └── Accion proactiva recomendada
├── Comparacion side-by-side de dos segmentos
└── [NO IMPLEMENTADO] Tabla de usuarios del segmento con drill-down

👤 Customer 360
├── Selector de usuario (dropdown con busqueda por user_id)
├── Ficha completa:
│   ├── Health score gauge (0-100) + tags (Hey Pro, Nomina, etc.)
│   ├── Demografia (card con avatar y campos etiquetados)
│   ├── Productos activos (cards visuales con iconos, saldo, estatus)
│   ├── Customer DNA (texto narrativo completo)
│   ├── Radar chart: perfil del usuario vs. promedio de su segmento
│   ├── Acciones proactivas (cards con iconos)
│   ├── Transacciones recientes (tabla de ultimas 10)
│   └── Donut chart de gasto por categoria
└── Boton "Hablar con Havi" → navega a pagina chatbot con usuario preseleccionado

💬 Havi Next (Chatbot)
├── Selector de usuario (carga el contexto automaticamente)
├── Chat UI con historial de conversacion completo
├── Customer DNA como system prompt
├── Respuesta en two-step: deteccion de tool calls (non-streaming) → respuesta final (streaming)
├── Tool calls visibles como "Consultando tus datos..." durante ejecucion
├── Sugerencias de prompts (chips clickeables)
└── Errores manejados con mensaje en placeholder

📈 Analytics
├── Tab 1 — Actividad Transaccional:
│   ├── Top metricas (transacciones, volumen, interacciones Havi, % voz)
│   ├── Heatmap hora × dia de la semana (monto promedio)
│   └── Sankey diagram: categoria → tipo operacion → estatus
├── Tab 2 — Conversaciones:
│   ├── Sunburst de intenciones (si hay datos de intenciones)
│   ├── Distribucion de canal (texto vs. voz)
│   └── Sentiment breakdown
├── Tab 3 — Adopcion de Productos:
│   ├── Tabla de adopcion de productos
│   └── Hey Pro %, usuarios con seguro, usuarios con patron atipico
└── [NO IMPLEMENTADO] Funnel consulta → resuelto vs. escalado
└── [NO IMPLEMENTADO] Cohortes por antiguedad vs. engagement
```

### 6.2 Setup de Páginas (Streamlit Multipage)

```
src/dashboard/
├── app.py                  # Entry point (st.navigation)
├── pages/
│   ├── home.py
│   ├── segments.py
│   ├── customer_360.py
│   ├── chatbot.py
│   └── analytics.py
├── components/
│   ├── charts.py           # Plotly/Altair wrappers
│   ├── cards.py            # Métricas y tarjetas
│   └── chatbot_ui.py       # Chat UI reutilizable
└── utils/
    ├── data_loader.py      # Carga desde SQLite/Parquet
    └── styling.py          # Tema, colores, CSS
```

### 6.3 Visualizaciones Clave

| Vista                 | Libreria         | Interactividad                     |
| --------------------- | ---------------- | ---------------------------------- |
| UMAP 2D Scatter       | Plotly Express   | Hover con user_id, zoom, seleccion |
| Segment Treemap       | Plotly           | Tooltip con tamano y %             |
| Feature Importance    | Altair           | Bar chart con tooltip z-score      |
| Transacciones Heatmap | Plotly           | Hora x Dia, escala de color monto  |
| Sankey (Categorias)   | Plotly           | Nodes arrastrables                 |
| Radar Chart (360)     | Plotly           | Overlay usuario vs. segmento       |
| Donut Chart           | Plotly           | Gastos por categoria               |
| Sunburst (Intenciones)| Plotly           | Jerarquia de intenciones           |
| Chat UI               | Streamlit nativo | `st.chat_input`, `st.chat_message` |

---

## 7. Infraestructura & DevOps

### 7.1 Stack Tecnológico

| Capa                    | Tecnología                        | Versión       | Justificación                                                  |
| ----------------------- | --------------------------------- | ------------- | -------------------------------------------------------------- |
| **Lenguaje**            | Python                            | 3.11+         | Requisito del equipo                                           |
| **DataFrames**          | Polars + Pandas                   | latest        | Polars para ETL pesado, Pandas para compatibilidad con sklearn |
| **ML**                  | scikit-learn, UMAP-learn, HDBSCAN | latest        | Ligero, sin GPU necesaria                                      |
| **LLM** | Azure AI Foundry + Azure OpenAI | DeepSeek-V3.2 + text-embedding-3-large | Student plan, serverless DeepSeek (chat) + managed endpoint (embeddings) |
| **Dashboard**           | Streamlit                         | ≥1.28         | Requisito, soporte nativo de streaming                         |
| **Visualización**       | Plotly + Altair                   | latest        | Interactivo, integración nativa con Streamlit                  |
| **Vector Store**        | FAISS (in-memory)                 | latest        | Sin dependencia externa, rápido para ~15K vectores             |
| **Almacenamiento**      | SQLite + Parquet                  | built-in      | Volumen pequeño (~200MB total), self-contained                 |
| **Orquestación actual** | Makefile                          | —             | Scripts secuenciales                                           |
| **Orquestación futura** | Prefect                           | latest        | Arquitectura lista para migrar                                 |
| **Entorno**             | venv + pip-tools                  | —             | Reproducible con `requirements.txt`                            |

### 7.2 Servicios Azure

| Servicio                        | Uso                                 | Costo (Student)         |
| ------------------------------- | ----------------------------------- | ----------------------- |
| **Azure AI Foundry** | DeepSeek-V3.2 (chat + tool calling) | Pay-as-you-go por token |
| **Azure OpenAI** | text-embedding-3-large (embeddings) | Pay-as-you-go por token |
| _(Opcional)_ Azure Blob Storage | Backup de datasets                  | Gratis (5GB LRS hot)    |

### 7.3 Seguridad

```
.gitignore:
  .env*
  data/raw/
  data/processed/
  data/*.db
  __pycache__/
  .venv/
  *.pyc
  .DS_Store
  docs/checklist_implementacion.md
```

> **Streamlit se ejecuta 100% local**. Las keys de Azure nunca salen del entorno.
> No se usa Streamlit Community Cloud ni ngrok.

### 7.4 Dependencias (`requirements.txt`)

```
# Core
pandas>=2.0
polars>=0.20
numpy>=1.24

# ML
scikit-learn>=1.3
umap-learn>=0.5
hdbscan>=0.8
shap>=0.42

# LLM — Azure AI Foundry + Azure OpenAI
openai>=1.0
azure-core

# Vector Store
faiss-cpu>=1.7

# Dashboard
streamlit>=1.28
plotly>=5.15
altair>=5.0
watchdog>=6.0

# Utils
python-dotenv>=1.0
pyarrow>=14.0
joblib>=1.3

# Pipeline (opcional futuro)
prefect>=2.0
```

### 7.5 Makefile

```makefile
.PHONY: validate ingest enrich features cluster dashboard all clean

# Data
validate:
	python src/data/validate.py

ingest:
	python src/data/ingest.py

# Enrichment (3 modulos implementados, descriptions es STUB)
enrich:
	python -m src.enrichment.embeddings
	python -m src.enrichment.intents
	python -m src.enrichment.customer_dna

# Feature Engineering
features:
	python src/features/build_matrix.py

# Clustering
cluster:
	python src/models/cluster.py
	python src/models/segments.py

# Dashboard
dashboard:
	streamlit run src/dashboard/app.py

# Pipeline completo
all: validate enrich features cluster
	@echo "Pipeline completado. Ejecuta 'make dashboard' para Streamlit."

# Limpieza de outputs intermedios
clean:
	rm -rf data/processed/*
	rm -f data/*.db
```

### 7.6 Preparación para Migrar a Prefect

Cada script ya está diseñado como una función principal con firma clara:

```python
# src/enrichment/embeddings.py
def run_embeddings(data_dir: str, output_dir: str) -> None:
    """Genera embeddings conversacionales por usuario."""
    ...

if __name__ == "__main__":
    run_embeddings("data/raw/", "data/processed/")
```

Para migrar a Prefect solo se requiere:

```python
from prefect import task, flow

@task(retries=3, retry_delay_seconds=30)
def embeddings_task():
    run_embeddings("data/raw/", "data/processed/user_embeddings.parquet")

@flow
def enrichment_flow():
    embeddings_task()
    intents_task()
    descriptions_task()
    customer_dna_task()
```

---

## 8. Estructura del Repositorio

```
DatathonTec2026/
│
├── .env                          # Variables de entorno (gitignored)
├── .gitignore                    # Excluye .env, data/, __pycache__
├── Makefile                      # Orquestacion secuencial
├── requirements.txt              # Dependencias
├── AGENTS.md                     # Instrucciones para agentes de IA
│
├── Arquitectura.md               # Este documento
├── stack.md                      # Stack tecnologico con versiones
│
├── data/                         # Gitignored
│   ├── raw/                      # Datasets originales
│   │   ├── hey_clientes.csv
│   │   ├── hey_productos.csv
│   │   ├── hey_transacciones.csv
│   │   └── dataset_50k_anonymized.parquet
│   ├── processed/                # Datasets enriquecidos (generados)
│   │   ├── user_embeddings.parquet
│   │   ├── conv_intents.parquet
│   │   ├── user_intents.parquet
│   │   ├── customer_dna.parquet
│   │   ├── feature_matrix.parquet
│   │   ├── user_segments.parquet
│   │   └── segment_profiles.json
│   └── features.db               # SQLite feature store
│
├── docs/
│   ├── diccionario_datos_transacciones.md
│   ├── diccionario_datos_conversaciones.md
│   └── Presentacion.md
│
├── notebooks/                    # Vacio — exploracion pendiente
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── validate.py            # Validacion de schemas (COMPLETO)
│   │   └── ingest.py              # Carga y limpieza inicial (COMPLETO)
│   │
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── embeddings.py          # §3.1 Embeddings conversacionales (COMPLETO)
│   │   ├── intents.py             # §3.2 Extraccion de intenciones (COMPLETO)
│   │   ├── descriptions.py        # §3.3 Normalizacion descripciones (STUB)
│   │   ├── customer_dna.py        # §3.4 Customer DNA template (COMPLETO, $0)
│   │   └── llm_client.py          # Cliente Azure compartido (COMPLETO)
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   └── build_matrix.py        # Construccion de feature matrix (COMPLETO)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cluster.py             # UMAP + HDBSCAN pipeline (COMPLETO)
│   │   └── segments.py            # Perfilamiento y labeling deterministico (COMPLETO)
│   │
│   ├── chatbot/
│   │   ├── __init__.py
│   │   ├── agent.py               # Chatbot con tool calling + streaming two-step (COMPLETO)
│   │   └── tools.py               # Implementacion de 3 herramientas (COMPLETO)
│   │
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py                 # Entry point Streamlit (COMPLETO)
│       ├── pages/
│       │   ├── __init__.py
│       │   ├── home.py            # Home / KPIs (COMPLETO)
│       │   ├── segments.py        # Segment Explorer (COMPLETO)
│       │   ├── customer_360.py    # Customer 360 (COMPLETO)
│       │   ├── chatbot.py         # Havi Next Chat (COMPLETO)
│       │   └── analytics.py       # Analytics (COMPLETO)
│       ├── components/
│       │   ├── __init__.py
│       │   ├── charts.py          # Plotly/Altair wrappers (COMPLETO)
│       │   ├── cards.py           # Metricas y tarjetas (COMPLETO)
│       │   └── chatbot_ui.py      # Chat UI con streaming (COMPLETO)
│       └── utils/
│           ├── __init__.py
│           ├── data_loader.py     # Carga cacheada desde Parquet/JSON (COMPLETO)
│           └── styling.py         # Tema CSS, colores Hey Banco (COMPLETO)
```

---

## 9. Plan de Implementación

### Fases y Duración Estimada

| Fase       | Descripcion               | Estado      | Dependencias |
| ---------- | ------------------------- | ----------- | ------------ |
| **Fase 1** | Data prep & validacion    | COMPLETO | —            |
| **Fase 2** | Enrichment batch (LLM)    | COMPLETO (parcial: embeddings, intenciones, DNA. Descripciones = STUB) | Fase 1       |
| **Fase 3** | Feature engineering       | COMPLETO | Fase 2       |
| **Fase 4** | Clustering & segmentacion | COMPLETO | Fase 3       |
| **Fase 5** | Streamlit dashboard       | COMPLETO | Fase 4       |
| **Fase 6** | Chatbot streaming         | COMPLETO | Fase 4       |
| **Fase 7** | Pitch deck & ensayo       | PENDIENTE    | Fase 5+6     |
| **Fase 8** | Makefile + polish         | COMPLETO | Fase 5+6     |

### Detalle por Fase

#### Fase 1: Data Prep & Validacion

- [x] Leer datasets en Polars/Pandas
- [x] Validar schemas contra diccionario de datos (checks 1.2, 1.3, 1.7, 1.8)
- [x] Chequear nulls, rangos, FK integrity, duplicados
- [x] Cruce de `user_id` entre datasets
- [x] Ingesta: limpiar, estandarizar fechas, guardar como Parquet

#### Fase 2: Enrichment Batch

- [x] Configurar cliente Azure (`src/enrichment/llm_client.py`) — chat (DeepSeek-V3.2) + embeddings (text-embedding-3-large)
- [x] Embeddings: vectorizar ~24K conversaciones, mean-pool por usuario (3072 dims, $0.20)
- [x] Intenciones: clasificar conversaciones en batch (50 por llamada), con soporte de sampling
- [ ] Descripciones: **STUB** — no implementado (archivo con `pass`)
- [x] Customer DNA: perfil narrativo deterministico (~5.6K usuarios, $0.00, <1 segundo)

#### Fase 3: Feature Engineering

- [x] Join de todas las features por `user_id`
- [x] Manejo de usuarios sin conversaciones (imputacion por cero)
- [x] One-hot encoding para categoricas
- [x] Agregaciones transaccionales (frecuencia, montos, categorias)
- [x] Feature matrix final: ~3,209 columnas → `data/processed/feature_matrix.parquet`

#### Fase 4: Clustering & Segmentacion

- [x] KNN Imputer (k=5) + StandardScaler (sin escalar columnas de embedding)
- [x] UMAP reduccion a 8 dimensiones
- [x] HDBSCAN clustering con grid search (16 combinaciones, Silhouette scoring)
- [x] Asignacion de ruido a clusters cercanos (KNN k=1, percentil 95)
- [x] Validacion (Silhouette)
- [x] Segment labeling deterministico (reglas Python, $0)
- [x] Perfiles de segmento con acciones proactivas

#### Fase 5: Streamlit Dashboard

- [x] Configurar `st.navigation` con 5 paginas
- [x] Home: KPIs con sparklines, treemap de segmentos, quick insights, navegacion
- [x] Segment Explorer: UMAP scatter + tarjeta de segmento con comparacion
- [x] Customer 360: ficha completa + radar chart + donut + transacciones
- [x] Analytics: heatmap, sankey, sunburst, adopcion de productos
- [x] Chatbot page

#### Fase 6: Chatbot Streaming

- [x] Implementar 3 herramientas: `get_account_summary`, `get_recent_transactions`, `get_recommendation`
- [x] Integrar Customer DNA como system prompt
- [x] Streaming two-step: deteccion de tool calls (non-streaming) → respuesta final (streaming)
- [x] UI de chat con tool calls visibles y sugerencias de prompts
- [x] Errores manejados con mensaje en placeholder

#### Fase 7: Pitch Deck & Ensayo

- [ ] Presentación ejecutiva (slides)
- [ ] Storytelling: problema → solución → impacto
- [ ] Demo grabado o live del dashboard + chatbot
- [ ] Alineación con rúbrica (cada slide mapea a un criterio)

#### Fase 8: Makefile + Polish

- [ ] Targets Makefile funcionales: `make validate`, `make enrich`, etc.
- [ ] `make all` pipeline completo
- [ ] Archivo `.env.example`
- [ ] README con instrucciones de setup
- [ ] Limpieza de código, type hints, docstrings

---

## 10. Estimacion de Costos (Azure AI Foundry)

### DeepSeek-V3.2 + text-embedding-3-large Pricing

| Modelo                 | Input (por 1M tokens) | Output (por 1M tokens) |
| ---------------------- | --------------------- | ---------------------- |
| DeepSeek-V3.2          | $0.27                 | $1.10                  |
| text-embedding-3-large | $0.13                 | --                     |

### Costo Real por Tarea (con codigo implementado)

| Tarea                                        | Tokens In (M) | Tokens Out (M)    | Costo      |
| -------------------------------------------- | ------------- | ----------------- | ---------- |
| Embeddings conversacionales                  | 10.0          | -- (embedding API) | **$0.20**  |
| Intenciones (24K conv x batch 50)            | 12.0          | 3.0               | **$6.54**  |
| Descripciones                               | --            | --                | **$0.00** (STUB, no implementado) |
| Customer DNA                                | --            | --                | **$0.00** (template deterministico) |
| Chatbot demo (streaming, ~100 interacciones) | 0.5           | 0.5               | **$0.69**  |
| Segment labeling (~10 segmentos)             | --            | --                | **$0.00** (reglas Python) |
| **TOTAL**                                    | **22.5**      | **3.5**           | **~$7.43** |

> Con DeepSeek-V3.2 + text-embedding-3-large, el costo total real es ~$7.43 USD — muy por debajo del presupuesto de $20.

### Estrategias de Mitigacion de Costos (opcional, ya innecesarias)

| Estrategia                                                                                                                                                   | Ahorro Est. | Estado       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | ------------ |
| Customer DNA template deterministico (implementado): reemplaza LLM con reglas Python.                                                                       | $5.33       | APLICADO |
| Descripciones no implementadas (STUB): si se implementa con regex en vez de LLM, costo es $0.                                                               | $3.55       | APLICADO |
| Segment labeling deterministico (implementado): reglas Python en vez de LLM.                                                                                | $0.04       | APLICADO |
| **Ahorro total aplicado**                                                                                                                                     | **$8.92**   | --           |

### Plan de Ejecucion con Presupuesto Controlado (Real)

```
Orden de ejecucion real (ya completado):

1. Embeddings      → $0.20  (text-embedding-3-large, mean-pool por usuario)
2. Intenciones     → $6.54  (DeepSeek-V3.2, 24K conversaciones, batch 50)
3. Customer DNA    → $0.00  (Template deterministico Python, <1 segundo)
4. Segment Labeling → $0.00  (Reglas Python, sin LLM)
5. Descripciones    → $0.00  (STUB — no implementado)
6. Chatbot demo    → $0.69  (DeepSeek-V3.2 streaming, ~100 interacciones)
───────────────────────────────────────
   Total           → ~$7.43  ← Muy por debajo de $20

Presupuesto restante: ~$12.57. Puede usarse para:
- Procesar intenciones al 100% (si se ejecuto con sample <100%)
- Implementar descripciones con LLM si se requiere ($3.55)
- Ampliar chatbot demo con mas interacciones
- Iteraciones adicionales de enriquecimiento
```

---

## 11. Alineación con Rúbrica de Evaluación

| Criterio                        | Peso | Cómo lo cubrimos                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Objetivos y Alcance**         | 15%  | Definicion clara de clases: segmentos descubiertos por aprendizaje no supervisado (HDBSCAN) con features enriquecidas por LLM. Esquema de evaluacion no supervisado: Silhouette + grid search (DBCV descartado por inestable en UMAP). Plan de accion: 4 tipos de automatizacion proactiva (ofertas, alertas, insights, promociones) mapeadas a cada segmento. |
| **Innovacion y Creatividad**    | 35%  | Customer DNA: perfil narrativo deterministico como system prompt del chatbot. 3 tecnicas de enriquecimiento (embeddings + intenciones + DNA template). Tool calling nativo openai SDK (3 herramientas) con streaming two-step en Streamlit. Segment labeling automatizado con reglas Python (sin LLM). Dashboard interactivo con 5 paginas, tema personalizado Hey Banco. |
| **Impacto y Viabilidad**        | 35%  | Costo total real ~$7.43 (presupuesto $20, ~$12.57 de sobra). Escalable a millones de usuarios (batching, arquitectura modular). Sin vendor lock-in: Azure es el unico servicio externo, endpoints OpenAI-compatibles. Impacto medible: metricas de experiencia de cliente (satisfaccion, resolution rate, score buro, patrones atipicos). |
| **Presentacion y Comunicacion** | 15%  | Dashboard Streamlit interactivo con 5 vistas (Home, Segmentos, Customer 360, Havi Next, Analytics). Chatbot con streaming en tiempo real → demo funcional. Customer 360 con ficha completa y recomendaciones. Storytelling: del dato crudo a la accion proactiva personalizada. Tema visual Hey Banco (dark/white). |

---

## 12. Decisiones de Arquitectura

### Decisiones Clave

| #   | Decisión                                                                | Alternativas Consideradas                                      | Justificación                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **DeepSeek-V3.2** sobre GPT-4.1 mini | GPT-4.1 mini, GPT-4o, Claude 3.5 Sonnet, Llama 3 | ~33% más barato en input, ~31% en output. Disponible en Azure AI Foundry como serverless OpenAI-compatible. Tool calling y JSON structured output nativos. Costo total estimado $17.45 (dentro de $20). |
| 2   | **HDBSCAN** sobre KMeans                                                | KMeans, Gaussian Mixture, DBSCAN, Agglomerative                | HDBSCAN descubre número de clusters automáticamente, maneja ruido, no asume formas esféricas ni gaussianas. KMeans requeriría asumir K a priori.                                   |
| 3   | **UMAP** sobre PCA/t-SNE                                                | PCA, t-SNE, PaCMAP                                             | UMAP preserva estructura global y local, escala a alta dimensionalidad (embeddings 1536-dim), más rápido que t-SNE.                                                                |
| 4   | **Feature Matrix ~3,200 cols** sobre Autoencoders                         | Autoencoders, VAE, Deep Clustering                             | Interpretabilidad: cada feature tiene nombre y significado de negocio. Autoencoders son caja negra. El volumen (15K x ~3,200) es manejable sin GPU. |
| 5   | **FAISS in-memory** sobre Pinecone/Weaviate                             | Pinecone, Weaviate, ChromaDB                                   | 15K vectores caben en RAM (~100MB). FAISS sin servidor, sin costo, sin latencia de red. Self-contained.                                                                            |
| 6 | **Tool Calling nativo (openai SDK)** sobre LangChain/LlamaIndex | LangChain Agents, LlamaIndex, CrewAI | Zero-dependency adicional. OpenAI SDK nativo maneja tool calling desde v1.0. Menos abstracción → más control sobre streaming y costos. DeepSeek expone endpoint OpenAI-compatible. |
| 7   | **Makefile** sobre Airflow/Prefect (inicial)                            | Prefect, Airflow, Dagster                                      | Makefile es zero-config. Scripts ya están diseñados para migrar a Prefect (funciones puras con entrada/salida clara).                                                              |
| 8   | **SQLite + Parquet** sobre PostgreSQL/Blob                              | PostgreSQL, Azure Blob, MongoDB                                | Volumen pequeño (~200MB). Auto-contenido, sin servidor, portable. Parquet para DataFrames, SQLite para consultas rápidas desde Streamlit.                                          |
| 9   | **Polars para ETL** sobre Pandas-only                                   | Pandas solo                                                    | Polars es lazy, multithreaded por defecto, más eficiente en memoria. Pandas para compatibilidad con sklearn/umap.                                                                  |
| 10  | **Streamlit local** sobre Community Cloud                               | Streamlit Cloud, Gradio, Dash                                  | Requisito explícito. Ejecución local elimina exposición de keys Azure. Streamlit tiene streaming nativo (`st.write_stream`).                                                       |

### Trade-offs Aceptados

| Trade-off                                                                                                                             | Impacto                                                    | Mitigacion                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **DeepSeek-V3.2 puede tener precision diferente en intenciones vs. otros modelos** | Clasificacion de intenciones puede tener ~85-90% accuracy. | Batch de 50 conversaciones. Validacion y normalizacion de valores contra enumeraciones permitidas. |
| **HDBSCAN deja usuarios como ruido (cluster -1)**                                                                                     | Algunos usuarios no asignados a segmento                  | Reasignacion por KNN (k=1) al cluster mas cercano con umbral de distancia (percentil 95 intra-cluster). |
| **UMAP no-deterministico**                                                                                                            | Clusters pueden variar entre ejecuciones                   | Fijar `random_state=42`. Grid search sobre 16 combinaciones de hiperparametros. |
| **Customer DNA deterministico (template) es menos personalizado que LLM**                                                             | Perfiles genericos vs. personalizados                      | El template cubre 6 dimensiones con logica condicional especifica. Datos factuales del dataset (sin riesgo de alucinacion). |
| **Streamlit local = no compartir dashboard facilmente**                                                                               | Solo visible en la maquina del equipo                      | Grabacion de demo para el pitch. Compartir pantalla en presentacion. |

---

## Apéndice A: Referencia Rápida de Comandos

```bash
# Setup inicial
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # o crea .env con tus keys de Azure

# Pipeline completo
make all

# Etapas individuales
make validate    # Validacion de datos
make ingest      # Carga y limpieza inicial
make enrich      # Enrichment (embeddings + intenciones + customer DNA)
make features    # Feature matrix
make cluster     # UMAP + HDBSCAN + segment labeling
make dashboard   # Streamlit

# Chatbot
streamlit run src/dashboard/app.py   # Navega a pagina Havi Next

# Limpieza
make clean
```

---

## Apéndice B: Glosario

| Término          | Definición                                                                                                                                                           |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Customer DNA** | Perfil narrativo generado por LLM que describe necesidades implícitas, comportamiento financiero y oportunidades de atención proactiva de un cliente.                |
| **Embedding**    | Representacion vectorial densa de texto (3072 dimensiones) que captura semantica. Generado con `text-embedding-3-large`. |
| **HDBSCAN**      | Hierarchical Density-Based Spatial Clustering of Applications with Noise. Algoritmo de clustering que descubre automáticamente el número de clusters y maneja ruido. |
| **RAG**          | Retrieval-Augmented Generation. Tecnica donde el modelo recupera datos antes de generar respuesta. En este proyecto, el chatbot usa tool calling + Customer DNA como system prompt (sin FAISS/vector retrieval). |
| **Tool Calling** | Capacidad del LLM de invocar funciones externas (herramientas) para obtener datos que no están en su contexto.                                                       |
| **UMAP**         | Uniform Manifold Approximation and Projection. Algoritmo de reducción de dimensionalidad que preserva estructura local y global.                                     |
| **MCC**          | Merchant Category Code. Código que clasifica el giro comercial de un establecimiento.                                                                                |
| **NPS**          | Net Promoter Score. Métrica de satisfacción del cliente (escala 1-10).                                                                                               |
| **SPEI**         | Sistema de Pagos Electrónicos Interbancarios. Sistema de transferencias del Banco de México.                                                                         |
| **CoDi**         | Cobro Digital. Plataforma de pagos móviles de Banxico mediante QR.                                                                                                   |
| **GAT**          | Ganancia Anual Total. Rendimiento de productos de inversión.                                                                                                         |

---

_Documento de arquitectura — DatathonTec 2026 · Hey Banco · Versión 1.0_
