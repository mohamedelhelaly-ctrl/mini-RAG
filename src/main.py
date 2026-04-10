from fastapi import FastAPI
from routes import base,data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory


app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb_client = app.mongodb_conn[settings.MONGODB_DATABASE]



    llm_factory = LLMProviderFactory(settings)

    app.generation_client = llm_factory.create_provider(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    app.embedding_client = llm_factory.create_provider(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_conn.close()


app.include_router(base.base_router)
app.include_router(data.data_router)