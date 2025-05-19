from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os, shutil
from string import punctuation

# Document loading
from langchain_community.document_loaders.pdf import PyPDFLoader

# Text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Vector store
from langchain_community.vectorstores.weaviate import Weaviate

# Core LangChain primitives
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Chains
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Ollama integration
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM

import weaviate

app = FastAPI()

# Configuration
WEAVIATE_URL  = os.getenv("WEAVIATE_URL", "http://localhost:8080")
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL       = "qwen3:8b"
CHUNK_SIZE      = 1024
CHUNK_OVERLAP   = 128

# Initialize Ollama embeddings & LLM
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
llm        = OllamaLLM(model=LLM_MODEL, streaming=True)  # Enable streaming

# Initialize Weaviate client
client = weaviate.Client(
    url=WEAVIATE_URL,
    additional_headers={"X-Ollama-Model": EMBEDDING_MODEL}
)

# Build prompt template
prompt = ChatPromptTemplate.from_template(
    "Answer the question using only the context below.\n\n"
    "<context>\n{context}\n</context>\n\nQuestion: {input}"
)

# Document chain with streaming support
document_chain = create_stuff_documents_chain(
    llm,
    prompt,
    document_variable_name="context",
    output_parser=StrOutputParser()
)

class QueryRequest(BaseModel):
    question: str
    collection_name: str
    document_type: str
    index_id: str


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_type: str = Form(...),
    index_id: str = Form(...)
):
    try:
        class_schema = {
            "class": collection_name,
            "vectorizer": "text2vec-ollama",
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "source", "dataType": ["string"]},
                {"name": "page", "dataType": ["int"]},
                {"name": "document_type", "dataType": ["string"]},
                {"name": "index_id", "dataType": ["string"]}
            ]
        }
        
        if not client.schema.exists(class_schema["class"]):
            client.schema.create_class(class_schema)

        temp_dir = "./temp"
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, file.filename)
        with open(path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        loader = PyPDFLoader(path)
        pages = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        docs = splitter.split_documents(pages)

        # Add metadata to all documents
        for doc in docs:
            doc.metadata["document_type"] = document_type
            doc.metadata["index_id"] = index_id

        vectorstore = Weaviate(
            client=client,
            index_name=collection_name,
            text_key="text",
            embedding=embeddings,
            by_text=False
        )
        vectorstore.add_documents(docs)

        return JSONResponse({"message": f"Stored {len(docs)} chunks in {collection_name}"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/query")
async def query_documents(req: QueryRequest):
    try:
        if not client.schema.exists(req.collection_name):
            return JSONResponse(status_code=404, content={"error": "Collection not found"})
        vectorstore = Weaviate(
            client=client,
            index_name=req.collection_name,
            text_key="text",
            embedding=embeddings,
            by_text=False
        )

        # Create filter for document_type and index_id
        filter = {
            "operator": "And",
            "operands": [
                {"path": ["document_type"], "operator": "Equal", "valueString": req.document_type},
                {"path": ["index_id"], "operator": "Equal", "valueString": req.index_id}
            ]
        }

        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 10, "filter": filter}
        )

        # Create streaming response generator
        def generate():
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            try:
                stream = retrieval_chain.stream({"input": req.question})
                for chunk in stream:
                        # Handle different chunk formats
                        if isinstance(chunk, dict):
                            if "answer" in chunk:
                                yield f"data: {chunk['answer']}\n\n"
                        elif isinstance(chunk, str):
                            yield f"data: {chunk}\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"


        return StreamingResponse(generate(), media_type="text/event-stream", headers={"X-Content-Type-Options": "nosniff"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.mount("/", StaticFiles(directory="./", html=True), name="index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)