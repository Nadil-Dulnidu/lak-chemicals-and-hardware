from fastapi import File, UploadFile
from app.config.imagekit import imagekit
import tempfile
import shutil
import os
from app.config.logging import get_logger

logger = get_logger(__name__)


async def upload_image(file: UploadFile = File(...)) -> str:
    """
    Uploads an image to ImageKit and returns the URL.
    """
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        upload_result = imagekit.upload_file(
            file=open(temp_file_path, "rb"),
            file_name=file.filename,
            options=UploadFileRequestOptions(
                use_unique_file_name=True, tags=["backend-upload"]
            ),
        )
        return upload_result.url
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()
