from fastapi import APIRouter, HTTPException,Depends
from utils.jwt_handler import get_current_user
from models.book import Book
from database import get_db_connection
import asyncpg

router = APIRouter()

@router.get("/books")
async def get_books(current_user: dict= Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        books = await conn.fetch('SELECT * FROM books')
        return [dict(book) for book in books]
    finally:
        await conn.close()

@router.get("/books/{id}")
async def get_book(id: int,current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        book = await conn.fetchrow('SELECT * FROM books WHERE id = $1', id)
        if book:
            return dict(book)
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    finally:
        await conn.close()

@router.post("/books")
async def create_book(new_book: Book,current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        book_id = await conn.fetchval(
            'INSERT INTO books (title, author, genre, year_published, summary) VALUES ($1, $2, $3, $4, $5) RETURNING id',
            new_book.title, new_book.author, new_book.genre, new_book.year_published, new_book.summary
        )
        return {"id": book_id, "message": "Book added successfully"}
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Unique constraint violation")
    finally:
        await conn.close()
    

@router.put("/books/{id}")
async def update_book(id: int, updated_book: Book,current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        await conn.execute(
            'UPDATE books SET title = $1, author = $2, genre = $3, year_published = $4,summary=$5 WHERE id = $6',
            updated_book.title, updated_book.author, updated_book.genre, updated_book.year_published,update_book.summary, id
        )
        return {"message": "Book updated"}
    finally:
        await conn.close()

@router.delete("/books/{id}")
async def delete_book(id: int,current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        await conn.execute('DELETE FROM books WHERE id = $1', id)
        return {"message": "Book deleted"}
    finally:
        await conn.close()
