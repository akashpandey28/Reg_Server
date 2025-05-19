# 🧠 RAG Server Setup Guide

This guide walks you through setting up a Retrieval-Augmented Generation (RAG) server using FastAPI, Weaviate, LangChain, and Ollama.

## 🗂️ Project Structure

```
rag-project/
│
├── docker-compose.yml         # Weaviate vector store setup
├── rag_server.py              # FastAPI app (entry point)
├── requirements.txt           # Python dependencies
└── temp/                      # Temporary PDF storage
```

---

## 🚀 Step 1: Start Weaviate with Ollama Module

Ensure Docker is installed, then use the following `docker-compose.yml` to start Weaviate:

```yaml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      CLUSTER_HOSTNAME: 'node1'
      ENABLE_MODULES: 'text2vec-ollama'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-ollama'
      OLLAMA_API_HOST: 'host.docker.internal:11434'
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  weaviate_data:
```

Start it with:

```bash
docker-compose up -d
```

Ensure Ollama is pulled on your host machine with the embedding model loaded:

```bash
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
```

---

## 🧑‍💻 Step 2: Install Python Dependencies

Recommended Python version: **3.11**

Create a virtual environment and install dependencies:

```bash
.\myenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

📄 `requirements.txt`:

```
fastapi==0.104.1
uvicorn==0.23.2
numpy==1.24.4
langchain==0.3.25
langchain-ollama==0.3.3
langchain-community
langchain-text-splitters
weaviate-client==4.5.1
pypdf==3.17.1
python-multipart==0.0.9
```

---

## 🧾 Step 3: Run the RAG Server

```bash
python rag_server.py
```

The server will start at: [http://localhost:8000](http://localhost:8000)

---

## 🛠️ API Endpoints

### ➕ Upload PDF

`POST /upload`

Upload a PDF and automatically split and vectorize its content.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@path_to_your.pdf"
```

### ❓ Query

`POST /query`

Send a question. The server will perform semantic search and respond using LLM.

Request:

```json
{
  "question": "What is the summary of the uploaded document?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [...]
}
```

### ✅ Health Check

`GET /health`

Returns:

```json
{ "status": "healthy" }
```

---

## 📎 Notes

* Ensure the embedding model and LLM are downloaded in Ollama (`nomic-embed-text` and `deepseek-r1:7b`)
* By default, embeddings are stored in Weaviate under the class `Document`.


