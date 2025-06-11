import csv
import sqlite3

conn = sqlite3.connect("books.db")
cur = conn.cursor()

with open("books.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            UPDATE books
            SET series = ?,
                language = ?,
                pages = ?,
                reviews = ?
            WHERE title = ? AND author = ?
        """, (
            row['series'],
            row['language'],
            row['pages'],
            row['numRatings'],
            row['title'],
            row['author']
        ))

conn.commit()
conn.close()
