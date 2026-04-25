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
                    │   FEATURE ENRICHMENT (LLM)      │
                    │   Azure AI Foundry DeepSeek-V3.2 │
                    │                                  │
                    │  ① Embeddings Conversacionales   │
                    │  ② Extracción de Intenciones     │
                    │  ③ Normalización Descripciones   │
                    │  ④ Customer DNA Narrativo        │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   UNSUPERVISED LEARNING          │
                    │                                  │
                    │  Feature Matrix (15K × 220)      │
                    │  StandardScaler + KNN Imputer    │
                    │  UMAP (n_components=8)           │
                    │  HDBSCAN (min_cluster=100)       │
                    │  Segment Labeling (LLM)          │
                    └───────────────┬────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
┌──────────▼──────────┐  ┌─────────▼─────────┐  ┌──────────▼──────────┐
│   STREAMLIT APP     │  │   INSIGHTS STORE  │  │   CHATBOT AGENT     │
│                     │  │                   │  │                      │
│ • Overview KPIs     │  │ • Segmentos       │  │ • RAG sobre datos   │
│ • Segment Explorer  │  │ • Perfiles        │  │   del usuario       │
│ • Customer 360      │  │ • Customer DNA    │  │ • Tool Calling (3)  │
│ • Analytics         │  │ • Recomendaciones │  │ • Streaming real-   │
│ • Havi Next (Chat)  │  │                   │  │   time en Streamlit │
└─────────────────────┘  └───────────────────┘  └─────────────────────┘
```

### Flujo End-to-End

```
Ingesta → Validación → Enrichment (LLM batch) → Feature Engineering
→ Clustering No Supervisado → Perfilamiento de Segmentos
→ Dashboard Streamlit + Chatbot RAG con Streaming
```

### Principios de Diseño

| Principio                                  | Implementación                                                                             |
| ------------------------------------------ | ------------------------------------------------------------------------------------------ |
| **Sandbox sin restricciones regulatorias** | Datos 100% sintéticos. Sin compliance de CNBV/LFPDPPP. Libertad para APIs externas.        |
| **Cloud**                                  | Azure for Students. Servicio principal: Azure OpenAI (GPT-4.1 mini).                       |
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
# Checks a ejecutar:
# 1. Schema: columnas esperadas, tipos correctos
# 2. Nulls esperados: limite_credito/tasa_interes nulos para no-crédito
# 3. Rangos: score_buro [295, 850], satisfaccion [3, 10], edad > 0
# 4. FK integrity: user_ids en productos/transacciones existen en clientes
# 5. Duplicates: user_id único en clientes, transaccion_id único
# 6. Encoding: M/H/SE, estados válidos de México, fechas ISO
# 7. Cruce conversaciones: ¿cuántos user_id de Havi matchean con clientes?
```

---

## 3. Feature Enrichment Layer

> **Modelo**: DeepSeek-V3.2 via Azure AI Foundry (serverless endpoint, `AZURE_INFERENCE_CREDENTIAL` + `AZURE_INFERENCE_ENDPOINT`).
> **Modo**: Batch síncrono con rate limiting (60 RPM). Structured Output (JSON Schema) donde aplique.

### 3.1 Embeddings Conversacionales (`src/enrichment/embeddings.py`)

**Objetivo**: Vectorizar la semántica de lo que cada usuario pregunta a Havi.

| Parámetro                  | Valor                                                                 |
| -------------------------- | --------------------------------------------------------------------- |
| **Modelo** | `text-embedding-3-large` (via Azure OpenAI) |
| **Dimensionalidad** | 3072 |
| **Entrada** | Campo `input` de cada interacción (mensaje del usuario) |
| **Preprocesamiento** | Concatenar mensajes del usuario por conversación en orden cronológico |
| **Agregación por usuario** | Mean-pooling + [varianza, min, max] por dimensión → ~3120 features |
| **Batch size** | 500 textos por llamada |
| **Estimación tokens** | ~10M tokens totales |
| **Costo estimado** | $1.30 USD |

**Output**: `data/processed/user_embeddings.parquet` — un vector de ~1560 dimensiones por `user_id`.

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
| **Costo estimado**    | $3.60 USD                                                  |

**Agregación por usuario**:

- Conteo por tipo de intención
- Proporción de sentimiento negativo
- Urgencia máxima y promedio
- Tasa de resolución (resuelto / total)
- Total de conversaciones, mensajes promedio, canal texto/voz ratio

**Output**: `data/processed/user_intents.parquet` + `data/processed/conv_intents.parquet`.

### 3.3 Normalización de Descripciones (`src/enrichment/descriptions.py`)

**Objetivo**: Extraer información estructurada del campo `descripcion_libre` en transacciones (texto libre no estandarizado).

**Prompt**:

```
Extrae de esta descripción de transacción:
- merchant_name: nombre del comercio
- category: categoría (supermercado, restaurante, delivery, etc.)
- is_subscription: true si parece suscripción recurrente
- is_recurring: true si es pago periódico
```

