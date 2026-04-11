from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/uploads", tags=["uploads"])


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
