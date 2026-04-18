from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse 
from httpcore import request
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import os
import aiofiles
from models import ResponseEnum, AssetTypeEnum
import logging
from .schemas.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.mongodb_schemas import DataChunk
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.mongodb_schemas.asset import Asset

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile, 
                      app_settings : Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )

    project = await project_model.get_or_create_project(
        project_id=project_id
    )

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
    
    asset_model = await AssetModel.create_instance(
        db_client=request.app.mongodb_client
    )

    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.ASSET_TYPE_FILE.value,
        asset_name=file_id, 
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(status_code=status.HTTP_200_OK, 
                        content={
                            "message": message, 
                            "file_id": str(asset_record.id),
                            "file_name": asset_record.asset_name
                            }
                        )


@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str, process_request: ProcessRequest):
    # file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )

    project = await project_model.get_or_create_project(
        project_id=project_id
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.mongodb_client
    )

    asset_model = await AssetModel.create_instance(
            db_client=request.app.mongodb_client
        )

    project_file_ids = {}
    
    if process_request.file_id:
        asset_record = await asset_model.get_asset(
            asset_project_id=project.id,
            asset_name=process_request.file_id
        )
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={"error": ResponseEnum.FILE_NOT_FOUND.value}
                )
        
        project_file_ids[asset_record.id] = asset_record.asset_name

    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.ASSET_TYPE_FILE.value
        )
        project_file_ids = {
            record.id : record.asset_name 
            for record in project_files
        }
    
    if len(project_file_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"error": ResponseEnum.NO_FILES_TO_PROCESS.value}
            )
    

    process_controller = ProcessController(project_id=project_id)

    if do_reset == 1:
        deleted_count = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )
        logger.info(f"Deleted {deleted_count} existing chunks for project {project_id} before processing new file.")

    no_of_records = 0
    no_of_files = 0
    for asset_id, file_id in project_file_ids.items():
        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"File with ID {file_id} not found for project {project_id}. Skipping processing for this file.")
            continue

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

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_of_records += await chunk_model.insert_chunks_bulk(chunks=file_chunks_records)
        no_of_files += 1
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={
            "message": ResponseEnum.FILE_PROCESSING_SUCCESS.value,
            "file_ids": str(project_file_ids),
            "number_of_files_processed": no_of_files,
            "inserted_chunks": no_of_records
        }
    )



    
