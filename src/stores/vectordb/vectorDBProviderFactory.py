from .providers import QdrantDBProvider, PgVectorProvider
from .vectorDBEnums import vectorDBEnums
from controllers.BaseController import BaseController 
from sqlalchemy.orm import sessionmaker 

class vectorDBProviderFactory:
    
    def __init__(self, config: dict, db_client: sessionmaker = None):
        self.config = config
        self.base_controller = BaseController()
        self.db_client = db_client

    def create_provider(self, provider: str):
        if provider == vectorDBEnums.QDRANT.value:
            db_client = self.base_controller.get_database_path(self.config.VECTOR_DB_PATH)
            
            return QdrantDBProvider(
                db_client=db_client,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                index_threshold=self.config.VECTOR_DB_PGVECTOR_INDEX_THRESHOLD
            )
        elif provider == vectorDBEnums.PGVECTOR.value:
            db_client = self.db_client

            return PgVectorProvider(
                db_client=db_client,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                index_threshold=self.config.VECTOR_DB_PGVECTOR_INDEX_THRESHOLD
            )
        return None