from fastapi import FastAPI
from routes import base,data,nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.vectorDBProviderFactory import vectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


app = FastAPI()

@app.on_event("startup")
async def startup():
    settings = get_settings()
    
    #mongoDB client
    # app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    # app.db_client = app.mongodb_conn[settings.MONGODB_DATABASE]

    postgres_conn_string = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DB}"
    app.db_engine = create_async_engine(postgres_conn_string)
    app.db_client = sessionmaker(
        app.db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
 

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

    app.template_parser = TemplateParser(
        language=settings.DEFAULT_LANGUAGE
    )

@app.on_event("shutdown")
async def shutdown():
    # app.mongodb_conn.close()
    app.db_engine.dispose()
    app.vectordb_client.disconnect()

 
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)