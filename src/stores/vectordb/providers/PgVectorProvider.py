from ..vectorDBInterface import vectorDBInterface
from ..vectorDBEnums import PgVectorDistanceMethodEnums, PgVectorTableSchemaEnums, PgVectorIndexTypeEnums, DistanceMethodEnums
from typing import List
from models.db_schemas.minirag.schemas.data_chunk import RetrievedDocument
from sqlalchemy.sql import text as sql_query
import json
import logging

class PgVectorProvider(vectorDBInterface):
    def __init__(self, db_client, default_vector_size: int = 768, 
                 distance_method: str = None, index_threshold: int = 1000):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold
        self.pgvector_prefix = PgVectorTableSchemaEnums._PREFIX.value

        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"
        
        if distance_method == DistanceMethodEnums.COSINE.value:
            self.default_distance_method = PgVectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.default_distance_method = PgVectorDistanceMethodEnums.DOT.value

        
        self.logger = logging.getLogger("uvicorn")
    
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                 await session.execute(sql_query(
                     "CREATE EXTENSION IF NOT EXISTS vector"
                 ))
                 await session.commit()
    
    def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        record = None
        async with self.db_client() as session:
            async with session.begin():
                list_table_query = sql_query(
                    f'SELECT tablename FROM pg_tables WHERE tablename = :collection_name'
                )
                results = await session.execute(list_table_query, {"collection_name": collection_name})
                record = results.scalar_one_or_none()
        return record is not None
    
    async def list_all_collections(self) -> List: 
        records = []
        async with self.db_client() as session:
            async with session.begin():
                list_tables_query = sql_query(
                    "SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix" # LIKE operator in SQL is used to search for a specified pattern in a column.
                )
                results = await session.execute(list_tables_query, {"prefix": self.pgvector_prefix})
                records = results.scalars().all()
        return records
    
    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            async with session.begin():
                table_info_query = sql_query(f'''
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name
                ''')

                count_records_query = sql_query(
                    f"SELECT COUNT(*) FROM {collection_name}"
                )

                table_info = await session.execute(table_info_query, {"collection_name": collection_name})
                count_records = await session.execute(count_records_query)

                table_data = table_info.fetchone()
                if not table_data:
                    return None
                
                return {
                    "table_info ": {
                        "schemaname": table_data[0],
                        "tablename": table_data[1],
                        "tableowner": table_data[2],
                        "tablespace": table_data[3],
                        "hasindexes": table_data[4]
                    },
                    "no_of_records": count_records.scalar_one()
                }

    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection {collection_name}...")

                delete_query = sql_query(
                    f"DROP TABLE IF EXISTS {collection_name}"
                )
                await session.execute(delete_query)
                await session.commit()
            

    async def create_collection(self, collection_name: str,
                                embedding_size: int = None, 
                                distance_method: str = None,
                                do_reset: bool = False):
        if do_reset:
            _ = await self.delete_collection(collection_name)
        
        if not await self.is_collection_existed(collection_name):
            self.logger.info(f"Creating collection {collection_name}...")

            async with self.db_client() as session:
                async with session.begin():
                    create_table_query = sql_query(
                        f"CREATE TABLE {collection_name} ("
                            f"{PgVectorTableSchemaEnums.ID.value} bigserial PRIMARY KEY, "
                            f"{PgVectorTableSchemaEnums.TEXT.value} text, "
                            f"{PgVectorTableSchemaEnums.VECTOR.value} vector({embedding_size or self.default_vector_size}), "
                            f"{PgVectorTableSchemaEnums.METADATA.value} jsonb DEFAULT \'{{}}\', " # jsonb better for read ops, json better for write ops
                            f"{PgVectorTableSchemaEnums.CHUNK_ID.value} bigint, "
                            f"FOREIGN KEY ({PgVectorTableSchemaEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)"
                        ")"
                    ) 
                    await session.execute(create_table_query)
                    await session.commit()
                    self.logger.info(f"Collection {collection_name} created successfully")
            return True
        
        # self.logger.info(f"Collection {collection_name} already exists")
        return False

    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                check_index_query = sql_query(f"""
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = :collection_name AND indexname = :index_name
                """)
                result = await session.execute(check_index_query, {"collection_name": collection_name, "index_name": index_name})
                record = result.scalar_one_or_none()
                return record is not None
            
    
    async def create_index(self, collection_name: str, 
                           index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        
        is_index_existed = await self.is_index_existed(collection_name)
        if is_index_existed:
            # self.logger.info(f"Index for collection {collection_name} already exists")
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_records_query = sql_query(
                    f"SELECT COUNT(*) FROM {collection_name}"
                )
                count_records = await session.execute(count_records_query)
                no_of_records = count_records.scalar_one()
                if no_of_records < self.index_threshold:
                    return False
                
                self.logger.info(f"START: Creating index for collection {collection_name}...")
                index_name = self.default_index_name(collection_name)
                create_index_query = sql_query(
                    f"CREATE INDEX {index_name} ON {collection_name} "
                    f"USING {index_type} ({PgVectorTableSchemaEnums.VECTOR.value} {self.default_distance_method})"
                )
                await session.execute(create_index_query)
                await session.commit()
                self.logger.info(f"END: Index for collection {collection_name} created successfully")
                return True
        

    async def reset_index(self, collection_name: str, 
                          index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                drop_index_query = sql_query(
                    f"DROP INDEX IF EXISTS {index_name}"
                )
                await session.execute(drop_index_query)
                await session.commit()
                self.logger.info(f"Index for collection {collection_name} dropped successfully")
        
        return self.create_index(collection_name, index_type)





    async def insert_one(self, collection_name: str,
                         text: str,
                         vector: list,
                         metadata: dict = None,
                         record_id: str = None):
        
        if not await self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist.")
            return False
        if not record_id:
            self.logger.warning(f"record_id is required for inserting a record in collection {collection_name}.")
            return False
        
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
        async with self.db_client() as session:
            async with session.begin():
                insert_query = sql_query(
                    f"INSERT INTO {collection_name} "
                    f"({PgVectorTableSchemaEnums.TEXT.value}, {PgVectorTableSchemaEnums.VECTOR.value}, {PgVectorTableSchemaEnums.METADATA.value}, {PgVectorTableSchemaEnums.CHUNK_ID.value}) " 
                    "VALUES (:text, :vector, :metadata, :chunk_id) "
                )
                await session.execute(insert_query, {
                    "text": text,
                    "vector": "[" + ",".join([str(v) for v in vector]) + "]", # convert list to string representation of list to be inserted in the vector column
                    "metadata": metadata_json  ,
                    "chunk_id": record_id 
                })
                await session.commit()
        await self.create_index(collection_name) 
        return True
        
    async def instert_many(self, collection_name: str,
                          texts: list,
                          vectors: list,
                          metadatas: list = None,
                          record_ids: list = None,
                          batch_size: int = 50):
        
        if not await self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist.")
            return False
        
        if len(vectors) != len(record_ids):
            self.logger.warning(f"Length of vectors and record_ids must be the same for inserting records in collection {collection_name}.")
            return False
        
        if not metadatas or len(metadatas)==0:
            metadatas = [None] * len(vectors)
        
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(record_ids), batch_size):
                    batch_texts = texts[i: i + batch_size]
                    batch_vectors = vectors[i: i + batch_size]
                    batch_metadatas = metadatas[i: i + batch_size]
                    batch_record_ids = record_ids[i: i + batch_size]

                    values = []
                    for text, vector, metadata, record_id in zip(batch_texts, batch_vectors, batch_metadatas, batch_record_ids):
                        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else "{}" 
                        values.append({
                            'text': text,
                            'vector': "[" + ",".join([str(v) for v in vector]) + "]",
                            'metadata': metadata_json,
                            'chunk_id': record_id
                        })

                    insert_batch_query = sql_query(
                        f"INSERT INTO {collection_name} "
                        f"({PgVectorTableSchemaEnums.TEXT.value}, {PgVectorTableSchemaEnums.VECTOR.value}, {PgVectorTableSchemaEnums.METADATA.value}, {PgVectorTableSchemaEnums.CHUNK_ID.value}) " 
                        "VALUES (:text, :vector, :metadata, :chunk_id) "
                    )
                    await session.execute(insert_batch_query, values)
                    await session.commit()

        await self.create_index(collection_name) # create index after inserting each batch to ensure the index is updated with the new records, and also to avoid long index creation time for large number of records inserted in one batch
        
        return True
    
    async def search_by_vector(self, collection_name: str,
                               vector: list,
                               limit: int) -> List[RetrievedDocument]: 
        if not await self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist.")
            return False
        
        vector = "[" + ",".join([str(v) for v in vector]) + "]"

        async with self.db_client() as session:
            async with session.begin():
                search_query = sql_query(
                    f'SELECT {PgVectorTableSchemaEnums.TEXT.value} as text,  '
                    f'1 - ({PgVectorTableSchemaEnums.VECTOR.value} <=> :vector) as score ' # cosine similarity = 1 - cosine distance, vector <=> vector is the operator for calculating the distance between two vectors in pgvector
                    f'FROM {collection_name} '
                    'ORDER BY score DESC '
                    f'LIMIT {limit}'
                )
                results = await session.execute(search_query, {"vector": vector})
                records = results.fetchall()

                return [
                    RetrievedDocument(
                        text=record.text,
                        score=record.score
                    )
                    for record in records
                ]


                 