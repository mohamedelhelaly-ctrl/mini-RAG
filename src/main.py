from fastapi import FastAPI
from routes import base,data,nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.vectorDBProviderFactory import vectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser


app = FastAPI()

@app.on_event("startup")
async def startup():
    settings = get_settings()
    
    #mongoDB client
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb_client = app.mongodb_conn[settings.MONGODB_DATABASE]

    llm_factory = LLMProviderFactory(settings)
    vectordb_factory = vectorDBProviderFactory(settings)

    #generation client
    app.generation_client = llm_factory.create_provider(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    #embedding client
    app.embedding_client = llm_factory.create_provider(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)

    #vector database client
    app.vectordb_client = vectordb_factory.create_provider(settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()

    app.template_parser = TemplateParser(settings.DEFAULT_LANGUAGE)

@app.on_event("shutdown")
async def shutdown():
    app.mongodb_conn.close()
    app.vectordb_client.disconnect()

 
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)