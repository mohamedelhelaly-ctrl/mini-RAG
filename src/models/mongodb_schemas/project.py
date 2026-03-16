from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class Project(BaseModel):
    _id: Optional[ObjectId]
    project_id: str = Field(...,min_length=1)

    @validator('project_id')
    def validate_project_id(cls, v):
        if not v:
            raise ValueError('Project ID is required')
        elif not v.isalnum():
            raise ValueError('Project ID must be alphanumeric')
        return v

    # Tells Pydantic to accept fields typed with Python classes it doesn't know how to validate (ObjectID)
    class Config:
        arbitrary_types_allowed = True