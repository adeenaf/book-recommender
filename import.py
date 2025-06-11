import csv
import sqlite3

conn = sqlite3.connect("books.db")
cur = conn.cursor()

with open("books.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            INSERT INTO books (title, author, rating, description, genres)
            VALUES (?, ?, ?, ?, ?)
        """, (
            row['title'],
            row['author'],
            float(row['rating']) if row['rating'] else None,
            row['description'],
            row['genres'],
        ))

conn.commit()
conn.close()
