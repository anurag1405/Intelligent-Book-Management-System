import joblib
import pandas as pd
import asyncpg
from database import get_db_connection
from fastapi import HTTPException

kmeans = joblib.load('Recommendation.pkl')
scaler = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

async def books_recommended(title):
    print(title)
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Fetch the genre and average rating of the book
        result = await conn.fetchrow(
            """
            SELECT b.genre, round(AVG(r.rating),1) as avg_rating
            FROM books b
            JOIN reviews r ON b.id = r.book_id
            WHERE b.title = $1
            GROUP BY b.id, b.genre
            """,
            title
        )

        if result is None:
            return {"message": "No current recommendations matching"}

        genre, avg_rating = result['genre'], result['avg_rating']

        # Encode the genre and scale the input
        genre_encoded = label_encoder.transform([genre])[0]
        X_input = scaler.transform([[genre_encoded, avg_rating]])

        # Predict the cluster for the input book
        cluster = kmeans.predict(X_input)[0]

        # Fetch all books and their ratings
        rows = await conn.fetch(
            """
            SELECT b.id, b.title, b.author, b.genre, AVG(r.rating) AS rating
            FROM books b
            JOIN reviews r ON b.id = r.book_id
            GROUP BY b.id, b.title, b.author, b.genre
            """
        )

        if not rows:
            return {"message": "No books found in the database"}

        # Convert rows into a pandas DataFrame
        books_list = [dict(row) for row in rows]  # Convert each row (Record) to a dictionary
        books_df = pd.DataFrame(books_list, columns=['id', 'title', 'author', 'genre', 'rating'])

        # Encode the genre column
        books_df['genre_encoded'] = label_encoder.transform(books_df['genre'])

        # Scale the features
        features = scaler.transform(books_df[['genre_encoded', 'rating']])

        # Predict clusters for all books
        books_df['cluster'] = kmeans.predict(features)

        # Filter books in the same cluster and exclude the current book
        recommendations = books_df[(books_df['cluster'] == cluster) & (books_df['title'] != title)][['title', 'author']]

        if recommendations.empty:
            return {"message": "No current recommendations matching"}

        # Return recommendations as a dictionary
        return recommendations.to_dict(orient='records')

    except asyncpg.PostgresError as db_error:
        raise HTTPException(status_code=500, detail=f"Database query error: {db_error}")
    finally:
        await conn.close()
