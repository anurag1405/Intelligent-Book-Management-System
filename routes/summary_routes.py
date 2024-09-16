from fastapi import APIRouter, HTTPException,Depends
from models.summaryrequest import SummaryRequest
from database import get_db_connection
from utils.summarization import generate_summary
from utils.jwt_handler import get_current_user


router = APIRouter()

@router.post("/summary")
async def summary(data: SummaryRequest,current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        if data.id is None:
            summary=generate_summary(data.content)
            return [{"summary": summary}]
        summary = await conn.fetchrow(
            """SELECT summary FROM books WHERE id = $1""", data.id
        )

        if summary is None:
            summary=generate_summary(data.content)
            return [{"summary": summary}]
        text = summary['summary'] + data.content
        summary=generate_summary(text)
        return [{"summary": summary}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        await conn.close()
