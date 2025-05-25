from typing import Dict, Any, AsyncGenerator, Optional
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores.weaviate import Weaviate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

import config
from database.weaviate_client import weaviate_client
from models.schemas import QueryRequest

class QueryService:
    @staticmethod
    async def query_documents(query_request: QueryRequest) -> AsyncGenerator[str, None]:
        """
        Query documents with the given parameters
        """
        if not weaviate_client.collection_exists(query_request.collection_name):
            yield "[ERROR] Collection not found"
            return
        
        # Configure LLM with temperature and max tokens if provided
        temperature = query_request.temperature if query_request.temperature is not None else config.DEFAULT_TEMPERATURE
        max_tokens = query_request.max_tokens if query_request.max_tokens is not None else config.DEFAULT_MAX_TOKENS
        
        llm = OllamaLLM(
            model=config.LLM_MODEL, 
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
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
        
        vectorstore = Weaviate(
            client=weaviate_client.client,
            index_name=query_request.collection_name,
            text_key="text",
            embedding=weaviate_client.embeddings,
            by_text=False
        )
        
        # Create filter for document_type and index_id
        filter = {
            "operator": "And",
            "operands": [
                {"path": ["document_type"], "operator": "Equal", "valueString": query_request.document_type},
                {"path": ["index_id"], "operator": "Equal", "valueString": query_request.index_id}
            ]
        }
        
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 10, "filter": filter}
        )
        
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        try:
            stream = retrieval_chain.stream({"input": query_request.question})
            async for chunk in stream:
                # Handle different chunk formats
                if isinstance(chunk, dict):
                    if "answer" in chunk:
                        yield chunk["answer"]
                elif isinstance(chunk, str):
                    yield chunk
        except Exception as e:
            yield f"[ERROR] {str(e)}"