from pydantic import BaseModel

class Book(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int
    summary: str
