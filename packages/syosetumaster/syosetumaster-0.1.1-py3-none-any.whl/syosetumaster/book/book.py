

from pydantic import BaseModel

class Book(BaseModel):
    text: str
    