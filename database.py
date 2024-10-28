from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import USER,PASSWORD,DATABASE,HOST
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
import asyncpg


# Database engine and session setup
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_connection():
    try:
        connection = await asyncpg.connect(
            user=USER, 
            password=PASSWORD, 
            database=DATABASE, 
            host=HOST
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
