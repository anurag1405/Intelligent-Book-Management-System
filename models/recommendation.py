from pydantic import BaseModel

class RecommendationRequest(BaseModel):
    title: str