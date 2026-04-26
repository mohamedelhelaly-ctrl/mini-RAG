from celery import chunks

from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DatabaseEnums import DatabaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from typing import List
from sqlalchemy.future import select
from sqlalchemy import delete, func

class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client)
        return instance
    
    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        return chunk
    
    
    async def get_chunk(self, chunk_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_id == chunk_id)
                chunk = session.execute(query).scalar_one_or_none()
        return chunk
    

    # processes chunks in small batches rather than loading the entire list into memory at once, to prevent memory overflow and improve performance when dealing with large datasets.
    async def insert_chunks_bulk(self, chunks: list[DataChunk], batch_size: int = 100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
            await session.commit()
        return len(chunks)
        
    
    async def delete_chunks_by_project_id(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(query)
            await session.commit()
        return result.rowcount  # Return the number of deleted rows
    

    
    async def get_chunks_by_project(self, project_id: ObjectId, page_no: int=1,
                                    page_size: int=50) -> List[DataChunk]:
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_no-1) * page_size).limit(page_size)
                result = await session.execute(query)
                chunks = result.scalars().all()
        return chunks
        