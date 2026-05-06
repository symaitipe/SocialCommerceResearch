from pydantic import BaseModel
from typing import List, Optional

class CommentInput(BaseModel):
    text: str

class BatchInput(BaseModel):
    comments: List[str]

class CommentResult(BaseModel):
    text: str
    language: str
    intent: str
    sentiment: str