| Parámetro             | Valor                                                        |
| --------------------- | ------------------------------------------------------------ |
| **Entrada**           | `descripcion_libre` de `hey_transacciones` donde no sea nulo |
| **Batch**             | 100 descripciones por llamada                                |
| **Estimación tokens** | ~5M in / ~2M out                                             |
| **Costo estimado**    | $2.00 USD                                                    |

**Agregación por usuario**:

- Comercio más frecuente
- Número de suscripciones detectadas (cruce con `cargo_recurrente`)
- Diversidad de categorías (entropía)

**Output**: `data/processed/tx_enriched.parquet`.

### 3.4 Customer DNA Narrativo (`src/enrichment/customer_dna.py`)

**Objetivo**: Generar un perfil narrativo de 150-200 palabras por usuario que describa necesidades implícitas, comportamiento financiero y oportunidades de atención proactiva.

**Prompt (por usuario)**:

```
Eres un analista financiero de Hey Banco. Genera un perfil narrativo del siguiente cliente
basado en sus datos. Incluye:
- Perfil demográfico y comportamiento digital
- Uso de productos financieros
- Patrones de gasto y transacciones
- Historial de interacciones con el asistente virtual Havi
- Necesidades implícitas no expresadas
- Oportunidades de atención proactiva (ofertas, alertas, insights)

[Sesión de datos del usuario: demografía, productos, top transacciones, top conversaciones]
```

| Parámetro             | Valor                                              |
| --------------------- | -------------------------------------------------- |
| **Entrada**           | Datos agregados por usuario (~500 tokens cada uno) |
| **Batch**             | 25 usuarios por llamada                            |
| **Estimación tokens** | ~7.5M in / ~3M out                                 |
| **Costo estimado**    | $3.00 USD                                          |

**Doble output**:

1. **Texto narrativo** → almacenado en SQLite, usado como `system prompt` del chatbot personalizado
2. **Embedding del perfil** (text-embedding-3-large, 3072 dims) → feature adicional para clustering

**Output**: `data/processed/customer_dna.parquet` (texto + embedding por usuario).

### 3.5 Optimizaciones de Costo y Rendimiento

| Estrategia            | Detalle                                                                         |
| --------------------- | ------------------------------------------------------------------------------- |
| **Caché**             | Embeddings cacheados por texto. Si un input ya fue procesado, no se re-consume. |
| **Rate Limiting**     | 60 RPM (Azure OpenAI Student tier). Semáforo asíncrono con `asyncio`.           |
| **Retry con backoff** | 3 reintentos con exponential backoff (1s, 2s, 4s) para rate limits.             |
| **Batching**          | Máximo tokens por request: 4096 (input). Agrupar para minimizar llamadas.       |
| **JSON Mode**         | Structured output en lugar de parseo libre. Reduce tokens de salida y errores.  |

---

## 4. Unsupervised Learning Layer

### 4.1 Feature Matrix Final (~220 columnas)

| Grupo                  | Features                                                                                                                                                                                                                                                                                                           | Cardinalidad | Origen              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | ------------------- |
| **Demográficas**       | edad, genero (one-hot), estado (one-hot), nivel_educativo (ordinal), ocupacion (one-hot), ingreso_mensual_mxn, idioma_preferido                                                                                                                                                                                    | ~40          | `hey_clientes`      |
| **Engagement**         | antiguedad_dias, dias_desde_ultimo_login, preferencia_canal (one-hot), satisfaccion_1_10, es_hey_pro, nomina_domiciliada, recibe_remesas, usa_hey_shop                                                                                                                                                             | ~10          | `hey_clientes`      |
| **Crédito**            | score_buro, tiene_seguro, patron_uso_atipico                                                                                                                                                                                                                                                                       | 3            | `hey_clientes`      |
| **Productos**          | num_productos_activos, tipo_producto (one-hot 11), utilizacion_pct_avg, saldo_actual_total, tasa_interes_promedio, plazo_meses_promedio, monto_mensualidad_total                                                                                                                                                   | ~20          | `hey_productos`     |
| **Transaccionales**    | frecuencia_total, frecuencia_por_categoria_mcc (one-hot 14), frecuencia_por_canal (one-hot 9), frecuencia_por_tipo_operacion (one-hot 13), monto_promedio, monto_total, hora_pico, dia_semana (one-hot 7), pct_internacional, cashback_total, intentos_promedio, pct_no_procesada, motivo_no_procesada (one-hot 8) | ~55          | `hey_transacciones` |
| **Conversacionales**   | num_conversaciones, msgs_promedio, pct_canal_voz, diversidad_interacciones                                                                                                                                                                                                                                         | 4            | Dataset Havi        |
| **Embeddings (Havi)** | Mean-pooled vector | 3072 | §3.1 |
| **Intenciones** | Conteo por intent (11), sentiment_avg (-1 a 1), urgency_avg, resolution_rate | 14 | §3.2 |
| **Enriquecimiento TX** | suscripciones_detectadas, comercio_top_freq, entropia_categorias | 3 | §3.3 |
| **Customer DNA** | Embedding del perfil narrativo | 3072 | §3.4 |

