import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.deps import get_current_active_user
from app.models import User

router = APIRouter()

UPLOAD_BASE = Path("/opt/local-services/backend/uploads")
ALLOWED_TYPES = {"avatar", "portfolio", "chat", "verification_doc"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...),
    current_user: User = Depends(get_current_active_user),
):
    if type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid upload type. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are allowed",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 10MB",
        )

    ext = "jpg" if file.content_type == "image/jpeg" else "png"
    filename = f"{uuid_mod.uuid4()}.{ext}"

    upload_dir = UPLOAD_BASE / type
    upload_dir.mkdir(parents=True, exist_ok=True)

    filepath = upload_dir / filename
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/uploads/{type}/{filename}"

    return {
        "url": url,
        "filename": filename,
        "size": len(contents),
        "content_type": file.content_type,
    }
