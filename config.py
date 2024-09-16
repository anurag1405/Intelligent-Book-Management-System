import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY =os.getenv("GROQ_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
USER=os.getenv("USER") 
PASSWORD=os.getenv("PASSWORD")
DATABASE=os.getenv("DATABASE")
HOST=os.getenv("HOST")
