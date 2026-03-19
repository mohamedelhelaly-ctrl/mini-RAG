from .BaseDataModel import BaseDataModel
from .mongodb_schemas import Asset
from .enums.DatabaseEnums import DatabaseEnum
from bson import ObjectId

class AssetModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DatabaseEnum.COLLECTION_ASSET_NAME.value]
    
    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client) # creates an instance of the AssetModel class, passing the db_client to the constructor
        await instance.init_collection()
        return instance
    
    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DatabaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            self.db_client[DatabaseEnum.COLLECTION_ASSET_NAME.value]
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index.get("unique", False) # unique = index["unique"] if "unique" in index else False
                )
    
    async def create_asset(self, asset: Asset):
        result = await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))  # insert_one takes a dict, we need to convert the Asset object to a dict  
        asset.id = result.inserted_id
        return asset
    
    async def get_all_project_assets(self, asset_project_id: str):
        return await self.collection.find({
            "asset_project_id": ObjectId(asset_project_id) 
            if isinstance(asset_project_id, str) else asset_project_id
        }).tolist(length=None)
    

    