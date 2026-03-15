from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import os
import aiofiles
from models import ResponseEnum
import logging
from .schemas.data import ProcessRequest

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
    
    file_path, file_id = data_controller.generate_unique_filepath(original_filename=file.filename, project_id=project_id)

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
                            "file_path": file_path,
                            "file_id": file_id
                            }
                        )


@data_router.post("/process/{project_id}")
async def process_data(project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(
        file_content=file_content, 
        file_id=file_id,
        chunk_size=chunk_size, 
        overlap_size=overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"error": ResponseEnum.FILE_PROCESSING_FAILED.value}
            )
    
    # return JSONResponse(
    #     status_code=status.HTTP_200_OK, 
    #     content={
    #         "message": ResponseEnum.FILE_PROCESSING_SUCCESS.value,
    #         "file_id": file_id
    #     }
    # ), file_chunks

    return file_chunks


    
