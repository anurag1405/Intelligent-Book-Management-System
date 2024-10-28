from pydantic import BaseModel

class Review(BaseModel):
    review_text: str
    rating: float
