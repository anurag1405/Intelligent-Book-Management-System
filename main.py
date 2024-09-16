from fastapi import FastAPI
from routes import book_routes, review_routes, recommendation_routes,summary_routes,auth_routes
from database import get_db_connection

app = FastAPI()

# Include routes
app.include_router(book_routes.router)
app.include_router(review_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(summary_routes.router)
app.include_router(auth_routes.router, prefix="/auth") 

@app.on_event("startup")
async def startup():
    await get_db_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
