from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    id: Optional[ObjectId]  = Field(default=None, alias="_id") # allows us to use 'id' instead of '_id' when creating a DataChunk object, but it will be stored in MongoDB as '_id'
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: ObjectId
    
    # Tells Pydantic to accept fields typed with Python classes it doesn't know how to validate (ObjectID)
    class Config:
        arbitrary_types_allowed = True