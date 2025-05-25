import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter
from langchain_ollama import OllamaEmbeddings
import config
from datetime import datetime
from typing import List, Dict, Optional
from langchain_weaviate.vectorstores import WeaviateVectorStore as Weaviate
from langchain_core.retrievers import BaseRetriever

class WeaviateClient:
    def __init__(self):
        self.client = weaviate.connect_to_local(
            host="weaviate",
            port=8080,
            grpc_port=50051,
            headers={"X-Embedding-Api-Key": "dummy"}  # Required for v4 schema validation
        )
        self.embeddings = OllamaEmbeddings(
            model=config.EMBEDDING_MODEL,
            base_url="http://host.docker.internal:11434"
        )
        self._init_metadata_collection()

    def _init_metadata_collection(self):
        """Initialize the metadata collection"""
        try:
            if not self.client.collections.exists(config.METADATA_COLLECTION):
                self.client.collections.create(
                    name=config.METADATA_COLLECTION,
                    properties=[
                        Property(name="collection_name", data_type=DataType.TEXT),
                        Property(name="document_type", data_type=DataType.TEXT),
                        Property(name="index_id", data_type=DataType.TEXT),
                        Property(name="filename", data_type=DataType.TEXT),
                        Property(name="upload_date", data_type=DataType.TEXT)
                    ],
                    vectorizer_config=Configure.Vectorizer.none()
                )
        except Exception as e:
            self.client.close()
            raise RuntimeError(f"Metadata collection init failed: {str(e)}")

    def __del__(self):
        """Safer cleanup with existence check"""
        if hasattr(self, 'client') and self.client.is_connected():
            self.client.close()
    
    def init_collection(self, collection_name: str) -> None:
        """Initialize document collection with explicit vector index config"""
        if not self.client.collections.exists(collection_name):
            self.client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="page", data_type=DataType.INT),
                    Property(name="document_type", data_type=DataType.TEXT),
                    Property(name="index_id", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT)
                ],
                vectorizer_config=Configure.Vectorizer.none(),
            )
    
    
    def store_metadata(self, collection_name: str, document_type: str, 
                     index_id: str, filename: str) -> None:
        """Store metadata using v4 data insertion pattern"""
        metadata_collection = self.client.collections.get(config.METADATA_COLLECTION)
        
        metadata_collection.data.insert(
            properties={
                "collection_name": collection_name,
                "document_type": document_type,
                "index_id": index_id,
                "filename": filename,
                "upload_date": datetime.now().isoformat()
            }
        )
    
    def get_all_collections(self) -> List[str]:
        """Get collections using v4 collection interface"""
        print("Fetching all collections...")
        collections = self.client.collections.list_all().values()  # Get collection objects
        print("Available collections:", collections)
        return [
            collection.name for collection in collections
            if collection.name != config.METADATA_COLLECTION
        ]
    
    def get_index_ids(self, collection_name: str) -> List[str]:
        """Get index IDs using v4 query interface"""
        metadata_collection = self.client.collections.get(config.METADATA_COLLECTION)
        
        response = metadata_collection.query.fetch_objects(
            limit=1000,
            return_properties=["index_id"],
            filters=Filter.by_property("collection_name").equal(collection_name)
        )
        
        return list({obj.properties["index_id"] for obj in response.objects})
    
    def get_document_types(self, collection_name: str) -> List[str]:
        """Get document types using v4 query interface"""
        metadata_collection = self.client.collections.get(config.METADATA_COLLECTION)
        
        response = metadata_collection.query.fetch_objects(
            limit=1000,
            return_properties=["document_type"],
            filters=Filter.by_property("collection_name").equal(collection_name)
        )
        
        return list({obj.properties["document_type"] for obj in response.objects})
    
    def get_files(self, collection_name: str, document_type: str, 
                index_id: str) -> List[Dict[str, str]]:
        """Get files using v4 query interface with compound filter"""
        metadata_collection = self.client.collections.get(config.METADATA_COLLECTION)
        
        response = metadata_collection.query.fetch_objects(
            return_properties=["filename", "upload_date"],
            filters=Filter.all_of([
                Filter.by_property("collection_name").equal(collection_name),
                Filter.by_property("document_type").equal(document_type),
                Filter.by_property("index_id").equal(index_id)
            ])
        )
        
        return [{
            "filename": obj.properties["filename"],
            "upload_date": obj.properties["upload_date"]
        } for obj in response.objects]
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check collection existence using v4 interface"""
        return self.client.collections.exists(collection_name)
    
    def __del__(self):
        """Ensure proper connection cleanup"""
        if self.client.is_connected():
            self.client.close()
    
    
    def get_retriever(self, collection_name: str, document_type: str, index_id: str, k: int = 10) -> Optional[BaseRetriever]:
        """
        Get configured retriever with proper filters
        """
        if not self.client.collections.exists(collection_name):
            return None

        # Create vector store instance
        vectorstore = Weaviate(
            client=self.client,
            index_name=collection_name,
            text_key="text",
            embedding=self.embeddings
        )

        # Build v4 filter
        query_filter = Filter.all_of(
            Filter.by_property("document_type").equal(document_type),
            Filter.by_property("index_id").equal(index_id)
        )

        return vectorstore.as_retriever(
            search_kwargs={"k": k, "filter": query_filter}
        )

# Create a singleton instance
weaviate_client = WeaviateClient()