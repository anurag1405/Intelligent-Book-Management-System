from fastapi import APIRouter,Depends
from models.recommendation import RecommendationRequest
from utils.book_recommendations import books_recommended
from utils.jwt_handler import get_current_user

router = APIRouter()

@router.post("/recommendations")
async def get_recommendations(data: RecommendationRequest,current_user: dict = Depends(get_current_user)):
    books=await books_recommended(data.title)
    return books
    
    
