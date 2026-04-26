.PHONY: validate enrich features cluster dashboard all clean

VENV := .venv/bin

validate:
	$(VENV)/python src/data/validate.py

enrich:
	$(VENV)/python src/enrichment/embeddings.py
	$(VENV)/python src/enrichment/intents.py
	$(VENV)/python src/enrichment/descriptions.py
	$(VENV)/python src/enrichment/customer_dna.py

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
