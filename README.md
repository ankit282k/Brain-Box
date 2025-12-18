# Brain Box 🧠

Brain Box is a Retrieval-Augmented Generation (RAG) chat bot. The backend ingests documents, builds a vector store, and serves a chat API that answers questions using retrieved context.

## Features
- Vector embedding and storage using ChromaDB
- Semantic retrieval and prompt orchestration with LangChain
- It uses Models powered by Azure AI Foundry
- Document ingestion and vector store rebuild on upload
- Pluggable LLM / embedding configuration via environment variables

## Repository Structure

- `backend/` — FastAPI app and RAG logic (app.py, main.py, vector_store.py, etc.)
- `frontend/` — Streamlit UI
- `data/` — Uploaded documents and vector store files
- `templates/` — HTML templates (if used)
- `docker-compose.yml` — Docker compose for local deployment

## Requirements
- Python 3.10+
- See `backend/requirements.txt` and `frontend/requirements.txt` for project-specific dependencies

## Quickstart - Docker

```bash
docker compose up --build
```

## Run locally

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Install frontend dependencies (if using Streamlit UI):

```bash
pip install -r frontend/requirements.txt
```

4. Create a `.env` file in the project root (see next section for variables).

5. Run the backend (development):

```bash
# from project root
python backend/app.py
# or
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

6. Run the frontend UI (Streamlit):

```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

## .env — recommended variables

Create a `.env` file at the project root. The backend reads configuration from environment variables (via `os.environ` in the code). Below are recommended variables and example values — adapt these to your environment and provider.

Example `.env`:

```
# Azure AI Foundry
AZURE_API_KEY
API_VERSION
AZURE_ENDPOINT 

# Models
MODEL_NAME=gpt-4.1-mini   # or any supported model name
EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small
DEPLOYMENT_NAME = "gpt-4.1-mini"

```

How to use the `.env` file:

- Place `.env` in the repository root. Your shell or a dotenv loader will expose these values to the Python process.
- If you rely on `python-dotenv` in the codebase, the app will load `.env` automatically; otherwise export variables before starting the app:

## Notes & Troubleshooting
- Ensure `OPENAI_API_KEY` (or other LLM provider keys) are valid and have required permissions.
- If the app cannot initialize the bot, check logs for missing env vars or missing dependencies.
- Uploaded documents are stored in `data/` — if vector files are stored there too, keep backups before deleting.

## Next steps / customization
- Swap embedding or LLM models by changing `EMBEDDING_MODEL` and `LLM_MODEL` in `.env`.
- Add provider-specific secrets (Pinecone, Azure, etc.) to `.env` and update `backend/vector_store.py` accordingly.
- Add authentication to the API in front of the endpoints for production.