> **Total estimado**: ~6,200 columnas para ~15,000 usuarios.
> Los embeddings dominan dimensionalidad (>90% de features) — UMAP es crítico para reducción efectiva.

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
│ 5. ASIGNACIÓN DE RUIDO A CLUSTER CERCANO                     │
│    - KNN (k=5) desde puntos de ruido a centroides de cluster │
│    - Asignar al cluster del vecino más cercano si distancia  │
│      < percentil 95 de distancias intra-cluster              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 6. VALIDACIÓN                                                │
│    - DBCV (Density-Based Cluster Validation)                 │
│    - Silhouette Score (sobre UMAP embedding)                 │
│    - Estabilidad: correr con distintos random seeds          │
└──────────────────────────────────────────────────────────────┘
```

**Hyperparámetros a tunear**:

- `n_components` UMAP: probar [5, 8, 10, 15] — elegir el que maximice DBCV
- `min_cluster_size` HDBSCAN: probar [50, 100, 150, 200] — balance granularidad vs. interpretabilidad
- `metric` UMAP: probar `euclidean` vs. `cosine` para embeddings de alta dimensión

### 4.3 Perfilamiento de Segmentos (`src/models/segments.py`)

**Para cada segmento descubierto, computar**:

1. **Estadísticas descriptivas**: Media/mediana de features vs. población general (z-score de diferencia)
2. **Top features discriminantes**: SHAP o diferencia absoluta estandarizada
3. **LLM Labeling**: GPT-4.1 mini nombra y describe el segmento en lenguaje de negocio:

```
Describe este segmento de clientes de Hey Banco. Datos:
- Demografía: [edad_avg, genero_dist, ingreso_avg, ubicacion_top]
- Productos: [top 3 tipos, utilizacion_promedio, saldo_promedio]
- Transacciones: [categoria_top, monto_promedio, canal_preferido]
- Conversaciones: [intent_top, sentiment_avg, num_convs_promedio]

Genera:
- Nombre del segmento (ej: "Jóvenes Digitales Diversificados")
- Descripción de 3 oraciones
- Top 3 necesidades implícitas
- Recomendación de acción proactiva
```

4. **Mapeo a acciones proactivas** (según Presentacion.md):
   - **Ofertas segmentadas**: ¿qué producto complementario tiene mayor propensión?
   - **Alertas de cargos**: ¿segmento con alto `patron_uso_atipico`?
   - **Insights de gastos**: ¿categoría de gasto predominante del segmento?
   - **Promociones**: ¿producto con baja adopción vs. perfil del segmento?

**Output**: `data/processed/segment_profiles.json` + `data/processed/user_segments.parquet`.

---

## 5. Chatbot Agent Layer

> **Arquitectura**: RAG híbrido sobre datos del usuario + tool calling.
> **Modelo**: DeepSeek-V3.2 con streaming habilitado.
> **Framework**: `azure-ai-inference` SDK + Streamlit `st.write_stream()`.

### 5.1 Arquitectura del Agente

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHATBOT RAG AGENT                                │
│                                                                          │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────────┐  │
│  │ SYSTEM PROMPT│    │   CONTEXTO RAG   │    │     TOOL CALLING      │  │
│  │              │    │                  │    │                       │  │
│  │ Customer DNA │    │ • Perfil segmento│    │ ① get_account_summary │  │
│  │ narrativo    │    │ • Embeddings     │    │ ② get_recent_tx       │  │
│  │ (§3.4)       │    │   conversacional │    │ ③ get_recommendation  │  │
│  │              │    │ • Intenciones top│    │                       │  │
│  │ Voz: empático│    │ • Productos      │    │ Todas retornan datos  │  │
│  │ y proactivo  │    │   activos        │    │ del usuario autentic. │  │
│  └──────────────┘    └──────────────────┘    └───────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    STREAMING RESPONSE                             │   │
│  │  client.complete(                                                    │   │
│  │      model="DeepSeek-V3.2",                                          │   │
│  │      messages=[system, ...history, user_msg],                     │   │
│  │      tools=[account_summary, recent_tx, recommendation],          │   │
│  │      stream=True                                                  │   │
│  │  )                                                                │   │
│  │  → st.write_stream(response_chunks)                               │   │
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
    """
    Retorna el resumen de cuenta del usuario:
    - Productos activos con saldo/límite
    - Créditos con utilización, mensualidad
    - Inversiones con saldo
    - Seguros activos
    """
    return {
        "productos": [
            {"tipo": "cuenta_debito", "saldo": 12345.67},
            {"tipo": "tarjeta_credito_hey", "limite": 50000, "utilizado": 15000,
             "utilizacion_pct": 0.30, "pago_minimo": 750, "fecha_corte": "2026-05-15"},
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
    """
    Retorna las últimas N transacciones del usuario.
    """
    return {
        "transacciones": [
            {"fecha": "2026-04-20", "monto": 850.00,
             "comercio": "Superama", "categoria": "supermercado",
             "estatus": "completada", "cashback": 8.50},
            # ...
        ],
        "alerta": {
            "cargos_atipicos": True,
            "detalle": "2 cargos en categoría inusual (viajes) por $4,500"
        } if user_has_atypical else None,
    }
```

