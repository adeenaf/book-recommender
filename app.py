from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import unquote
import sqlite3
import json
import ast
import re


app = Flask(__name__)

app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.template_filter('parse_genres')
def parse_genres_filter(value):
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
        return [value]
    except:
        return [value]

# Function to connect to database
def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

def get_series_name(series_str):
    if series_str and '#' in series_str:
        return series_str.split('#')[0].strip()
    else:
        return None

@app.context_processor
def inject_genre_icons():
    genre_icons = {
        'Default': 'bi-book'
    }
    return dict(genre_icons=genre_icons)

@app.route('/')
def index():
    conn = get_db_connection()
    popular_genres = ['Fantasy', 'Romance', 'Science Fiction', 'Mystery', 'Thriller', 'Nonfiction']
    genre_books = {}

    for genre in popular_genres:
        books = conn.execute("""
            SELECT id, title, author FROM books 
            WHERE genres LIKE ?
            ORDER BY RANDOM() LIMIT 15 
        """, (f'%{genre}%',)).fetchall()

        genre_books[genre] = books

    conn.close()
    return render_template('index.html', genre_books=genre_books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect('/')
        else:
            flash('Invalid username or password', 'danger')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        # Check if the passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_pw = generate_password_hash(password)

        # Database connection
        conn = get_db_connection()

        try:
            # Insert user into the database
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
        except sqlite3.IntegrityError:
            # Handle the case where the username already exists
            flash('Username already exists. Please choose another one.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        conn.close()

        # Flash success message
        flash("Registered successfully. Please log in.")
        return redirect('/login')

    return render_template('register.html')

# Search route: show matching books
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    sort = request.args.get("sort", "")

    conn = get_db_connection()

    # Get all matching books (we’ll sort in Python later)
    books_raw = conn.execute("""
        SELECT id, title, author, genres, rating, reviews FROM books
        WHERE title LIKE ? OR author LIKE ? OR genres LIKE ?
    """, (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()

    # Convert to list of dicts
    books_list = []
    for book in books_raw:
        book_dict = dict(book)
        book_dict['genres'] = ', '.join(book_dict['genres'].split(','))
        # Ensure 'rating' and 'reviews' are numbers
        book_dict['rating'] = float(book_dict.get('rating', 0) or 0)
        book_dict['reviews'] = int(book_dict.get('reviews', 0) or 0)
        books_list.append(book_dict)

    # Sort
    if sort == "az":
        books_list.sort(key=lambda b: b["title"].lower())
    elif sort == "za":
        books_list.sort(key=lambda b: b["title"].lower(), reverse=True)
    elif sort == "popular":
        books_list.sort(key=lambda b: b.get("reviews", 0), reverse=True)
    elif sort == "rating":
        books_list.sort(key=lambda b: b.get("rating", 0), reverse=True)

    # Pagination
    total_count = len(books_list)
    total_pages = (total_count + per_page - 1) // per_page
    paginated_books = books_list[offset:offset + per_page]

    conn.close()

    return render_template(
        'search_results.html',
        books=paginated_books,
        query=query,
        page=page,
        total_pages=total_pages,
        sort=sort
    )

# Book detail page
@app.route('/book/<int:book_id>')
def book_details(book_id):
    with open('similarities.json') as f:
        similarity_data = json.load(f)

    conn = get_db_connection()
    book_row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if book_row is None:
        conn.close()
        return "Book not found", 404
    
    book = dict(book_row)
    clean_series = get_series_name(book.get('series'))
    
    if clean_series:
        series_books = conn.execute(
            "SELECT * FROM books WHERE series LIKE ? AND id != ? LIMIT 5",
            (clean_series + '%', book_id)  # Use LIKE to match series + #number variants
        ).fetchall()
    else:
        series_books = []

    # Prepare genre string for display and a set for similarity
    try:
        genres_list = ast.literal_eval(book['genres'])
        if isinstance(genres_list, list):
            book['genres'] = ', '.join(g.strip() for g in genres_list)
            book_genres = set(g.strip().lower() for g in genres_list if g.strip())
        else:
            raise ValueError
    except:
        # fallback if genres is not a list-like string
        book['genres'] = ', '.join(g.strip() for g in book['genres'].split(','))
        book_genres = set(g.strip().lower() for g in book['genres'].split(',') if g.strip())

    book_title = book['title'].strip().lower()
    book_author = book['author'].strip().lower()
    similar_ids = similarity_data.get(str(book_id), [])

    main_recommendations = []
    fallback_recommendations = []

    if similar_ids:
        placeholders = ','.join(['?'] * len(similar_ids))
        query = f"SELECT * FROM books WHERE id IN ({placeholders})"
        similar_books = conn.execute(query, similar_ids).fetchall()

        for b in similar_books:
            if b['id'] == book_id:
                continue

            # Get genres for this similar book
            try:
                b_genres_list = ast.literal_eval(b['genres'])
                if isinstance(b_genres_list, list):
                    b_genres = set(g.strip().lower() for g in b_genres_list if g.strip())
                else:
                    raise ValueError
            except:
                b_genres = set(g.strip().lower() for g in b['genres'].split(',') if g.strip())

            b_title = b['title'].strip().lower()
            b_author = b['author'].strip().lower()

            if b_title == book_title or b_author == book_author:
                continue

            similarity_score = jaccard_similarity(book_genres, b_genres)

            if similarity_score >= 0.3:
                main_recommendations.append((similarity_score, b))
            elif similarity_score >= 0.1:
                fallback_recommendations.append((similarity_score, b))

        main_recommendations.sort(reverse=True, key=lambda x: x[0])
        fallback_recommendations.sort(reverse=True, key=lambda x: x[0])

    current_status = None
    user_id = session.get('user_id')
    if user_id:
        result = conn.execute(
            "SELECT status FROM user_books WHERE user_id = ? AND book_id = ?",
            (user_id, book_id)
        ).fetchone()
        if result:
            current_status = result['status']

    conn.close()

    recommendations = [b for _, b in main_recommendations[:10]]
    fallback = []

    if len(recommendations) < 5:
        remaining = 10 - len(recommendations)
        fallback = [b for _, b in fallback_recommendations[:remaining]]

    return render_template(
        'book_details.html',
        book=book,
        recommendations=recommendations,
        fallback=fallback,
        current_status=current_status, series_books=series_books
    )

@app.route('/mark/<int:book_id>/<status>')
def mark_book(book_id, status):
    if 'user_id' not in session:
        flash('You need to log in to mark books.', 'danger')
        return redirect('/login')

    if status not in ['wishlist', 'reading', 'read']:
        return "Invalid status", 400

    user_id = session['user_id']
    conn = get_db_connection()

    # Check if the book is already marked with the same status
    exists = conn.execute('''
        SELECT 1 FROM user_books WHERE user_id = ? AND book_id = ? AND status = ?
    ''', (user_id, book_id, status)).fetchone()

    if exists:
        flash(f'This book is already marked as {status}.', 'info')
    else:
        conn.execute("INSERT OR REPLACE INTO user_books (user_id, book_id, status) VALUES (?, ?, ?)",
                     (user_id, book_id, status))
        conn.commit()
        flash(f'Book marked as {status}.', 'success')

    conn.close()
    return redirect(f'/book/{book_id}')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must be logged in to view your profile.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()

    def fetch_books_by_status(status):
        return conn.execute(
            '''SELECT books.* FROM books
               JOIN user_books ON books.id = user_books.book_id
               WHERE user_books.user_id = ? AND user_books.status = ?''',
            (user_id, status)
        ).fetchall()

    wishlist = fetch_books_by_status('wishlist')
    reading = fetch_books_by_status('reading')
    read = fetch_books_by_status('read')

    conn.close()

    return render_template('profile.html', wishlist=wishlist, reading=reading, read=read)

@app.route("/genre/<genre_name>")
def view_genre(genre_name):
    conn = get_db_connection()

    page = request.args.get("page", 1, type=int)
    per_page = 12
    offset = (page - 1) * per_page

    books = conn.execute(
        "SELECT * FROM books WHERE genres LIKE ? LIMIT ? OFFSET ?", (f"%{genre_name}%", per_page, offset)
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM books WHERE genres LIKE ?", 
        (f"%{genre_name}%",)
    ).fetchone()[0]

    total_pages = (total + per_page - 1) // per_page

    conn.close()
    return render_template("genre.html", books=books, genre_name=genre_name, page=page, total_pages=total_pages)

@app.route('/remove_book/<int:book_id>/<status>')
def remove_book(book_id, status):
    if 'user_id' not in session:
        flash('Please log in to continue.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM user_books WHERE user_id = ? AND book_id = ? AND status = ?',
        (user_id, book_id, status)
    )
    conn.commit()
    conn.close()

    flash(f'Book removed from {status} list.', 'success')
    return redirect('/profile')

@app.route('/series/<series_name>')
def series_books(series_name):
    conn = get_db_connection()
    books = conn.execute(
        "SELECT * FROM books WHERE series LIKE ? COLLATE NOCASE",
        (f"{series_name}%",)
    ).fetchall()
    conn.close()

    # Convert to mutable dicts
    books = [dict(book) for book in books]
    numbered_books = []
    grouped_books =  []

    for book in books:
        series_value = book.get('series', '')
        if '-' in series_value:
            grouped_books.append(book)
        else:
            match = re.search(r'#(\d+)', series_value)
            if match:
                book['series_number'] = int(match.group(1))
                numbered_books.append(book)

    # Sort numbered books by series number
    numbered_books.sort(key=lambda b: b['series_number'])

    return render_template('series_books.html', series_name=series_name, numbered_books=numbered_books,
        grouped_books=grouped_books
    )


if __name__ == '__main__':
    app.run(debug=True)
