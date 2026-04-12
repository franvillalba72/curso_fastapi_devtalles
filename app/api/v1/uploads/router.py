import os
import shutil  # Para tener permisos para mover y guardar archivos
import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.file_storage import save_upload_image

router = APIRouter(prefix="/uploads", tags=["uploads"])

MEDIA_DIR = "app/media"


@router.post("/bytes")
async def upload_bytes(file: bytes = File(...)):
    return {
        "filename": "uploaded_file",
        "content_type": "application/octet-stream",
        "size_bytes": len(file),
    }


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
    }


@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    saved_file = save_upload_image(file)

    return {
        "filename": saved_file["filename"],
        "content_type": saved_file["content_type"],
        "url": saved_file["url"],
        "size_mb": saved_file["size_mb"],
        # "chunk_size_used": saved_file["chunk_size_used"],
        # "chunk_calls": saved_file["chunk_calls"],
        # "chunk_sizes": saved_file["chunk_sizes"],
    }
