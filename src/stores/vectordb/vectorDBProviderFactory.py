from .providers import QdrantDBProvider
from .vectorDBEnums import vectorDBEnums
from controllers.BaseController import BaseController 

class vectorDBProviderFactory:
    
    def __init__(self, config: dict):
        self.config = config
        self.base_controller = BaseController()

    def create_provider(self, provider: str):
        if provider == vectorDBEnums.QDRANT.value:
            db_path = self.base_controller.get_database_path(self.config.VECTOR_DB_PATH)
            
            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD
            )
        return None