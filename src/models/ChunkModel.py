from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DatabaseEnums import DatabaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from typing import List

class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DatabaseEnum.COLLECTION_CHUNK_NAME.value]

    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client)
        await instance.init_collection()
        return instance
    
    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DatabaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.db_client[DatabaseEnum.COLLECTION_CHUNK_NAME.value]
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index.get("unique", False)
                )
    

    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))  # insert_one takes a dict, we need to convert the DataChunk object to a dict  
        chunk.chunk_id = result.inserted_id
        return chunk
    
    
    async def get_chunk(self, chunk_id: int):
        result = await self.collection.find_one({
            "_id": ObjectId(chunk_id)
        })
        if result is None:
            return None
        
        return DataChunk(**result) 
    

    
    async def insert_chunks_bulk(self, chunks: list[DataChunk], batch_size: int = 100):
        # processes chunks in small batches rather than loading the entire list into memory at once, to prevent memory overflow and improve performance when dealing with large datasets.
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            operations = [
                InsertOne(chunk.dict(by_alias=True, exclude_unset=True)) 
                for chunk in batch
            ]
            # performs multiple insert operations in a single database call, which is more efficient than inserting each chunk individually
            await self.collection.bulk_write(operations)
        
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })
        return result.deleted_count
    
    async def get_chunks_by_project(self, project_id: ObjectId, page_no: int=1,
                                    page_size: int=50) -> List[DataChunk]:
        records = await self.collection.find({
            "chunk_project_id": project_id
        }).skip((page_no-1) * page_size).limit(page_size).to_list(length=None) 

        return [DataChunk(**record) for record in records]
    
    async def fetch_all_chunks(chunk_model, project_id):
        all_chunks = []
        page_no = 1
        page_size = 50  # Or adjust as needed
        while True:
            chunks = await chunk_model.get_chunks_by_project(project_id, page_no=page_no, page_size=page_size)
            if not chunks or len(chunks)==0:  # No more results
                break
            all_chunks.extend(chunks)
            page_no += 1
        return all_chunks