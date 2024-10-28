import faiss
import pickle
from database import get_db_connection
from fastapi import HTTPException
import numpy as np
import mlflow.pyfunc
import pandas as pd


model_name = "Best_SVD_Model"
model_uri = f"models:/{model_name}/latest"
model = mlflow.pyfunc.load_model(model_uri=model_uri)


with open('artifacts/vectorizer.pkl','rb') as f:
    vectorizer = pickle.load(f)

k = 11
async def load_faiss():
    index = index = faiss.read_index("artifacts/faiss_books_index.index")
    return index

async def content_based(title, k=20):
    conn = await get_db_connection()  
    try:
        index = await load_faiss()
        book_record = await conn.fetchrow("SELECT id, faiss_index FROM books WHERE title = $1", title)
        if not book_record:
            return f"No book found with the title '{title}'"
    
        book_id = book_record['id']
        faiss_index = book_record['faiss_index']
        book_vector = index.reconstruct(faiss_index).reshape(1, -1)
        distances, indices = index.search(book_vector, k)
        recommended_book_ids = await conn.fetch("SELECT id FROM books WHERE faiss_index = ANY($1::int[])", indices[0])
        recommended_book_ids = [record['id'] for record in recommended_book_ids]
        if book_id in recommended_book_ids:
            recommended_book_ids.remove(book_id)
        
        return recommended_book_ids
    
    finally:
        await conn.close()

async def hybrid_recommendations(username, title):
    k = 10
    book_ids = await content_based(title)
    predicted_ratings = []
    conn = await get_db_connection()
    
    try:
        record = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)  
        if not record:
            raise HTTPException(status_code=404, detail="User not found")
        user_encoded = record['id'] 
        for id in book_ids:
            input_data = pd.DataFrame({
                "user_id": pd.Series(user_encoded, dtype='int32'),  # Explicitly set dtype to int32
                "item_id": pd.Series(id, dtype='int32')   # Explicitly set dtype to int32
            })
            prediction = model.predict(input_data)
            predicted_ratings.append((id, prediction))
        collaborative_book_ids = [book_id for book_id, _ in sorted(predicted_ratings, key=lambda x: -x[1])[:k]]
        if collaborative_book_ids:
            books = await conn.fetch(
                "SELECT id, title, summary FROM books WHERE id = ANY($1::int[])",
                collaborative_book_ids
            )
            return books
        return []  # Return an empty list if no books are found

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    finally:
        await conn.close()


async def add_newbook_to_faiss(new_book):
    index = await load_faiss()
    metadata = new_book.title + " " + new_book.author + " " + new_book.genre + " " + new_book.summary
    tfidf_vectors = vectorizer.transform([metadata])  # Wrap metadata in a list to ensure it's treated as a single sample
    dense_vectors = tfidf_vectors.toarray().astype(np.float32)
    current_faiss_size = index.ntotal
    index.add(dense_vectors)
    faiss.write_index(index, "faiss_books_index.index")
    new_faiss_index = current_faiss_size  # This is the FAISS index of the newly added vector
    return new_faiss_index
