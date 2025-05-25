# query_service.py
from typing import AsyncGenerator
from langchain_ollama import OllamaLLM
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
        Query documents using repository pattern for Weaviate access
        """
        if not weaviate_client.collection_exists(query_request.collection_name):
            yield "[ERROR] Collection not found"
            return

        try:
            retriever = weaviate_client.get_retriever(
                collection_name=query_request.collection_name,
                document_type=query_request.document_type,
                index_id=query_request.index_id,
                k=10
            )

            llm = OllamaLLM(
                model=config.LLM_MODEL,
                temperature=query_request.temperature or config.DEFAULT_TEMPERATURE,
                max_tokens=query_request.max_tokens or config.DEFAULT_MAX_TOKENS,
                streaming=True,
            )

            prompt = ChatPromptTemplate.from_template(
                "Answer the question using only the context below.\n\n"
                "<context>\n{context}\n</context>\n\nQuestion: {input}"
            )
            
            document_chain = create_stuff_documents_chain(
                llm,
                prompt,
                document_variable_name="context",
                output_parser=StrOutputParser()
            )

            retrieval_chain = create_retrieval_chain(retriever, document_chain)

            async for chunk in retrieval_chain.astream({"input": query_request.question}):
                yield chunk.get("answer", "") if isinstance(chunk, dict) else chunk

        except Exception as e:
            yield f"[ERROR] {str(e)}"