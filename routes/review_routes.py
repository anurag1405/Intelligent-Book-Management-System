from fastapi import APIRouter, HTTPException, Depends
from models.review import Review
from utils.jwt_handler import get_current_user
from database import get_db_connection
router = APIRouter()

@router.post("/books/{id}/reviews")
async def create_review(id: int, new_review: Review,current_user: dict=Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        book = await conn.fetchrow('SELECT * FROM books WHERE id = $1', id)
        if book is None:
            raise HTTPException(status_code=404, detail="No book present with the given ID")
        
        await conn.execute(
            'INSERT INTO reviews (book_id, user_id, review_text, rating) VALUES ($1, $2, $3, $4)',
            id, current_user['username'], new_review.review_text, new_review.rating
        )
        return {"message": "Review added"}
    finally:
        await conn.close()
    

@router.get("/books/{id}/reviews")
async def get_reviews(id: int,current_user: dict=Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        reviews = await conn.fetch('SELECT * FROM reviews WHERE book_id = $1', id)
        return [dict(review) for review in reviews]
    finally:
        await conn.close()
