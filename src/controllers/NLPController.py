from .BaseController import BaseController
from models.mongodb_schemas.project import Project
from models.mongodb_schemas.data_chunk import DataChunk
from typing import List 
from stores.llm.LLMEnums import EmbeddingDocumentTypeEnums
import json

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id: str):
      return f"collection_{project_id}".strip()
    
    def reset_vectordb_collection(self, project: Project):
       collection_name = self.create_collection_name(project.project_id)
       return self.vectordb_client.delete_collection(collection_name)
    
    def get_vectordb_collection_info(self, project: Project):
       collection_name = self.create_collection_name(project.project_id)
       collection_info = self.vectordb_client.get_collection_info(collection_name)
       
       #return collection_info
       return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
       )
    
    def index_into_vectordb(self, project: Project, 
                            chunks: List[DataChunk], 
                            chunks_ids: List[int], 
                            do_reset: bool = False):
        # get collection name
        # manage items
        # create collection if not exist
        # insert items into collection

        collection_name = self.create_collection_name(project.project_id)

        texts = [chunk.chunk_text for chunk in chunks]
        metadatas = [chunk.chunk_metadata for chunk in chunks]
        vectors = [
           self.embedding_client.embed_text(text, document_type=EmbeddingDocumentTypeEnums.DOCUMENT.value)
           for text in texts
        ]
 
        _ = self.vectordb_client.create_collection(
           collection_name=collection_name,
           embedding_size = self.embedding_client.embedding_size,
           do_reset=do_reset
        )

        _ = self.vectordb_client.instert_many(
           collection_name=collection_name,
           texts = texts,
           vectors = vectors,
           metadatas = metadatas,
           record_ids=chunks_ids 
        )
        return True
    
    def search_vectordb_collection(self, project: Project, text: str, limit: int = 10):
        # get collection name
        # get text embedding vector
        # do semantic search

      collection_name = self.create_collection_name(project.project_id)
      
      query_vector = self.embedding_client.embed_text(text, document_type=EmbeddingDocumentTypeEnums.QUERY.value)
      if not query_vector or len(query_vector) == 0:
         return False
      
      results = self.vectordb_client.search_by_vector(
         collection_name=collection_name,
         vector=query_vector,
         limit=limit
      )

      if not results:
         return False 

      return json.loads(
            json.dumps(results, default=lambda x: x.__dict__)
       )
      
      


       

   
