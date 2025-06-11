# BOOKVERSE - Book Recommendation System
#### Video Demo: https://youtu.be/-_Hfr5PkJjI
#### Live Demo: https://bookverse-jbew.onrender.com
#### Description: 
This project is a **Book Recommendation System** web application designed to help users discover books similar to those they enjoy, based on a sophisticated hybrid recommendation algorithm and a user-friendly interface. The system leverages a rich dataset of over 50,000 books, extracting metadata from CSV files, storing it in an SQLite database, and providing dynamic recommendations based on genres, descriptions, and author information.

---

### Project Overview

The goal of this project was to build a robust book recommendation engine alongside a full-stack web application that allows users to explore, search, and personalize their reading journey. The system focuses on accuracy and diversity in recommendations by combining multiple similarity metrics in a hybrid model, while also emphasizing usability through features like user authentication, customizable UI modes, and genre-based browsing.

---

### Data Preparation and Database Creation

The initial dataset was provided as a large CSV file from Kaggle, containing over 50,000 book records with columns including `id`, `title`, `author`, `description`, `genres`, and other metadata. 



- **Data Extraction**: I wrote Python scripts to parse this CSV file, clean the data by removing entries with missing or empty descriptions, and normalize genre tags by stripping whitespace and converting to lowercase.
- **Database Setup**: The cleaned data was then imported into an SQLite database (`books.db`). This database serves as the core data source for the web application, allowing efficient querying for books, user interactions, and recommendations.

---

### The Hybrid Similarity Model

At the core of the project is a **hybrid content-based recommendation algorithm** that computes similarity between books based on three key factors:

#### 1. Genre Similarity (Primary Factor)

- Each book’s genres are treated as a set of categories (e.g., “fantasy”, “adventure”, “mystery”).
- The **Jaccard similarity index** measures the overlap of genre sets between two books:
  \
  Jaccard(A, B) = |A ∩ B| / |A ∪ B|
  
- Genre similarity is given the highest weight (50%) because it captures the broad thematic and categorical relationship between books, which strongly influences reader preference.

#### 2. Description Similarity (Secondary Factor)

- Book descriptions are vectorized using **TF-IDF (Term Frequency-Inverse Document Frequency)**. Text is converted into numeric vectors that capture important words and common stopwords are down-weighted.
- **Cosine similarity** between these TF-IDF vectors measures semantic similarity and tells how alike two books’ descriptions are.
- Description similarity is weighted at 40%. Nuance is added by capturing style, themes, and narrative elements beyond simple genre labels.

#### 3. Author Penalty (Tertiary Factor)

- Books by the **same author** are penalized by subtracting a small score (0.1) to reduce over-recommendation of the same author’s works unless their similarity score is very high.
- This ensures diversity in the recommendation and users discover books from different authors as well as strong matches within an author’s series or related works.

---

### Similarity Computation and Optimization

- For each book, the algorithm computes hybrid similarity scores against all other books, ranks them, and selects the top 30 recommendations.
- Same-author books with moderate similarity (score < 0.8) are filtered out to avoid repetition.
- To handle the large dataset efficiently, **parallel processing** with `joblib` accelerates similarity calculations, running them concurrently across multiple CPU cores.
- Partial results are periodically saved to JSON files for fault tolerance and recovery.
- The final similarity mapping is stored in `similarities.json`, allowing fast lookup during user interaction.

---

### Web Application Features

The front-end and back-end were built with **Flask** and **SQLite**, incorporating multiple user-focused features:

#### User Authentication

- Users can **register** new accounts, with passwords securely hashed using industry-standard hashing libraries before storage.
- Users can **log in** and **log out**, with session management ensuring personalized experiences.
- Authentication guards user-specific actions like adding books to wishlists or marking reading status.

#### Book Exploration & Browsing

- Users can explore books by **genre** via a **bootstrap carousel**. This visual horizontal scroll allows browsing books in categories such as fantasy, science fiction, romance, and more.
- Each carousel dynamically loads relevant book titles and authors fetched from the database.
- Users can sort books by popularity, rating, or alphabetical order (A-Z / Z-A) using the "Sort By" filter available.

#### Recommendations & Bookmarks

- On each book’s detail page, users receive a list of recommended similar books computed by the hybrid similarity algorithm.
- Users can **add books to their wishlists**, mark them as **currently reading**, or **completed**.
- The system prevents duplicate bookmarks and manages the user’s personal reading lists efficiently.
- On the side, users can view **Other books in the series** and surf over to see all the books in the series with their respective series numbers. Individual volumes and book collections are shown separately.

---

### UI/UX Enhancements

- A **dark mode / light mode toggle** was implemented to improve accessibility and comfort for users reading at different times.
- The interface uses **Bootstrap** for responsive design, ensuring the site is functional and attractive on mobile devices and desktops.
- Real-time **search functionality** allows users to quickly find books by title.

---

### Code Structure and Files

- `app.py`: Main Flask application managing routes, user sessions, and API endpoints.
- `books.db`: Defines the database schema and contains three tables - users, books and user_books.
- `precompute_similarities.py`: Contains the similarity computation logic and helper functions for hybrid scoring.
- `templates/`: HTML templates for all pages, including home, login, register, book details, and user dashboard.
- `static/`: CSS stylesheet supporting the front-end.
- `import.py`: Data extraction codes for converting CSV to SQLite database.
- `similarities.json`: Precomputed similarity mappings used for fast recommendation lookups. Computed using Google Colab.

---

### Design Decisions & Challenges

- **Hybrid model choice:** Balancing genre and description similarity proved crucial to avoid recommendations that are either too generic (genre-only) or too narrow (text-only).
- **Author penalty:** This subtle tweak improved recommendation diversity without ignoring popular series.
- **Parallel processing:** A necessity to scale to 50,000+ books; naive pairwise comparisons would be prohibitively slow.
- **Security:** Hashing passwords and managing sessions properly were priorities for safe user authentication.
- **UI accessibility:** Dark/light mode and responsive design ensure a pleasant user experience across devices.

---

### Future Work

- Integrate **user ratings** and filtering for more personalized recommendations.
- Recommend books based on user's reading history.
- Add social features like user reviews, comments, and friend recommendations.
- Make an admin interface to add in more books and related metadata easily.

---

### Conclusion

This project combines data science, software engineering, and UI/UX design to deliver a polished book recommendation platform. Through careful dataset preparation, a well-thought-out hybrid recommendation engine, and user-centric features like authentication and dark mode, it provides a comprehensive tool for book lovers to discover and track their reading journeys.

---

Thank you for exploring this project! Any feedback or contributions are welcome.

---