#### Tool 3: `get_recommendation(user_id: str)`

```python
def get_recommendation(user_id: str) -> dict:
    """
    Retorna recomendación personalizada según segmento y perfil.
    """
    return {
        "tipo": "oferta_segmentada",  # oferta_segmentada | alerta_cargos | insight_gastos | promocion
        "titulo": "Tu Hey Pro te da 5% extra en restaurantes este mes",
        "descripcion": "Como usuario Hey Pro, activa el beneficio de 5% cashback...",
        "accion": "Activar beneficio",
        "producto_relacionado": "tarjeta_credito_hey",
    }
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

### 5.5 Streaming en Streamlit

```python
# src/chatbot/agent.py
from openai import OpenAI

def chat_stream(user_id: str, messages: list, tools: list) -> Generator:
    """Generador de chunks para streaming en Streamlit."""
    client = OpenAI(
        base_url=os.environ["AZURE_CHAT_BASE_URL"],
        api_key=os.environ["AZURE_CHAT_API_KEY"],
    )

    response = client.chat.completions.create(
        model="DeepSeek-V3.2",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=True,
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# src/dashboard/app.py
import streamlit as st

def render_chat():
    st.write_stream(chat_stream(user_id, messages, tools))
```

---

## 6. Streamlit Dashboard

### 6.1 Páginas

```
🏠 Home / Overview
├── KPIs: Total usuarios, segmentos, NPS promedio, usuarios Hey Pro %
├── Métricas de conversaciones: total, resolución rate, sentimiento avg
├── Métricas transaccionales: volumen total, ticket promedio, % no procesadas
└── Distribución de segmentos (treemap)

🔍 Segment Explorer
├── UMAP 2D scatter plot (coloreado por segmento, interactivo con Plotly)
├── Tarjeta de segmento seleccionado:
│   ├── Nombre, descripción (LLM-generated)
│   ├── Tamaño (# usuarios, %)
│   ├── Top 10 features discriminantes (bar chart horizontal)
│   ├── Needs cloud (wordcloud de necesidades implícitas)
│   └── Acción proactiva recomendada
└── Tabla de usuarios del segmento con drill-down

👤 Customer 360
├── Selector de usuario (dropdown con búsqueda por user_id)
├── Ficha completa:
│   ├── Demografía (card con íconos)
│   ├── Productos (tabla con estatus, saldo, utilización)
│   ├── Transacciones recientes (tabla + gráfico de categorías)
│   ├── Conversaciones con Havi (timeline)
│   └── Customer DNA (texto narrativo)
├── Radar chart: perfil del usuario vs. promedio de su segmento
└── "¿Qué haría Havi por este cliente?" (recomendación generada)

💬 Havi Next (Chatbot)
├── Chat UI con historial de conversación
├── Selector de usuario (carga el contexto automáticamente)
├── Streaming en tiempo real
├── Tool calls visibles en UI colapsable (debug mode)
└── Acciones proactivas sugeridas (tarjetas clickeables)

📈 Analytics
├── Patrones transaccionales:
│   ├── Heatmap hora × día de la semana
│   ├── Sankey diagram: categoría MCC → tipo operación → estatus
│   └── Treemap de comercios top
├── Conversaciones:
│   ├── Distribución de intenciones (sunburst)
│   ├── Sentiment trend (línea de tiempo)
│   └── Funnel: consulta → resuelto vs. escalado
└── Cohortes:
    ├── Usuarios por antigüedad vs. engagement
    └── Matriz de adopción de productos
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

| Vista                 | Librería         | Interactividad                     |
| --------------------- | ---------------- | ---------------------------------- |
| UMAP 2D Scatter       | Plotly Express   | Hover con user_id, zoom, selección |
| Segment Treemap       | Plotly           | Click → drill-down                 |
| Feature Importance    | Altair           | Bar chart con tooltip              |
| Transacciones Heatmap | Plotly           | Hora × Día, escala de color monto  |
| Sankey (Categorías)   | Plotly           | Nodes arrastrables                 |
| Sentiment Timeline    | Altair           | Línea con banda de confianza       |
| Radar Chart (360)     | Plotly           | Overlay usuario vs. segmento       |
| Chat UI               | Streamlit nativo | `st.chat_input`, `st.chat_message` |

---

## 7. Infraestructura & DevOps

### 7.1 Stack Tecnológico

| Capa                    | Tecnología                        | Versión       | Justificación                                                  |
| ----------------------- | --------------------------------- | ------------- | -------------------------------------------------------------- |
| **Lenguaje**            | Python                            | 3.11+         | Requisito del equipo                                           |
| **DataFrames**          | Polars + Pandas                   | latest        | Polars para ETL pesado, Pandas para compatibilidad con sklearn |
| **ML**                  | scikit-learn, UMAP-learn, HDBSCAN | latest        | Ligero, sin GPU necesaria                                      |
| **LLM** | Azure AI Foundry + Azure OpenAI | DeepSeek-V3.2 + text-embedding-3-large | Student plan, serverless + managed endpoint |
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
  .env
  data/raw/
  data/processed/
  data/*.db
  __pycache__/
  .venv/
  *.pyc

.env (nunca commiteado):
  AZURE_CHAT_API_KEY=...
  AZURE_CHAT_BASE_URL=https://<resource>.services.ai.azure.com/openai/v1/
  AZURE_CHAT_MODEL=DeepSeek-V3.2
  AZURE_EMBEDDING_API_KEY=...
  AZURE_EMBEDDING_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
  AZURE_EMBEDDING_MODEL=text-embedding-3-large
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

# Utils
python-dotenv>=1.0
pyarrow>=14.0
joblib>=1.3

# Pipeline (opcional futuro)
prefect>=2.0
```

### 7.5 Makefile

```makefile
.PHONY: validate enrich features cluster dashboard all clean

# Data
validate:
	python src/data/validate.py

# Enrichment (4 etapas, secuenciales pero con cache)
enrich:
	python src/enrichment/embeddings.py
	python src/enrichment/intents.py
	python src/enrichment/descriptions.py
	python src/enrichment/customer_dna.py

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
def run_embeddings(input_path: str, output_path: str) -> None:
    """Genera embeddings conversacionales por usuario."""
    ...

if __name__ == "__main__":
    run_embeddings("data/raw/", "data/processed/user_embeddings.parquet")
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
├── .env.example                  # Template de variables de entorno
├── .gitignore                    # Excluye .env, data/, __pycache__
├── Makefile                      # Orquestación secuencial
├── requirements.txt              # Dependencias
├── README.md                     # Setup y ejecución
│
├── Arquitectura.md               # Este documento
├── Presentacion.md               # Brief original del reto
│
├── data/                         # Gitignored
│   ├── raw/                      # Datasets originales
│   │   ├── hey_clientes.csv
│   │   ├── hey_productos.csv
│   │   ├── hey_transacciones.csv
│   │   └── dataset_50k_anonymized.parquet
│   └── processed/                # Datasets enriquecidos (generados)
│       ├── user_embeddings.parquet
│       ├── conv_intents.parquet
│       ├── user_intents.parquet
│       ├── tx_enriched.parquet
│       ├── customer_dna.parquet
│       ├── feature_matrix.parquet
│       ├── user_segments.parquet
│       └── segment_profiles.json
│
├── docs/
│   ├── diccionario_datos_transacciones.md
│   └── diccionario_datos_conversaciones.md
│
├── notebooks/
│   ├── 01_exploracion_clientes.ipynb
│   ├── 02_exploracion_transacciones.ipynb
│   ├── 03_exploracion_conversaciones.ipynb
│   └── 04_prototipo_clustering.ipynb
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── validate.py            # Validación de schemas
│   │   └── ingest.py              # Carga y joins iniciales
│   │
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── embeddings.py          # §3.1 Embeddings conversacionales
│   │   ├── intents.py             # §3.2 Extracción de intenciones
│   │   ├── descriptions.py        # §3.3 Normalización descripciones
│   │   ├── customer_dna.py        # §3.4 Customer DNA narrativo
│   │   └── llm_client.py          # Cliente Azure OpenAI compartido
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   └── build_matrix.py        # Construcción de feature matrix
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cluster.py             # UMAP + HDBSCAN pipeline
│   │   └── segments.py            # Perfilamiento y labeling
│   │
│   ├── chatbot/
│   │   ├── __init__.py
│   │   ├── agent.py               # Chatbot RAG con tool calling
│   │   └── tools.py               # Implementación de 3 herramientas
│   │
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py                 # Entry point Streamlit
│       ├── pages/
│       │   ├── __init__.py
│       │   ├── home.py
│       │   ├── segments.py
│       │   ├── customer_360.py
│       │   ├── chatbot.py
│       │   └── analytics.py
│       ├── components/
│       │   ├── __init__.py
│       │   ├── charts.py
│       │   ├── cards.py
│       │   └── chatbot_ui.py
│       └── utils/
│           ├── __init__.py
│           ├── data_loader.py
│           └── styling.py
```

---

## 9. Plan de Implementación

### Fases y Duración Estimada

| Fase       | Descripción               | Duración | Dependencias |
| ---------- | ------------------------- | -------- | ------------ |
| **Fase 1** | Data prep & validación    | ~1.5h    | —            |
| **Fase 2** | Enrichment batch (LLM)    | ~3h      | Fase 1       |
| **Fase 3** | Feature engineering       | ~1h      | Fase 2       |
| **Fase 4** | Clustering & segmentación | ~2h      | Fase 3       |
| **Fase 5** | Streamlit dashboard       | ~3h      | Fase 4       |
| **Fase 6** | Chatbot streaming RAG     | ~3h      | Fase 4       |
| **Fase 7** | Pitch deck & ensayo       | ~2h      | Fase 5+6     |
| **Fase 8** | Makefile + polish         | ~0.5h    | Fase 5+6     |
| _(Opc.)_   | Migrar a Prefect          | ~1h      | Fase 8       |

### Detalle por Fase

#### Fase 1: Data Prep & Validación

- [ ] Leer datasets en Polars/Pandas
- [ ] Validar schemas contra diccionario de datos
- [ ] Chequear nulls, rangos, FK integrity, duplicados
- [ ] Cruce de `user_id` entre datasets (¿cuántos matchean?)
- [ ] Estadísticas descriptivas básicas para notebook de exploración
- [ ] Guardar datasets limpios en `data/processed/`

#### Fase 2: Enrichment Batch (LLM)

- [ ] Configurar cliente Azure OpenAI (`src/enrichment/llm_client.py`)
- [ ] Embeddings: vectorizar ~50K inputs de Havi, mean-pool por usuario
- [ ] Intenciones: clasificar 24K conversaciones en batch (50 por llamada)
- [ ] Descripciones: normalizar `descripcion_libre` de transacciones
- [ ] Customer DNA: generar perfil narrativo para ~15K usuarios
- [ ] Verificar consumo de tokens acumulado contra presupuesto $20

#### Fase 3: Feature Engineering

- [ ] Join de todas las features por `user_id`
- [ ] Manejo de usuarios sin conversaciones (imputación por cero)
- [ ] One-hot encoding para categóricas
- [ ] Agregaciones transaccionales (frecuencia, montos, categorías)
- [ ] Feature matrix final → `data/processed/feature_matrix.parquet`

#### Fase 4: Clustering & Segmentación

- [ ] KNN Imputer + StandardScaler
- [ ] UMAP reducción a 8 dimensiones
- [ ] HDBSCAN clustering con hyperparameter search
- [ ] Asignación de ruido a clusters cercanos
- [ ] Validación (DBCV, Silhouette)
- [ ] LLM labeling de segmentos
- [ ] Perfiles de segmento con acciones proactivas

#### Fase 5: Streamlit Dashboard

- [ ] Configurar `st.navigation` con 5 páginas
- [ ] Home: KPIs y métricas
- [ ] Segment Explorer: UMAP scatter + perfil
- [ ] Customer 360: ficha completa + recomendación
- [ ] Analytics: heatmaps, sankey, trends
- [ ] Chatbot page (placeholder, se llena en Fase 6)

#### Fase 6: Chatbot Streaming RAG

- [ ] Implementar 3 herramientas: `get_account_summary`, `get_recent_transactions`, `get_recommendation`
- [ ] Construir Contexto RAG: embeddings + segmento + productos
- [ ] Integrar Customer DNA como system prompt
- [ ] Configurar streaming con `st.write_stream()`
- [ ] UI de chat con tool calls visibles
- [ ] Pruebas de conversación con 5 usuarios de distintos segmentos

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

## 10. Estimación de Costos (Azure AI Foundry)

### DeepSeek-V3.2 + text-embedding-3-small Pricing (Azure AI Foundry)

| Modelo                 | Input (por 1M tokens) | Output (por 1M tokens) |
| ---------------------- | --------------------- | ---------------------- |
| DeepSeek-V3.2              | $0.27                 | $1.10                  |
| text-embedding-3-large     | $0.13                 | —                      |

### Estimación por Tarea

| Tarea                                        | Tokens In (M) | Tokens Out (M)    | Costo      |
| -------------------------------------------- | ------------- | ----------------- | ---------- |
| Embeddings conversacionales                  | 10.0          | — (embedding API) | **$0.20**  |
| Intenciones (24K conv × batch 50)            | 12.0          | 3.0               | **$6.54**  |
| Descripciones (batch 100)                    | 5.0           | 2.0               | **$3.55**  |
| Customer DNA (15K users × batch 25)          | 7.5           | 3.0               | **$5.33**  |
| Chatbot demo (streaming, ~100 interacciones) | 0.5           | 0.5               | **$0.69**  |
| Segment labeling (LLM, ~10 segmentos)        | 0.05          | 0.02              | **$0.04**  |
| **TOTAL**                                    | **35.05**     | **8.52**          | **$17.45** |

> ✅ **Con DeepSeek-V3.2 + text-embedding-3-large, el costo total estimado es $17.45 USD — dentro del presupuesto de $20 sin necesidad de mitigación.**

### Estrategias de Mitigación de Costos (opcional)

| Estrategia                                                                                                                                                   | Ahorro Est. | Prioridad       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | --------------- |
| **Reducir batch de intenciones**: solo conversaciones > 2 interacciones (~9K en vez de 24K). Conversaciones de 1 mensaje se clasifican con reglas (sin LLM). | ~$3.90      | Media           |
| **Sampling para embedding**: si hay conversaciones repetitivas (~15K single-interaction), muestrear al 50%.                                                  | ~$0.10      | Baja            |
| **Customer DNA solo para usuarios con ≥3 conversaciones**: reduce de 15K a ~7K usuarios activos.                                                             | ~$2.50      | Media           |
| **DeepSeek-V3.2 es ~33% más barato que GPT-4.1 mini en input y ~31% en output**. El costo ya está dentro del presupuesto.                                    | —           | —               |
| **Priorizar intenciones y customer DNA**. Si sobra presupuesto, hacer descripciones. Si no, descripciones con reglas (str.contains).                         | ~$3.55      | Baja (fallback) |

### Plan de Ejecución con Presupuesto Controlado

```
Orden de ejecución para control de gasto:

1. Embeddings      → $1.30  ✅ Siempre
2. Intenciones     → $6.54  ✅ (conversaciones completas: 24K)
3. Customer DNA    → $5.33  ✅ (usuarios completos: 15K)
4. Segment Labeling → $0.04  ✅ Siempre
5. Chatbot demo    → $0.69  ✅ Siempre
───────────────────────────────────────
   Subtotal        → $13.90  ← Dentro de $20 ✅

6. Descripciones   → $3.55  ✅ Dentro del presupuesto
───────────────────────────────────────
   Total           → $17.45  ← Holgado dentro de $20
```

> Con la estrategia de mitigación opcional, el costo puede bajar aún más de ser necesario.

---

## 11. Alineación con Rúbrica de Evaluación

| Criterio                        | Peso | Cómo lo cubrimos                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Objetivos y Alcance**         | 15%  | • Definición clara de clases: segmentos descubiertos por aprendizaje no supervisado (HDBSCAN) con features enriquecidas por LLM<br>• Esquema de evaluación no supervisado: DBCV + Silhouette + estabilidad cross-run<br>• Plan de acción: 4 tipos de automatización proactiva (ofertas, alertas, insights, promociones) mapeadas a cada segmento |
| **Innovación y Creatividad**    | 35%  | • Customer DNA: perfil narrativo generado por LLM como system prompt del chatbot<br>• 4 técnicas de enriquecimiento LLM combinadas (embeddings + intenciones + descripciones + DNA)<br>• RAG híbrido con tool calling (3 herramientas) y streaming en tiempo real<br>• Segment labeling automatizado con LLM (no manual)                         |
| **Impacto y Viabilidad**        | 35%  | • Costo total <$14 (presupuesto $20)<br>• Escalable a millones de usuarios (batching, FAISS, arquitectura modular)<br>• Sin vendor lock-in: Azure OpenAI es el único servicio externo, reemplazable por open-source (ej. Llama 3)<br>• Impacto medible: métricas de experiencia de cliente (NPS, resolution rate, churn risk)                    |
| **Presentación y Comunicación** | 15%  | • Dashboard Streamlit interactivo con 5 vistas<br>• Chatbot con streaming en tiempo real → demo funcional<br>• Customer 360 con ficha completa y recomendaciones<br>• Storytelling: del dato crudo a la acción proactiva personalizada                                                                                                           |

---

## 12. Decisiones de Arquitectura

### Decisiones Clave

| #   | Decisión                                                                | Alternativas Consideradas                                      | Justificación                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **DeepSeek-V3.2** sobre GPT-4.1 mini | GPT-4.1 mini, GPT-4o, Claude 3.5 Sonnet, Llama 3 | ~33% más barato en input, ~31% en output. Disponible en Azure AI Foundry como serverless OpenAI-compatible. Tool calling y JSON structured output nativos. Costo total estimado $17.45 (dentro de $20). |
| 2   | **HDBSCAN** sobre KMeans                                                | KMeans, Gaussian Mixture, DBSCAN, Agglomerative                | HDBSCAN descubre número de clusters automáticamente, maneja ruido, no asume formas esféricas ni gaussianas. KMeans requeriría asumir K a priori.                                   |
| 3   | **UMAP** sobre PCA/t-SNE                                                | PCA, t-SNE, PaCMAP                                             | UMAP preserva estructura global y local, escala a alta dimensionalidad (embeddings 1536-dim), más rápido que t-SNE.                                                                |
| 4   | **Feature Matrix 220-column** sobre Autoencoders                        | Autoencoders, VAE, Deep Clustering                             | Interpretabilidad: cada feature tiene nombre y significado de negocio. Autoencoders son caja negra. El volumen (15K × 220) es manejable sin GPU.                                   |
| 5   | **FAISS in-memory** sobre Pinecone/Weaviate                             | Pinecone, Weaviate, ChromaDB                                   | 15K vectores caben en RAM (~100MB). FAISS sin servidor, sin costo, sin latencia de red. Self-contained.                                                                            |
| 6 | **Tool Calling nativo (openai SDK)** sobre LangChain/LlamaIndex | LangChain Agents, LlamaIndex, CrewAI | Zero-dependency adicional. OpenAI SDK nativo maneja tool calling desde v1.0. Menos abstracción → más control sobre streaming y costos. DeepSeek expone endpoint OpenAI-compatible. |
| 7   | **Makefile** sobre Airflow/Prefect (inicial)                            | Prefect, Airflow, Dagster                                      | Makefile es zero-config. Scripts ya están diseñados para migrar a Prefect (funciones puras con entrada/salida clara).                                                              |
| 8   | **SQLite + Parquet** sobre PostgreSQL/Blob                              | PostgreSQL, Azure Blob, MongoDB                                | Volumen pequeño (~200MB). Auto-contenido, sin servidor, portable. Parquet para DataFrames, SQLite para consultas rápidas desde Streamlit.                                          |
| 9   | **Polars para ETL** sobre Pandas-only                                   | Pandas solo                                                    | Polars es lazy, multithreaded por defecto, más eficiente en memoria. Pandas para compatibilidad con sklearn/umap.                                                                  |
| 10  | **Streamlit local** sobre Community Cloud                               | Streamlit Cloud, Gradio, Dash                                  | Requisito explícito. Ejecución local elimina exposición de keys Azure. Streamlit tiene streaming nativo (`st.write_stream`).                                                       |

### Trade-offs Aceptados

| Trade-off                                                                                                                             | Impacto                                                    | Mitigación                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **GPT-4.1 mini puede tener menor precisión que GPT-4o en intenciones** → DeepSeek-V3.2 puede tener precisión diferente en intenciones | Clasificación de intenciones puede tener ~85-90% accuracy. | Batch más grande (50 convs) incluye ejemplos en prompt. Si accuracy baja, agregar few-shot examples.                              |
| **HDBSCAN deja usuarios como ruido (cluster -1)**                                                                                     | ~13% de usuarios no asignados a segmento                   | Reasignación por KNN al cluster más cercano con umbral de distancia.                                                              |
| **UMAP no-determinístico**                                                                                                            | Clusters pueden variar entre ejecuciones                   | Fijar `random_state=117`. Validar estabilidad con 5 seeds diferentes.                                                             |
| **Customer DNA generado por LLM puede alucinar** → DeepSeek-V3.2 también puede alucinar                                               | Perfiles imprecisos afectan personalización del chatbot    | Data grounding: el prompt solo incluye datos factuales del dataset. Validar que el perfil no invente productos o comportamientos. |
| **Streamlit local = no compartir dashboard fácilmente**                                                                               | Solo visible en la máquina del equipo                      | Grabación de demo para el pitch. Compartir pantalla en presentación.                                                              |

---

## Apéndice A: Referencia Rápida de Comandos

```bash
# Setup inicial
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Editar con keys de Azure

# Pipeline completo
make all

# Etapas individuales
make validate    # Validación de datos
make enrich      # Enrichment LLM (4 módulos)
make features    # Feature matrix
make cluster     # UMAP + HDBSCAN
make dashboard   # Streamlit

# Chatbot demo
python src/chatbot/agent.py --user USR-00042

# Limpieza
make clean
```

---

## Apéndice B: Glosario

| Término          | Definición                                                                                                                                                           |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Customer DNA** | Perfil narrativo generado por LLM que describe necesidades implícitas, comportamiento financiero y oportunidades de atención proactiva de un cliente.                |
| **Embedding**    | Representación vectorial densa de texto (1536 dimensiones) que captura semántica. Generado con `text-embedding-3-small`.                                             |
| **HDBSCAN**      | Hierarchical Density-Based Spatial Clustering of Applications with Noise. Algoritmo de clustering que descubre automáticamente el número de clusters y maneja ruido. |
| **RAG**          | Retrieval-Augmented Generation. El chatbot recupera datos del usuario (productos, transacciones, perfil) antes de generar la respuesta.                              |
| **Tool Calling** | Capacidad del LLM de invocar funciones externas (herramientas) para obtener datos que no están en su contexto.                                                       |
| **UMAP**         | Uniform Manifold Approximation and Projection. Algoritmo de reducción de dimensionalidad que preserva estructura local y global.                                     |
| **MCC**          | Merchant Category Code. Código que clasifica el giro comercial de un establecimiento.                                                                                |
| **NPS**          | Net Promoter Score. Métrica de satisfacción del cliente (escala 1-10).                                                                                               |
| **SPEI**         | Sistema de Pagos Electrónicos Interbancarios. Sistema de transferencias del Banco de México.                                                                         |
| **CoDi**         | Cobro Digital. Plataforma de pagos móviles de Banxico mediante QR.                                                                                                   |
| **GAT**          | Ganancia Anual Total. Rendimiento de productos de inversión.                                                                                                         |

---

_Documento de arquitectura — DatathonTec 2026 · Hey Banco · Versión 1.0_
