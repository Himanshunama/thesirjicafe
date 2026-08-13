"""
The SirJi House Cafe - Reviews Backend
---------------------------------------
A small Flask + SQLite API that powers the review form and the
"Happy Customers" section on the cafe website.

Endpoints
---------
GET  /api/reviews         -> list all reviews (newest first)
POST /api/reviews         -> add a new review  {name, rating, review}
GET  /api/reviews/stats   -> {average_rating, total_reviews}
GET  /                    -> serves index.html (put your site's HTML in templates/index.html)

Run it
------
    pip install flask
    python app.py

Then open http://127.0.0.1:5000
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, g, render_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "reviews.db"

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Open (or reuse) a SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the reviews table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    # Put your site's HTML file at templates/index.html to serve it here.
    return render_template("index.html")


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    db = get_db()
    rows = db.execute(
        "SELECT name, rating, review, created_at FROM reviews ORDER BY id DESC"
    ).fetchall()

    reviews = [
        {
            "name": row["name"],
            "rating": row["rating"],
            "review": row["review"],
            "date": row["created_at"],
        }
        for row in rows
    ]
    return jsonify(reviews)


@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    review_text = str(data.get("review", "")).strip()
    rating = data.get("rating")

    # --- validation -------------------------------------------------
    if not name or not review_text or rating is None:
        return jsonify({"error": "name, rating and review are all required."}), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be a number between 1 and 5."}), 400

    if rating < 1 or rating > 5:
        return jsonify({"error": "rating must be between 1 and 5."}), 400

    if len(name) > 80:
        return jsonify({"error": "name is too long (max 80 characters)."}), 400

    if len(review_text) > 500:
        return jsonify({"error": "review is too long (max 500 characters)."}), 400

    # --- save ---------------------------------------------------------
    db = get_db()
    db.execute(
        "INSERT INTO reviews (name, rating, review, created_at) VALUES (?, ?, ?, ?)",
        (name, rating, review_text, datetime.utcnow().isoformat()),
    )
    db.commit()

    return jsonify({"message": "Review added successfully."}), 201


@app.route("/api/reviews/stats", methods=["GET"])
def review_stats():
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS total, AVG(rating) AS avg_rating FROM reviews"
    ).fetchone()

    total = row["total"] or 0
    avg_rating = round(row["avg_rating"], 1) if row["avg_rating"] else 0

    return jsonify({"total_reviews": total, "average_rating": avg_rating})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=False)
