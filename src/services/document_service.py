import os
import shutil
from fastapi import UploadFile
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.weaviate import Weaviate
from typing import List, Dict, Any

import config
from database.weaviate_client import weaviate_client

class DocumentService:
    @staticmethod
    async def upload_document(
        file: UploadFile,
        collection_name: str,
        document_type: str,
        index_id: str
    ) -> Dict[str, Any]:
        """
        Process and upload a document to Weaviate
        """
        # Initialize collection if it doesn't exist
        weaviate_client.init_collection(collection_name)
        
        # Save file temporarily
        temp_dir = "./temp"
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, file.filename)
        
        with open(path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        
        # Load and process document
        loader = PyPDFLoader(path)
        pages = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        
        docs = splitter.split_documents(pages)
        
        # Add metadata to all documents
        for doc in docs:
            doc.metadata["document_type"] = document_type
            doc.metadata["index_id"] = index_id
            doc.metadata["filename"] = file.filename
        
        # Store in Weaviate
        vectorstore = Weaviate(
            client=weaviate_client.client,
            index_name=collection_name,
            text_key="text",
            embedding=weaviate_client.embeddings,
            by_text=False
        )
        
        vectorstore.add_documents(docs)
        
        # Store metadata
        weaviate_client.store_metadata(collection_name, document_type, index_id, file.filename)
        
        # Clean up temporary file
        os.remove(path)
        
        return {"message": f"Stored {len(docs)} chunks in {collection_name}", "filename": file.filename}
    
    @staticmethod
    def get_collections() -> List[str]:
        """Get all collections"""
        return weaviate_client.get_all_collections()
    
    @staticmethod
    def get_index_ids(collection_name: str) -> List[str]:
        """Get all index_ids for a collection"""
        return weaviate_client.get_index_ids(collection_name)
    
    @staticmethod
    def get_document_types(collection_name: str) -> List[str]:
        """Get all document types for a collection"""
        return weaviate_client.get_document_types(collection_name)
    
    @staticmethod
    def get_files(collection_name: str, document_type: str, index_id: str) -> List[Dict[str, str]]:
        """Get all files for a collection, document_type and index_id"""
        return weaviate_client.get_files(collection_name, document_type, index_id)