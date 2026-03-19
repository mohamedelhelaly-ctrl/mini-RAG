from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class Asset(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id") # allows us to use 'id' instead of '_id' when creating a DataChunk object, but it will be stored in MongoDB as '_id'
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: int = Field(ge=0, default=None) # size in bytes
    asset_config: dict = Field(default=None)
    asset_pushed_at: datetime = Field(default=datetime.utcnow())

    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("asset_project_id", 1)
                ],
                "name": "asset_project_id_index",
                "unique": False
            },
            {
                "key": [
                    ("asset_project_id", 1),
                    ("asset_name", 1)
                ],
                "name": "asset_project_id_name_index",
                "unique": True
            }
        ]
