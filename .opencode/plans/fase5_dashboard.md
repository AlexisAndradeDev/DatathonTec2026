# Plan Fase 5 — Streamlit Dashboard + Chatbot RAG · Hey Banco

## Estructura de archivos

```
src/dashboard/
├── app.py                  ← Entry point: st.navigation con 5 páginas + tema Hey Banco
├── pages/
│   ├── home.py             ← KPIs, métricas, treemap
│   ├── segments.py         ← UMAP 2D scatter + perfil de segmento
│   ├── customer_360.py     ← Ficha usuario + radar chart + DNA
│   ├── chatbot.py          ← Havi Next (chatbot streaming + RAG)
│   └── analytics.py        ← Heatmap, Sankey, funnel, cohortes
├── components/
│   ├── charts.py           ← Wrappers Plotly/Altair reutilizables
│   ├── cards.py            ← KPI cards estilizadas
│   └── chatbot_ui.py       ← Chat UI con tool calls colapsables
├── utils/
│   ├── data_loader.py      ← Carga cacheada desde Parquet/SQLite
│   └── styling.py          ← CSS + theme_config Hey Banco
└── assets/
    └── logo.png            ← Logo Hey Banco (opcional, o texto como marca)
```

## Tema Hey Banco

### Elementos de diseño

| Elemento | Descripción |
|----------|-------------|
| Color primario | Teal/verde-azulado característico de Hey Banco |
| Fondo sidebar | Azul oscuro |
| Fondo principal | Gris claro |
| Texto | Casi negro |
| Acentos | Naranja para alertas, Verde para cashback |
| Fuente | Inter, fallback sans-serif |
| Cards | Fondo blanco, sombra suave, border-radius 12px |
| Métricas KPI | Número grande, label pequeño |

### Implementación en `styling.py`

```python
# CSS customizado que se inyecta con st.markdown(..., unsafe_allow_html=True)
# + st.set_page_config(page_title="Hey Banco | Havi Motor", 
#                       page_icon="...", layout="wide")
```

## Páginas

### 1. Home (`pages/home.py`)

```
┌─────────────────────────────────────────────────────────┐
│  [KPI] 15,025    [KPI] 15        [KPI] 7.4/10   [KPI] 37% │
│  Usuarios       Segmentos       Satisfacción    Hey Pro   │
├─────────────────────────────────────────────────────────┤
│  Distribución de Segmentos (Treemap Plotly)              │
│  [Cluster 2: 3,179] [Cluster 8: 2,031] ...              │
├─────────────────────────────────────────────────────────┤
│  Métricas Transaccionales        │  Métricas Havi        │
│  Volumen total: $XX M            │  Total convs: 50K     │
│  Ticket promedio: $X,XXX         │  Resolution rate: XX% │
│  % No procesadas: X.X%           │  Sentiment avg: X.XX  │
└─────────────────────────────────────────────────────────┘
```

KPIs:
- Total usuarios, segmentos, NPS promedio, usuarios Hey Pro %
- Métricas conversacionales: total, resolución rate, sentimiento avg
- Métricas transaccionales: volumen total, ticket promedio, % no procesadas
- Distribución de segmentos (treemap Plotly)

### 2. Segment Explorer (`pages/segments.py`)

```
┌─────────────────────────────────────────────────────────┐
│  Selector: [Dropdown: elegir segmento]                  │
├──────────────────────┬──────────────────────────────────┤
│ UMAP 2D Scatter      │ Tarjeta de Segmento              │
│ (Plotly, coloreado   │ Nombre: "Jóvenes Pro Digitales" │
│  por cluster, hover  │ Tamaño: 1,318 (8.8%)            │
│  con user_id)        │ Descripción: ...                 │
│                      │ Top 10 Features (Altair bar)     │
│                      │ Necesidades (lista)              │
│                      │ Acción proactiva (badge)         │
│                      │                                  │
│                      │ Tabla: usuarios del segmento     │
└──────────────────────┴──────────────────────────────────┘
```

Elementos:
- UMAP 2D scatter plot, coloreado por segmento, interactivo con Plotly (hover con user_id, zoom, selección)
- Tarjeta de segmento: nombre, descripción, tamaño, %
- Top 10 features discriminantes (bar chart horizontal Altair)
- Necesidades (lista)
- Acción proactiva recomendada
- Tabla de usuarios del segmento con drill-down

### 3. Customer 360 (`pages/customer_360.py`)

```
┌─────────────────────────────────────────────────────────┐
│  Selector de usuario: [Dropdown USR-XXXXX con búsqueda] │
├─────────────┬─────────────┬──────────────────────────────┤
│ Demografía  │ Productos   │ Transacciones recientes      │
│ (card)      │ (tabla)     │ (tabla + gráfico categorías) │
├─────────────┴─────────────┼──────────────────────────────┤
│ Customer DNA (texto)      │ Radar Chart: usuario vs      │
│                           │ promedio de su segmento       │
├───────────────────────────┴──────────────────────────────┤
│  "¿Qué haría Havi por este cliente?" (recomendación)     │
└──────────────────────────────────────────────────────────┘
```

