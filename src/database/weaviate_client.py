import weaviate
from langchain_ollama import OllamaEmbeddings
import config
from datetime import datetime
from typing import List, Dict, Any, Optional

class WeaviateClient:
    def __init__(self):
        self.client = weaviate.Client(
            url=config.WEAVIATE_URL,
            additional_headers={"X-Ollama-Model": config.EMBEDDING_MODEL}
        )
        self.embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        self._init_metadata_collection()
    
    def _init_metadata_collection(self):
        """Initialize the metadata collection for storing document metadata"""
        metadata_schema = {
            "class": config.METADATA_COLLECTION,
            "properties": [
                {"name": "collection_name", "dataType": ["string"]},
                {"name": "document_type", "dataType": ["string"]},
                {"name": "index_id", "dataType": ["string"]},
                {"name": "filename", "dataType": ["string"]},
                {"name": "upload_date", "dataType": ["string"]}
            ]
        }
        
        if not self.client.schema.exists(metadata_schema["class"]):
            self.client.schema.create_class(metadata_schema)
    
    def init_collection(self, collection_name: str) -> None:
        """Initialize a collection in Weaviate if it doesn't exist"""
        class_schema = {
            "class": collection_name,
            "vectorizer": "text2vec-ollama",
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "source", "dataType": ["string"]},
                {"name": "page", "dataType": ["int"]},
                {"name": "document_type", "dataType": ["string"]},
                {"name": "index_id", "dataType": ["string"]},
                {"name": "filename", "dataType": ["string"]}
            ]
        }
        
        if not self.client.schema.exists(class_schema["class"]):
            self.client.schema.create_class(class_schema)
    
    def store_metadata(self, collection_name: str, document_type: str, index_id: str, filename: str) -> None:
        """Store document metadata in the metadata collection"""
        upload_date = datetime.now().isoformat()
        
        self.client.data_object.create(
            class_name=config.METADATA_COLLECTION,
            data_object={
                "collection_name": collection_name,
                "document_type": document_type,
                "index_id": index_id,
                "filename": filename,
                "upload_date": upload_date
            }
        )
    
    def get_all_collections(self) -> List[str]:
        """Get all collection names from Weaviate"""
        schema = self.client.schema.get()
        collections = []
        
        for cls in schema["classes"]:
            class_name = cls["class"]
            # Skip the metadata collection
            if class_name != config.METADATA_COLLECTION:
                collections.append(class_name)
        
        return collections
    
    def get_index_ids(self, collection_name: str) -> List[str]:
        """Get all index_ids for a given collection"""
        query = {
            "class": config.METADATA_COLLECTION,
            "properties": ["index_id"],
            "where": {
                "path": ["collection_name"],
                "operator": "Equal",
                "valueString": collection_name
            }
        }
        
        result = self.client.query.get(**query).do()
        
        if not result or "data" not in result or "Get" not in result["data"] or config.METADATA_COLLECTION not in result["data"]["Get"]:
            return []
        
        items = result["data"]["Get"][config.METADATA_COLLECTION]
        # Get unique index_ids
        unique_ids = set()
        for item in items:
            unique_ids.add(item["index_id"])
        
        return list(unique_ids)
    
    def get_document_types(self, collection_name: str) -> List[str]:
        """Get all document_types for a given collection"""
        query = {
            "class": config.METADATA_COLLECTION,
            "properties": ["document_type"],
            "where": {
                "path": ["collection_name"],
                "operator": "Equal",
                "valueString": collection_name
            }
        }
        
        result = self.client.query.get(**query).do()
        
        if not result or "data" not in result or "Get" not in result["data"] or config.METADATA_COLLECTION not in result["data"]["Get"]:
            return []
        
        items = result["data"]["Get"][config.METADATA_COLLECTION]
        # Get unique document_types
        unique_types = set()
        for item in items:
            unique_types.add(item["document_type"])
        
        return list(unique_types)
    
    def get_files(self, collection_name: str, document_type: str, index_id: str) -> List[Dict[str, str]]:
        """Get all files for a given collection, document_type and index_id"""
        query = {
            "class": config.METADATA_COLLECTION,
            "properties": ["filename", "upload_date"],
            "where": {
                "operator": "And",
                "operands": [
                    {"path": ["collection_name"], "operator": "Equal", "valueString": collection_name},
                    {"path": ["document_type"], "operator": "Equal", "valueString": document_type},
                    {"path": ["index_id"], "operator": "Equal", "valueString": index_id}
                ]
            }
        }
        
        result = self.client.query.get(**query).do()
        
        if not result or "data" not in result or "Get" not in result["data"] or config.METADATA_COLLECTION not in result["data"]["Get"]:
            return []
        
        return result["data"]["Get"][config.METADATA_COLLECTION]
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        return self.client.schema.exists(collection_name)

# Create a singleton instance
weaviate_client = WeaviateClient()  