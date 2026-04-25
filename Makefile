.PHONY: validate enrich features cluster dashboard all clean

validate:
	python src/data/validate.py

enrich:
	python src/enrichment/embeddings.py
	python src/enrichment/intents.py
	python src/enrichment/descriptions.py
	python src/enrichment/customer_dna.py

features:
	python src/features/build_matrix.py

cluster:
	python src/models/cluster.py
	python src/models/segments.py

dashboard:
	streamlit run src/dashboard/app.py

all: validate enrich features cluster
	@echo "Pipeline completado. Ejecuta 'make dashboard' para Streamlit."

clean:
	rm -rf data/processed/*
	rm -f data/*.db
