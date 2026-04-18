from pydantic import BaseModel
from typing import Optional

class IndexPushRequest(BaseModel):
    do_reset: Optional[int] = 0

class IndexSearchRequest(BaseModel):
    text: str
    limit: Optional[int] = 5 