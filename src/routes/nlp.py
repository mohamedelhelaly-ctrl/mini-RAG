from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse 
from helpers.config import get_settings, Settings
from routes.schemas.nlp import IndexPushRequest, IndexSearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models.enums.ResponseEnums import ResponseEnum
import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp", 
    tags=["api_v1", "nlp"]
)

@nlp_router.post("/index/push/{project_id}")
async def index_project_data(project_id: str, request: Request, push_request: IndexPushRequest,
                            app_settings : Settings = Depends(get_settings)):

    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.mongodb_client
    )
     
    project = await project_model.get_or_create_project(
        project_id=project_id
    )
 
    if not project: 
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": ResponseEnum.PROJECT_NOT_FOUND.value}
        )

    nlp_controller = NLPController(request.app.vectordb_client, 
                                request.app.generation_client, 
                                request.app.embedding_client,
                                request.app.template_parser)

    has_records = True
    page_no = 1
    inserted_records = 0 
    idx = 0

    while has_records:
        page_chunks = await chunk_model.get_chunks_by_project(
            project_id=project.id,
            page_no=page_no
        )

        if not page_chunks or len(page_chunks)==0:
            has_records = False
            break

        chunks_ids = list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_into_vectordb(
        project=project,
        chunks=page_chunks,
        chunks_ids=chunks_ids,
        do_reset= push_request.do_reset
        )

        if not is_inserted:
            logger.error(f"Failed to index chunks for project {project_id} at page {page_no}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": ResponseEnum.VECTORDB_INSERTION_FAILED.value}
            )
        
        page_no += 1
        inserted_records += len(page_chunks)
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": ResponseEnum.VECTORDB_INSERTION_SUCCESS.value,
            "inserted records": inserted_records}
    )
    

@nlp_router.get("/index/info/{project_id}")
async def get_index_info(project_id: str, request: Request):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )
    project = await project_model.get_or_create_project(
        project_id=project_id
    )

    nlp_controller = NLPController(request.app.vectordb_client, 
                                request.app.generation_client, 
                                request.app.embedding_client,
                                request.app.template_parser)
    
    collection_info = nlp_controller.get_vectordb_collection_info(project)
    # print(collection_info)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": ResponseEnum.VECTORDB_COLLECTION_INFO_RETRIEVED.value,
                 "collection_info": collection_info}
    ) 


@nlp_router.post("/index/search/{project_id}")
async def search_index(project_id: str, request: Request, search_request: IndexSearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )
    project = await project_model.get_or_create_project(
        project_id=project_id
    )

    nlp_controller = NLPController(request.app.vectordb_client, 
                                request.app.generation_client, 
                                request.app.embedding_client,
                                request.app.template_parser)
    
    results = nlp_controller.search_vectordb_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": ResponseEnum.VECTORDB_SEARCH_ERROR.value}
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": ResponseEnum.VECTORDB_SEARCH_SUCCESS.value,
                 "results": [result.dict() for result in results] }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_query(project_id: str, request: Request, search_request: IndexSearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongodb_client
    )
    project = await project_model.get_or_create_project(
        project_id=project_id
    )

    nlp_controller = NLPController(request.app.vectordb_client, 
                                request.app.generation_client, 
                                request.app.embedding_client,
                                request.app.template_parser)
    
    response, final_prompt, chat_history = nlp_controller.answer_query(
        project=project,
        query=search_request.text,
        limit=search_request.limit
    )

    if not response:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": ResponseEnum.RAG_ANSWER_ERROR.value}
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": ResponseEnum.RAG_ANSWER_SUCCESS.value,
                 "response": response,
                 "final_prompt": final_prompt,
                 "chat_history": chat_history}
    )


