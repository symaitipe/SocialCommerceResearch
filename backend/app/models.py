from pydantic import BaseModel
from typing import List, Optional

class CommentInput(BaseModel):
    text: str
    product_category: Optional[str] = 'general'

class BatchInput(BaseModel):
    comments: List[str]
    product_category: Optional[str] = 'general'

class CommentResult(BaseModel):
    text: str
    language: str
    intent: str
    sentiment: str