import os
import uuid

import aiofiles
from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = "/opt/local-services/backend/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
EXTENSION_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


async def save_upload(file: UploadFile, upload_type: str) -> str:
    """
    Save an uploaded file to disk.

    Args:
        file: The uploaded file.
        upload_type: Subdirectory type (e.g. "avatars", "portfolio").

    Returns:
        Relative URL path to the saved file.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: image/jpeg, image/png",
        )

    # Read content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    ext = EXTENSION_MAP[file.content_type]
    filename = f"{uuid.uuid4()}.{ext}"
    dir_path = os.path.join(UPLOAD_DIR, upload_type)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Return relative URL path
    return f"/uploads/{upload_type}/{filename}"
