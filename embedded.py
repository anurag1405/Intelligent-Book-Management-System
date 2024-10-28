from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
import numpy as np
import pandas as pd
import psycopg2
from config import USER, PASSWORD, DATABASE, HOST
import pickle

# Database connection setup
def get_db_connection():
    try:
        connection = psycopg2.connect(
            user=USER, 
            password=PASSWORD, 
            database=DATABASE, 
            host=HOST
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Fetch all books from the database
def fetch_all_books():
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database.")
        return None
    
    query = "SELECT id, title, summary, author, genre FROM books"
    
    try:
        books_df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching data from the database: {e}")
        return None

    return books_df

# Create FAISS index for the books
def create_faiss_index(books_df):
    dimension = 512  # Adjust based on your use case
    index = faiss.IndexFlatL2(dimension)

    # Initialize TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=dimension)

    # Combine title, author, genre, and summary into a single text field
    texts = books_df['title'] + " " + books_df['author'] + " " + books_df['genre'] + " " + books_df['summary']

    # Transform texts into TF-IDF vectors
    tfidf_vectors = vectorizer.fit_transform(texts)
    dense_vectors = tfidf_vectors.toarray().astype(np.float32)

    # Add vectors to FAISS index
    index.add(dense_vectors)

    return index, vectorizer

# Update the FAISS index values for each book in Postgres
def update_faiss_index_in_db(books_df, index):
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database.")
        return
    
    try:
        cursor = conn.cursor()

        # Update FAISS index value for each book in the database
        for i, book_id in enumerate(books_df['id']):
            query = "UPDATE books SET faiss_index = %s WHERE id = %s"
            cursor.execute(query, (i, book_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("FAISS index values updated in the database.")
    except Exception as e:
        print(f"Error updating the database: {e}")

# Main logic
books_df = fetch_all_books()

if books_df is not None:
    books_df = books_df.fillna("")  # Fill missing summaries

    # Create FAISS index and vectorizer
    faiss_index, vectorizer = create_faiss_index(books_df)

    with open('vectorizer.pkl', 'wb') as f:
                pickle.dump(vectorizer, f)

    # Save FAISS index to disk
    faiss.write_index(faiss_index, "faiss_books_index.index")

    # Update FAISS index in Postgres for past books
    update_faiss_index_in_db(books_df, faiss_index)

    print("FAISS index created and saved, and Postgres updated.")
