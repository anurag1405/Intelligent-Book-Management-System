from database import get_db_connection
import pandas as pd
from fastapi import HTTPException
import os

# Get the directory of the current file (DAG)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Set the path to the Model_Training directory


async def get_books():
    try:
        conn = await get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection is None.")
        query = "SELECT U.id, r.book_id, r.rating FROM reviews r JOIN users U ON r.user_id = U.username;"
        rows = await conn.fetch(query=query)
        df = pd.DataFrame(rows, columns=['id', 'book_id', 'rating'])
        df.to_csv(os.path.join(base_dir, "training.csv"),index=False)
       #return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(get_books())