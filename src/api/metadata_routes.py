from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.document_service import DocumentService

router = APIRouter(prefix="/metadata", tags=["Metadata"])

@router.get("/collections")
def get_all_collections():
    """
    Get list of all collections in the database
    """
    try:
        result = DocumentService.get_collections()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index_ids")
def get_index_ids(collection_name: str):
    """
    Get list of index_ids in the given collection id
    """
    try:
        result = DocumentService.get_index_ids(collection_name=collection_name)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document_types")
def get_document_types(collection_name: str):
    """
    Get list of document types in the given collection id
    """
    try:
        result = DocumentService.get_document_types(collection_name=collection_name)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
