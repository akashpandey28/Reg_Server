from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    collection_name: str
    document_type: str
    index_id: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class CollectionInfo(BaseModel):
    name: str

class CollectionsList(BaseModel):
    collections: List[CollectionInfo]

class IndexIdInfo(BaseModel):
    index_id: str

class IndexIdsList(BaseModel):
    index_ids: List[IndexIdInfo]

class DocumentTypeInfo(BaseModel):
    document_type: str

class DocumentTypesList(BaseModel):
    document_types: List[DocumentTypeInfo]

class FileInfo(BaseModel):
    filename: str
    upload_date: str

class FilesList(BaseModel):
    files: List[FileInfo]

class DocumentMetadata(BaseModel):
    collection_name: str
    document_type: str
    index_id: str
    filename: str
    upload_date: str