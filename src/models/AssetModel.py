from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums.DatabaseEnums import DatabaseEnum
from bson import ObjectId
from sqlalchemy.future import select

class AssetModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client) # creates an instance of the AssetModel class, passing the db_client to the constructor
        return instance

    
    async def create_asset(self, asset: Asset):
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset

    async def get_asset(self, asset_project_id: int, asset_name: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(Asset.asset_project_id == asset_project_id, Asset.asset_name == asset_name)
                result = await session.execute(query)
                asset = result.scalar_one_or_none()
        return asset
    
    async def get_all_project_assets(self, asset_project_id: int, asset_type: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(Asset.asset_project_id == asset_project_id, Asset.asset_type == asset_type)
                result = await session.execute(query)
                assets = result.scalars().all()
        return assets   
    

    