# Stack Tecnológico

## Frontend

| Nombre | Versión | Uso |
|--------|---------|-----|
| Streamlit | ≥1.28 | Dashboard interactivo con soporte nativo de streaming |
| Plotly | ≥5.15 | Visualizaciones interactivas (scatter UMAP, treemap, heatmap, sankey) |
| Altair | ≥5.0 | Gráficos estadísticos declarativos (feature importance, sentiment timeline) |

## Backend

| Nombre | Versión | Uso |
|--------|---------|-----|
| Python | 3.11+ | Lenguaje principal del proyecto |
| Pandas | ≥2.0 | Manipulación de DataFrames, compatibilidad con scikit-learn |
| Polars | ≥0.20 | ETL de alto rendimiento multithreaded nativo |
| NumPy | ≥1.24 | Operaciones numéricas vectorizadas |
| scikit-learn | ≥1.3 | Preprocesamiento (StandardScaler, KNN Imputer), validación (Silhouette) |
| UMAP-learn | ≥0.5 | Reducción de dimensionalidad preservando estructura local/global |
| HDBSCAN | ≥0.8 | Clustering no supervisado basado en densidad |
| SHAP | ≥0.42 | Interpretabilidad de features discriminantes por segmento |
| openai | ≥1.0 | SDK de Azure OpenAI (chat, embeddings, streaming, tool calling) |
| tiktoken | ≥0.5 | Estimación de tokens para control de costos |
| FAISS-cpu | ≥1.7 | Vector store in-memory para búsqueda semántica RAG |
| pyarrow | ≥14.0 | Lectura/escritura de Parquet comprimido |
| joblib | ≥1.3 | Serialización eficiente de modelos entrenados |
| python-dotenv | ≥1.0 | Carga de variables de entorno desde .env |

## Base de datos

| Nombre | Versión | Uso |
|--------|---------|-----|
| SQLite | built-in | Feature store local para consultas desde Streamlit |
| Parquet (pyarrow) | ≥14.0 | Almacenamiento columnar comprimido para datasets enriquecidos |

## Infraestructura / DevOps

| Nombre | Versión | Uso |
|--------|---------|-----|
| Azure OpenAI | — | Servicio cloud para GPT-4.1 mini y text-embedding-3-small |
| text-embedding-3-small | — | Modelo de embeddings semánticos (1536 dimensiones) |
| Azure Blob Storage | — | Backup opcional de datasets (5GB LRS hot gratis) |
| Makefile | — | Orquestación secuencial del pipeline (6 targets) |
| Prefect | ≥2.0 | Framework de orquestación preparado para migración futura |

## Herramientas de desarrollo

| Nombre | Versión | Uso |
|--------|---------|-----|
| venv | — | Entorno virtual aislado de Python |
| pip-tools | — | Gestión de dependencias reproducible con requirements.txt |
