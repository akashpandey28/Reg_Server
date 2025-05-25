# 🧠 RAG Server Setup Guide

This guide walks you through setting up a Retrieval-Augmented Generation (RAG) server using FastAPI, Weaviate, LangChain, and Ollama.


## 🚀 Step 1: Start Weaviate with Ollama Module

# Ollama config (Windows)
```
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

Ensure Ollama is pulled on your host machine with the embedding model loaded:

```bash
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
```


Start it with:

```bash
docker-compose up -d
```

The server will start at: [http://localhost:8000](http://localhost:8000)

---


