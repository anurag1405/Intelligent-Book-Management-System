from pydantic import BaseModel

class Review(BaseModel):
    user_id: int
    review_text: str
    rating: float
