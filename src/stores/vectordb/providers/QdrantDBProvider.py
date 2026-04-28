from ..vectorDBInterface import vectorDBInterface
from ..vectorDBEnums import vectorDBEnums, DistanceMethodEnums
from qdrant_client import QdrantClient, models
from typing import List
from models.db_schemas.minirag.schemas.data_chunk import RetrievedDocument
import logging

class QdrantDBProvider(vectorDBInterface):
    
    def __init__(self, db_client: str, default_vector_size: int = 768, 
                 distance_method: str = None, index_threshold: int = 1000 ):
        self.client = None
        self.db_client = db_client
        self.distance_method = None
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        self.client = QdrantClient(path=self.db_client)
        self.logger.info(f"Connected to QdrantDB")

    async def disconnect(self):
        self.client = None
        self.logger.info(f"Disconnected from QdrantDB")
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)
    
    async def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name)
    
    async def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection {collection_name}")
            self.client.delete_collection(collection_name)
            self.logger.info(f"Collection {collection_name} deleted successfully")
        else:
            self.logger.warning(f"Collection {collection_name} does not exist")

    async def create_collection(self, collection_name: str,
                          embedding_size: int,
                          do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name)

        if not self.is_collection_existed(collection_name):
            self.logger.info(f"Creating collection {collection_name} with embedding size {embedding_size}")
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_method)
            )
            return True
        return False
    
    async def insert_one(self, collection_name: str,
                   text: str,
                   vector: list,
                   metadata: dict = None,
                   record_id: str = None):
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist")
            return False
        
        try:
            _ = self.client.upsert(
                collection_name=collection_name,
                points = [
                    models.PointStruct(
                        id = record_id,
                        vector=vector,
                        payload={
                            "text": text,
                            "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error inserting record: {e}")
            return False
        
        return True
    
    async def instert_many(self, collection_name: str,
                     texts: list,
                     vectors: list,
                     metadatas: list = None,
                     record_ids: list = None,
                     batch_size: int = 50):
        
        if metadatas is None:
            metadatas = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.PointStruct(
                    id = batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x] ,
                        "metadata": batch_metadatas[x]
                    }
                )
                for x in range(len(batch_texts))
            ]
        try:
            _ = self.client.upsert(
                collection_name=collection_name,
                points=batch_records
            )
        except Exception as e:
            self.logger.error(f"Error inserting batch: {e}")
            return False

        return True
    
    async def search_by_vector(self, collection_name: str,
                         vector: list,
                         limit: int = 5):
        
        results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        )

        points = None
        # if isinstance(results, dict):
        #     points = results.get("points", [])
        # else:
        points = getattr(results, "points", [])

        if not points:
            self.logger.warning(
                f"No results found for the given query vector in collection {collection_name}"
            )
            return None
        
        return [
            RetrievedDocument(**{
                "text": point.payload["text"],
                "score": point.score
            })
            for point in points
        ]
    
    