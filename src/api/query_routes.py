from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from services.document_service import DocumentService
from models.schemas import FilesList, FileInfo

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_type: str = Form(...),
    index_id: str = Form(...)
):
    """
    Upload and process a PDF document
    """
    try:
        result = await DocumentService.upload_document(
            file=file,
            collection_name=collection_name,
            document_type=document_type,
            index_id=index_id
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def get_files(collection_name: str, document_type: str, index_id: str):
    """
    Get all files for a given collection, document_type and index_id
    """
    try:
        files = DocumentService.get_files(collection_name, document_type, index_id)
        file_list = [FileInfo(filename=file["filename"], upload_date=file["upload_date"]) for file in files]
        return FilesList(files=file_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))