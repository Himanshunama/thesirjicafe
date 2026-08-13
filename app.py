import sqlite3
import os
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, jsonify, request, g, render_template, Response

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "reviews.db"

app = Flask(__name__)

# ---------------------------------------------------------
# ADMIN PASSWORD
# ---------------------------------------------------------

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-password")


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    """Open or reuse SQLite connection for current request."""
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
    """Create reviews table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# ADMIN AUTHENTICATION
# ---------------------------------------------------------

def check_admin_auth():
    auth = request.authorization

    if not auth:
        return False

    return (
        auth.username == "admin"
        and auth.password == ADMIN_PASSWORD
    )


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not check_admin_auth():
            return Response(
                "Admin authentication required.",
                401,
                {
                    "WWW-Authenticate": 'Basic realm="SirJi Cafe Admin"'
                }
            )

        return function(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# GET ALL REVIEWS
# ---------------------------------------------------------

@app.route("/api/reviews", methods=["GET"])
def get_reviews():

    db = get_db()

    rows = db.execute("""
        SELECT id, name, rating, review, created_at
        FROM reviews
        ORDER BY id DESC
    """).fetchall()

    reviews = [
        {
            "id": row["id"],
            "name": row["name"],
            "rating": row["rating"],
            "review": row["review"],
            "date": row["created_at"]
        }
        for row in rows
    ]

    return jsonify(reviews)


# ---------------------------------------------------------
# ADD REVIEW
# ---------------------------------------------------------

@app.route("/api/reviews", methods=["POST"])
def add_review():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    review_text = str(data.get("review", "")).strip()
    rating = data.get("rating")

    # Validation
    if not name or not review_text or rating is None:
        return jsonify({
            "error": "name, rating and review are all required."
        }), 400

    try:
        rating = int(rating)

    except (TypeError, ValueError):
        return jsonify({
            "error": "rating must be a number between 1 and 5."
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "error": "rating must be between 1 and 5."
        }), 400

    if len(name) > 80:
        return jsonify({
            "error": "name is too long (max 80 characters)."
        }), 400

    if len(review_text) > 500:
        return jsonify({
            "error": "review is too long (max 500 characters)."
        }), 400

    # Save review
    db = get_db()

    db.execute("""
        INSERT INTO reviews
        (name, rating, review, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        rating,
        review_text,
        datetime.utcnow().isoformat()
    ))

    db.commit()

    return jsonify({
        "message": "Review added successfully."
    }), 201


# ---------------------------------------------------------
# REVIEW STATS
# ---------------------------------------------------------

@app.route("/api/reviews/stats", methods=["GET"])
def review_stats():

    db = get_db()

    row = db.execute("""
        SELECT
            COUNT(*) AS total,
            AVG(rating) AS avg_rating
        FROM reviews
    """).fetchone()

    total = row["total"] or 0

    avg_rating = (
        round(row["avg_rating"], 1)
        if row["avg_rating"]
        else 0
    )

    return jsonify({
        "total_reviews": total,
        "average_rating": avg_rating
    })


# ---------------------------------------------------------
# DELETE REVIEW
# ---------------------------------------------------------

@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@admin_required
def delete_review(review_id):

    db = get_db()

    cursor = db.execute(
        "DELETE FROM reviews WHERE id = ?",
        (review_id,)
    )

    db.commit()

    if cursor.rowcount == 0:
        return jsonify({
            "error": "Review not found."
        }), 404

    return jsonify({
        "message": "Review deleted successfully."
    })


# ---------------------------------------------------------
# ADMIN PAGE
# ---------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_page():
    return render_template("admin.html")


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------

init_db()

if __name__ == "__main__":
    app.run(debug=False)