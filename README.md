# Local RAG with Weaviate + Ollama (Qualcomm Snapdragon X Elite)

This sample demonstrates a fully local Retrieval-Augmented Generation (RAG) pipeline using:

- Weaviate as the vector database and retriever
- Ollama for local embedding and generation models
- Python scripts to create a collection, ingest documents, and run semantic and generative queries

It is designed to run locally on Windows Subsystem for Linux (WSL) devices powered by Qualcomm Snapdragon X Elite. The sample is a collaboration between Weaviate and Qualcomm.

## What this demo shows

- Local embedding creation via the `text2vec-ollama` module
- Local generation via the `generative-ollama` module
- Local ingestion of a CSV dataset (books) into Weaviate
- End-to-end RAG workflow: ingest → retrieve (semantic) → generate explanations

## Architecture

- `docker-compose.yml` starts two local services:
  - `ollama` on port `11434`
  - `weaviate` on port `8080` with modules enabled: `text2vec-ollama,generative-ollama`
- Weaviate is configured with API key authentication enabled.
- The Python scripts connect locally to Weaviate and use Ollama for embeddings and generation.

Key module and model choices used in this demo:

- Embeddings: `snowflake-arctic-embed:latest` (via Ollama)
- Generator: `llama3.2:1b` (via Ollama)

You can change these models later to any supported by Ollama.

## Prerequisites

- Docker Desktop with Docker Compose
- Python 3.10+ (tested with 3.12)
- Internet access for initial model pulls (first run only)
- Windows on ARM device (e.g., Qualcomm Snapdragon X Elite) or WSL2 environment

Note on acceleration: Ollama supports hardware acceleration where available on Windows. Ensure you use the appropriate Ollama build and drivers for your device for best performance.

## Quick start

1) Start the local stack (Weaviate + Ollama)

```bash
# From the project root
docker compose up -d
```

2) Pull the Ollama models used by this demo (run once)

```bash
docker exec -it ollama ollama pull snowflake-arctic-embed:latest
docker exec -it ollama ollama pull llama3.2:1b
```

3) Set up Python environment and install dependencies

- Ubuntu (Windows Subsystem for Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install weaviate-client>=4.16.0
```

4) Verify Weaviate is reachable

```bash
python 0-test-connection.py
```

Expected output: `True` for `client.is_ready()`.

5) Create the collection and configure vectorization/generation

```bash
python 1-create-collection.py
```

This creates a `Book` collection using:

- Vectorizer: `text2vec-ollama` with `snowflake-arctic-embed:latest`
- Generative: `generative-ollama` with `llama3.2:1b`

6) Ingest the sample dataset

```bash
python 2-populate.py
```

The dataset `7k-books-kaggle.csv` is included in the repo. The script reads each row and inserts a corresponding object into the `Book` collection.

Column mapping in `2-populate.py`:

- 0 → `isbn13`
- 1 → `isbn10`
- 2 → `title`
- 3 → `subtitle`
- 4 → `authors`
- 5 → `categories`
- 6 → `thumbnail`
- 7 → `description`
- 8 → `published_year`
- 9 → `average_rating`
- 10 → `num_pages`
- 11 → `ratings_count`

7) Run a semantic search (vector search)

```bash
python 3-semantic_search.py
```

Enter a natural-language query (e.g., "books about machine learning for beginners"). The script will retrieve the top matching books and print their titles and descriptions.

8) Run a generative search (RAG-style explanation)

```bash
python 4-generative_search.py
```

Enter a query and the script will ask the local LLM to explain why each recommended book might be interesting based on its metadata.

## Files in this repo

- `docker-compose.yml` — Starts `weaviate` and `ollama` locally with the necessary modules enabled.
- `0-test-connection.py` — Simple readiness check for Weaviate.
- `1-create-collection.py` — Creates the `Book` collection and configures vectorizer + generative modules.
- `2-populate.py` — Reads `7k-books-kaggle.csv` and inserts rows as `Book` objects.
- `3-semantic_search.py` — Runs a semantic (vector) search over the `Book` collection.
- `4-generative_search.py` — Runs a generative query to explain retrieved books.
- `7k-books-kaggle.csv` — Sample dataset for ingestion.

## Configuration

- Authentication
  - Weaviate is configured with API keys (see `docker-compose.yml`).
  - The Python scripts currently use the demo key `user-a-key` (see `0-test-connection.py`, `1-create-collection.py`, `2-populate.py`, `3-semantic_search.py`).
  - You can change the allowed keys in `docker-compose.yml` under:
    - `AUTHENTICATION_APIKEY_ALLOWED_KEYS`
    - `AUTHENTICATION_APIKEY_USERS`

- Models
  - Embeddings: `snowflake-arctic-embed:latest`
  - Generator: `llama3.2:1b`
  - To use different models, pull them with Ollama and update `1-create-collection.py` accordingly.

- Dataset
  - If you swap in a different CSV, ensure the columns map to the properties used by `2-populate.py`.
  - The current schema in `1-create-collection.py` defines the key properties used for search and generation.

## Troubleshooting

- 401 Unauthorized from Weaviate
  - Ensure the API key used by your Python scripts matches an allowed key in `docker-compose.yml`.

- Connection errors to Weaviate
  - Ensure the containers are running: `docker ps`
  - Ports: Weaviate `8080`, Ollama `11434` must be available.

- Embedding/generation fails or times out
  - Make sure the Ollama models have been pulled: `docker exec -it ollama ollama list`
  - The first request after a model pull may take longer while the model loads.

- Ingestion errors
  - Validate the CSV format and column order.
  - Large ingests can be batched; see Weaviate client docs if you need higher throughput.

- Performance on Snapdragon X Elite
  - Use the latest Ollama build for Windows on ARM and keep drivers/accelerators up to date.
  - Close other heavy apps while running large models locally.

## Stopping and cleaning up

```bash
docker compose down
```

Volumes `weaviate_data` and `ollama_data` persist between runs. To remove them as well, run:

```bash
docker compose down -v
```

## Credits

This sample is a collaboration between Weaviate and Qualcomm.
