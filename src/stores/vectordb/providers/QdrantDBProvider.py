from ..vectorDBInterface import vectorDBInterface
from ..vectorDBEnums import vectorDBEnums, DistanceMethodEnums
from qdrant_client import QdrantClient, models
from typing import List
from models.db_schemas.data_chunk import RetrievedDocument
import logging

class QdrantDBProvider(vectorDBInterface):
    
    def __init__(self, db_path: str, distance_method: str):
        self.client = None
        self.db_path = db_path
        self.distance_method = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)
        self.logger.info(f"Connected to QdrantDB")

    def disconnect(self):
        self.client = None
        self.logger.info(f"Disconnected from QdrantDB")
    
    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            self.client.delete_collection(collection_name)
            self.logger.info(f"Collection {collection_name} deleted successfully")
        else:
            self.logger.warning(f"Collection {collection_name} does not exist")

    def create_collection(self, collection_name: str,
                          embedding_size: int,
                          do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name)

        if not self.is_collection_existed(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_method)
            )
            return True
        return False
    
    def insert_one(self, collection_name: str,
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
    
    def instert_many(self, collection_name: str,
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
    
    def search_by_vector(self, collection_name: str,
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
    
    