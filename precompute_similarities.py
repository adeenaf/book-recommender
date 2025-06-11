import sqlite3
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
from sklearn.preprocessing import normalize
import numpy as np
from joblib import Parallel, delayed, parallel_backend
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Jaccard similarity
def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

conn = sqlite3.connect('books.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Fetch all necessary info
books = cur.execute("SELECT id, title, author, description, genres FROM books WHERE description != ''").fetchall()

# Prepare data
book_ids = [book['id'] for book in books]
descriptions = [book['description'] for book in books]
authors = [book['author'].lower().strip() for book in books]
genres_list = [set(g.strip().lower() for g in book['genres'].split(',')) for book in books]

# Vectorize descriptions
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(descriptions)

# Normalize vectors
tfidf_matrix = normalize(tfidf_matrix)

# Function to compute hybrid similarity for a single book
def compute_similarity(i):
    cosine_sim = cosine_similarity(tfidf_matrix[i], tfidf_matrix).flatten()
    hybrid_scores = []

    for j in range(len(books)):
        if i == j:
            continue

        # Compute genre similarity (primary factor)
        genre_sim = jaccard_similarity(genres_list[i], genres_list[j])

        # Compute description similarity (secondary factor)
        description_sim = cosine_sim[j]

        # Compute author penalty (tertiary factor)
        author_bonus = -0.1 if authors[i] == authors[j] else 0

        # Final hybrid score with adjusted weights for genre, description, and author
        score = 0.5 * genre_sim + 0.4 * description_sim + author_bonus
        hybrid_scores.append((j, score))

    # Sort by hybrid score and select the top 30 most relevant books
    top_similar = sorted(hybrid_scores, key=lambda x: x[1], reverse=True)[:30]

    # Filter out books from the same author unless they have a high similarity score
    filtered_similar = []
    for book_idx, score in top_similar:
        book = books[book_idx]
        book_genres = set(book['genres'].lower().split(','))
        book_author = book['author'].lower()

        # Allow books from the same author only if the score is very high
        if book_author == books[i]['author'].lower() and score < 0.8:
            continue

        # Add the book to the filtered list
        filtered_similar.append((book_ids[book_idx], score))

    return book_ids[i], filtered_similar

# Parallelize similarity computation across all books
similarity_data = {}

# Parallel processing with periodic saving
def save_periodically(i, similarity_data):
    if i % 100 == 0:
        with open(f'similarities_partial_{i}.json', 'w') as f:
            json.dump(similarity_data, f)

# Use joblib to parallelize the similarity computation
with parallel_backend('threading', n_jobs=-1):
    results = Parallel(n_jobs=-1)(delayed(compute_similarity)(i) for i in tqdm(range(len(books))))

# Save the results into similarity_data
for i, (book_id, similar_books) in enumerate(results):
    similarity_data[book_id] = [book_id for book_id, _ in similar_books]
    save_periodically(i, similarity_data)  # Save periodically

# Save the final selection in the similarity data
with open('similarities.json', 'w') as f:
    json.dump(similarity_data, f)

conn.close()
logging.info("Finished similarity computation.")
