from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, shutil

# Document loading
from langchain_community.document_loaders.pdf import PyPDFLoader   # updated path :contentReference[oaicite:6]{index=6}

# Text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter  # external package :contentReference[oaicite:7]{index=7}

# Vector store
from langchain_community.vectorstores.weaviate import Weaviate      # updated module path :contentReference[oaicite:8]{index=8}

# Core LangChain primitives
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate                # core prompts :contentReference[oaicite:9]{index=9}
from langchain_core.output_parsers import StrOutputParser           # output parser

# Chains
from langchain.chains.combine_documents import create_stuff_documents_chain  # combine docs :contentReference[oaicite:10]{index=10}
from langchain.chains import create_retrieval_chain                          # retrieval :contentReference[oaicite:11]{index=11}

# Ollama integration
from langchain_ollama import OllamaEmbeddings   # new embeddings import :contentReference[oaicite:12]{index=12}
from langchain_ollama import OllamaLLM           # replace deprecated Ollama :contentReference[oaicite:13]{index=13}

import weaviate

app = FastAPI()

# Configuration
WEAVIATE_URL  = os.getenv("WEAVIATE_URL", "http://localhost:8080")
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL       = "deepseek-r1:7b"
CHUNK_SIZE      = 1024
CHUNK_OVERLAP   = 128

# Initialize Ollama embeddings & LLM
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)    # base_url defaults to http://localhost:11434 :contentReference[oaicite:14]{index=14}
llm        = OllamaLLM(model=LLM_MODEL)

# Initialize Weaviate client
client = weaviate.Client(
    url=WEAVIATE_URL,
    additional_headers={"X-Ollama-Model": EMBEDDING_MODEL}
)

# Create schema if it doesn't exist
schema = {
    "class": "Document",
    "vectorizer": "text2vec-ollama",
    "properties": [
        {"name": "text",   "dataType": ["text"]},
        {"name": "source", "dataType": ["string"]},
        {"name": "page",   "dataType": ["int"]}
    ]
}
if not client.schema.exists("Document"):
    client.schema.create_class(schema)

# Build prompt template
prompt = ChatPromptTemplate.from_template(
    "Answer the question using only the context below.\n\n"
    "<context>\n{context}\n</context>\n\nQuestion: {input}"
)

# Document‐to‐text chain
document_chain = create_stuff_documents_chain(
    llm,
    prompt,
    document_variable_name="context",
    output_parser=StrOutputParser()
)

class QueryRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        temp_dir = "./temp"
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, file.filename)
        with open(path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # Load and split PDF
        loader = PyPDFLoader(path)
        pages = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        docs = splitter.split_documents(pages)

        # Persist to Weaviate
        vectorstore = Weaviate(
            client=client,
            index_name="Document",
            text_key="text",
            embedding=embeddings,
            by_text=False
        )
        vectorstore.add_documents(docs)

        return JSONResponse({"message": f"Stored {len(docs)} chunks from {file.filename}"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/query")
async def query_documents(req: QueryRequest):
    try:
        vectorstore = Weaviate(
            client=client,
            index_name="Document",
            text_key="text",
            embedding=embeddings,
            by_text=False
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        resp = retrieval_chain.invoke({"input": req.question})

        # Gather metadata sources
        docs = retriever.get_relevant_documents(req.question)
        sources = [d.metadata for d in docs if hasattr(d, "metadata")]

        return {"answer": resp["answer"], "sources": sources}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
