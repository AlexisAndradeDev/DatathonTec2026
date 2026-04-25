# AGENTS.md — DatathonTec 2026 · Hey Banco

## Project

Motor de Inteligencia & Atención Personalizada: pipeline de IA para integrar logs conversacionales + registros transaccionales, segmentación no supervisada, y chatbot RAG con streaming.

**Current phase**: implementation — skeleton created, enrichment + chatbot pending.

## Key References

- `Arquitectura.md` — master architecture (12 sections). Read first for any implementation task.
- `stack.md` — technology stack with versions and purpose per technology.
- `docs/Presentacion.md` — original challenge brief and rubric.
- `docs/diccionario_datos_transacciones.md` — schema for clients, products, transactions CSVs.
- `docs/diccionario_datos_conversaciones.md` — schema for Havi conversation logs (Parquet).

## Hard Constraints

- **$20 USD max budget** for Azure AI Foundry API calls.
- **Azure for Students** — services: Azure AI Foundry (DeepSeek-V3.2 serverless) + Azure OpenAI (text-embedding-3-large).
- **DeepSeek-V3.2** is the chosen chat model. **text-embedding-3-large** for embeddings (3072 dimensions).
- **Streamlit runs local** — never deploy to Community Cloud, keys never leave the machine.
- **Secrets in `.env`** — `AZURE_CHAT_API_KEY`, `AZURE_CHAT_BASE_URL`, `AZURE_CHAT_MODEL`, `AZURE_EMBEDDING_API_KEY`, `AZURE_EMBEDDING_ENDPOINT`, `AZURE_EMBEDDING_MODEL`.
- **Data is 100% synthetic** — academic sandbox, no regulatory restrictions (CNBV, LFPDPPP).

## Architecture decisions (from Arquitectura.md §12)

| Decision      | Chosen                                   | Rejected               |
| ------------- | ---------------------------------------- | ---------------------- |
| LLM model     | DeepSeek-V3.2                            | GPT-4o, Claude, GPT-4.1 mini |
| Clustering    | HDBSCAN                                  | KMeans, GMM            |
| Dim reduction | UMAP                                     | PCA, t-SNE             |
| Vector store  | FAISS in-memory                          | Pinecone, Weaviate     |
| Tool calling  | openai SDK native                        | LangChain, LlamaIndex  |
| Pipeline      | Makefile → Prefect-ready                 | Airflow, Dagster       |
| Storage       | SQLite + Parquet                         | PostgreSQL, Azure Blob |
| ETL           | Polars (heavy) + Pandas (sklearn compat) | Pandas-only            |

## Planned repo structure (not yet created)

```
src/data/          — validate.py, ingest.py
src/enrichment/    — embeddings.py, intents.py, descriptions.py, customer_dna.py, llm_client.py
src/features/      — build_matrix.py
src/models/        — cluster.py, segments.py
src/chatbot/       — agent.py, tools.py
src/dashboard/     — app.py, pages/*, components/*, utils/*
data/raw/          — datasets (gitignored)
data/processed/    — enriched outputs (gitignored)
notebooks/         — exploration
```

## 4 enrichment techniques (sequential, budget-controlled)

1. Embeddings () — `text-embedding-3-large` (3072 dims), mean-pool per user (~$1.30)
2. Intent extraction — classify conversations with structured JSON output (~$3.60)
3. Description normalization — extract structured info from free-text transaction descriptions (~$3.55)
4. Customer DNA — narrative profile per customer, used as chatbot system prompt (~$5.33)

Budget control: prioritize 1→2→4. Run 3 only if budget remains (or fallback to regex rules).

## Chatbot architecture

- RAG hybrid + tool calling (openai SDK native, no extra frameworks)
- 3 tools: `get_account_summary`, `get_recent_transactions`, `get_recommendation`
- System prompt = Customer DNA narrative (§3.4)
- Streaming via `st.write_stream()`
- Streamlit UI with collapsible tool call visibility (debug mode)

## Pipeline commands (planned Makefile)

```
make validate    # data schema validation
make enrich      # 4 LLM enrichment stages
make features    # feature matrix build
make cluster     # UMAP + HDBSCAN
make dashboard   # streamlit run src/dashboard/app.py
make all         # full pipeline
make clean       # remove processed outputs
```

Each script is designed as a pure function (`run_X(input_path, output_path)`) for easy Prefect migration later.

## Herramientas

Siempre que necesites documentación de una librería,
API o framework, usa Context7 automáticamente sin
que yo tenga que pedirlo explícitamente.

## Memoria

Tienes acceso a Engram para memoria persistente via
mem_save, mem_search, mem_context, mem_session_summary.

- Guarda proactivamente con mem_save después de:
  decisiones de arquitectura, bugfixes, patrones
  descubiertos, cambios de configuración.
- Al iniciar sesión llama mem_context para recuperar
  contexto previo.
- Al terminar la sesión llama mem_session_summary —
  esto NO es opcional.
- Si hay compactación de contexto, llama mem_context
  inmediatamente para recuperar el estado.
