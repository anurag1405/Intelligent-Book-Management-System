from fastapi import APIRouter, Depends, HTTPException, status
from models.user import UserCreate, UserLogin
from utils.jwt_handler import create_access_token, decode_access_token,oauth2_scheme
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db_connection
import jwt
from fastapi.responses import JSONResponse

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Check if username exists
async def check_username(username):
    conn = await get_db_connection()  
    try:
        result = await conn.fetchrow("SELECT username FROM users WHERE username = $1", username)
        if result:
            # If the username exists, raise an exception with a clear message
            raise HTTPException(status_code=400, detail="Username already exists")
        return {"message": "Username is available"}
    except Exception as e:
        print(f"Error checking username: {e}")  # Log the error for debugging
        raise e
    finally:
        await conn.close()

# Check if email exists
async def check_email(email):
    conn = await get_db_connection()  
    try:
        result = await conn.fetchrow("SELECT email FROM users WHERE email = $1", email)
        if result:
            raise HTTPException(status_code=400, detail="Email already exists")
        return {"message": "Email is available"}
    except Exception as e:
        raise e
    finally:
        await conn.close()

# Register Route
@router.post("/register")
async def register(user: UserCreate):
    conn = await get_db_connection()
    try:
        # Check if username exists
        await check_username(user.username)
        # Check if email exists
        await check_email(user.email)
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        await conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES ($1, $2, $3)",
            user.username, user.email, hashed_password
        )
        return {"msg": "User registered successfully"}

    except HTTPException as e:
        raise e  
    except Exception as e:
        raise e
    finally:
        await conn.close()

# Login Route
@router.post("/login")
async def login(user: UserLogin, response:JSONResponse):
    conn = await get_db_connection()
    try:
        db_user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", user.username)
        if not db_user or not verify_password(user.password, db_user['hashed_password']):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        token = create_access_token(data={"sub": db_user['username']})
        response.set_cookie(key="access_token", value=token, httponly=True, secure=True)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        await conn.close()

# Middleware to protect routes
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Return the user (you may fetch user details from the database using username if needed)
    return {"username": username}

