.PHONY: validate ingest enrich features cluster dashboard all clean

VENV := .venv/bin

validate:
	$(VENV)/python src/data/validate.py

ingest:
	$(VENV)/python src/data/ingest.py

enrich:
	$(VENV)/python -m src.enrichment.embeddings
	$(VENV)/python -m src.enrichment.intents
	$(VENV)/python -m src.enrichment.customer_dna

features:
	$(VENV)/python src/features/build_matrix.py

cluster:
	$(VENV)/python src/models/cluster.py
	$(VENV)/python src/models/segments.py

dashboard:
	$(VENV)/streamlit run src/dashboard/app.py

all: validate enrich features cluster
	@echo "Pipeline completado. Ejecuta 'make dashboard' para Streamlit."

clean:
	rm -rf data/processed/*
	rm -f data/*.db
