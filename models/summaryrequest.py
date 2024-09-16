from pydantic import BaseModel

class SummaryRequest(BaseModel):
    id: int
    content: str