from .BaseController import BaseController
from models.db_schemas.minirag.schemas.project import Project
from models.db_schemas.minirag.schemas.data_chunk import DataChunk
from typing import List 
from stores.llm.LLMEnums import EmbeddingDocumentTypeEnums
import json

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client, template_parser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

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

      # return json.loads(
      #       json.dumps(results, de fault=lambda x: x.__dict__)
      #  )
      return results
    
    def answer_query(self, project: Project, query: str, limit: int = 10):
       #retrieve relevant chunks from vectordb
       #construct LLM prompt

       response, final_prompt, chat_history = None, None, None

       retrieved_chunks = self.search_vectordb_collection(project, query, limit)
       if not retrieved_chunks:
          return response, final_prompt, chat_history
       
       system_prompt = self.template_parser.get_prompt(
          group = "rag",
          key = "system_prompt"
       )
       
       document_prompts = "\n".join([
            self.template_parser.get_prompt(
               group = "rag",
               key = "document_prompt",
               vars={
                  "doc_num": i+1,
                  "chunk_text": self.generation_client.process_text(doc.text)
               }
            )
            for i, doc in enumerate(retrieved_chunks)
         ])
       
       footer_promt = self.template_parser.get_prompt(
          group = "rag",
          key = "footer_prompt",
          vars={
            "query": query
          }
       )

       chat_history = [
          self.generation_client.construct_prompt(
             prompt=system_prompt,
             role = self.generation_client.enums.ROLE_SYSTEM.value
          ) 
       ]

       final_prompt = "\n\n".join([document_prompts, footer_promt])

       response = self.generation_client.generate_text(
          prompt=final_prompt,
          chat_history=chat_history
       )

       return response, final_prompt, chat_history
 
 
       

   