Elementos:
- Selector de usuario (dropdown con búsqueda por user_id)
- Ficha completa: demografía (card), productos (tabla con estatus/saldo/utilización), transacciones recientes (tabla + gráfico de categorías), conversaciones con Havi (timeline), Customer DNA (texto narrativo)
- Radar chart: perfil del usuario vs. promedio de su segmento (Plotly)
- "¿Qué haría Havi por este cliente?" (recomendación generada)

### 4. Havi Next — Chatbot (`pages/chatbot.py` + `components/chatbot_ui.py`)

```
┌─────────────────────────────────────────────────────────┐
│  Selector de usuario: [Dropdown]                         │
│  ── Carga: Customer DNA como system prompt ──           │
├─────────────────────────────────────────────────────────┤
│  Chat UI (st.chat_message)                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Havi: ¡Hola! Soy tu asistente Hey Banco.        │    │
│  │       ¿En qué puedo ayudarte hoy?               │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ User: ¿Cuánto debo en mi tarjeta de crédito?    │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Havi: [streaming real-time con                 │    │
│  │        st.write_stream()]                       │    │
│  │                                                │    │
│  │  🔧 Tool: get_account_summary (colapsable)     │    │
│  │  │ user_id: USR-00042                         │    │
│  │  │ → cuenta_debito: $12,345...                │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  [st.chat_input "Escribe tu mensaje..."]                │
│                                                         │
│  Acciones sugeridas: [💰 Ver saldo] [📊 Últimos gastos] │
└─────────────────────────────────────────────────────────┘
```

Elementos:
- Chat UI con historial de conversación
- Selector de usuario (carga el contexto automáticamente: DNA como system prompt)
- Streaming en tiempo real con `st.write_stream()`
- Tool calls visibles en UI colapsable (debug mode)
- Acciones proactivas sugeridas (tarjetas clickeables)
- 3 herramientas integradas:
  - `get_account_summary(user_id)` → productos, saldos, créditos, inversiones, seguros
  - `get_recent_transactions(user_id, n=5)` → últimas N transacciones + alerta cargos atípicos
  - `get_recommendation(user_id)` → recomendación personalizada según segmento

### 5. Analytics (`pages/analytics.py`)

```
┌─────────────────────────────────────────────────────────┐
│  Heatmap: Hora × Día de la semana (Plotly)              │
├─────────────────────────────────────────────────────────┤
│  Sankey: Categoría MCC → Tipo operación → Estatus       │
├──────────────────────────┬──────────────────────────────┤
│  Sunburst: Intenciones   │ Sentiment trend (Altair)    │
├──────────────────────────┴──────────────────────────────┤
│  Cohortes: Antigüedad vs Engagement / Adopción productos│
└─────────────────────────────────────────────────────────┘
```

Elementos:
- Heatmap hora × día de la semana (Plotly, escala de color monto)
- Sankey diagram: categoría MCC → tipo operación → estatus (Plotly, nodes arrastrables)
- Distribución de intenciones (sunburst Plotly)
- Sentiment trend (línea de tiempo Altair con banda de confianza)
- Funnel: consulta → resuelto vs. escalado
- Cohortes: usuarios por antigüedad vs. engagement, matriz de adopción de productos

## Data Layer (`utils/data_loader.py`)

```python
@st.cache_data
def load_clients() → DataFrame
def load_segments() → DataFrame  
def load_profiles() → list[dict]
def load_customer_dna() → DataFrame
def load_transactions(n=10000) → DataFrame
def load_feature_matrix_cols(cols) → DataFrame
def load_havi_messages() → DataFrame
```

Cacheado con `@st.cache_data` para no recargar en cada interacción del dashboard.

## Visualizaciones Clave

| Vista | Librería | Interactividad |
|-------|----------|----------------|
| UMAP 2D Scatter | Plotly Express | Hover con user_id, zoom, selección |
| Segment Treemap | Plotly | Click → drill-down |
| Feature Importance | Altair | Bar chart con tooltip |
| Transacciones Heatmap | Plotly | Hora × Día, escala de color monto |
| Sankey (Categorías) | Plotly | Nodes arrastrables |
| Sentiment Timeline | Altair | Línea con banda de confianza |
| Radar Chart (360) | Plotly | Overlay usuario vs. segmento |
| Sunburst (Intenciones) | Plotly | Hover con detalle |
| Chat UI | Streamlit nativo | `st.chat_input`, `st.chat_message` |

## Orden de implementación

| # | Archivo | Dependencias | Complejidad |
|---|---------|-------------|-------------|
| 1 | `utils/styling.py` | Ninguna | Baja |
| 2 | `utils/data_loader.py` | styling | Media |
| 3 | `components/cards.py` | styling | Baja |
| 4 | `components/charts.py` | data_loader | Media |
| 5 | `app.py` | styling | Baja |
| 6 | `pages/home.py` | cards, data_loader | Media |
| 7 | `pages/segments.py` | charts, data_loader | Alta |
| 8 | `pages/customer_360.py` | charts, data_loader | Alta |
| 9 | `pages/analytics.py` | charts, data_loader | Alta |
| 10 | `chatbot/tools.py` (implementar) | data_loader | Media |
| 11 | `chatbot/agent.py` (mejorar tool calling) | tools, llm_client | Media |
| 12 | `components/chatbot_ui.py` | agent, styling | Alta |
| 13 | `pages/chatbot.py` | chatbot_ui, data_loader | Alta |
