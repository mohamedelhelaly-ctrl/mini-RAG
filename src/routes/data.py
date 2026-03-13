from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController
import os
import aiofiles
from models import ResponseEnum
import logging

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile, 
                      app_settings : Settings = Depends(get_settings)):
    
    data_controller = DataController()

    is_valid, message = data_controller.validate_file(file=file)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": message})
    
    file_path = data_controller.generate_unique_filename(original_filename=file.filename, project_id=project_id)

    # asynchronously stream an uploaded file to disk in fixed-size chunks, don't load the whole file into memory.
    try: 
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await out_file.write(chunk)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": ResponseEnum.FILE_UPLOAD_FAILED.value})
    
    return JSONResponse(status_code=status.HTTP_200_OK, 
                        content={
                            "message": message, 
                            "file_path": file_path
                            }
                        )
