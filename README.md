# The SirJi House Cafe — Reviews Backend

A small Flask + SQLite API that powers the "Happy Customers" section and
review form on your site.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser — it serves your
website (`templates/index.html`) and the API from the same server, so
there are no CORS issues.

## Files

- `app.py` — the Flask app (all API logic)
- `templates/index.html` — your cafe website (already wired to the API)
- `reviews.db` — SQLite database, created automatically on first run

## API

| Method | Endpoint             | Description                          |
|--------|-----------------------|---------------------------------------|
| GET    | `/api/reviews`        | List all reviews, newest first        |
| POST   | `/api/reviews`        | Add a review `{name, rating, review}` |
| GET    | `/api/reviews/stats`  | `{average_rating, total_reviews}`     |

**POST /api/reviews body:**
```json
{
  "name": "Aarav",
  "rating": 5,
  "review": "Amazing chai and cozy vibe!"
}
```

Validation: `name` and `review` are required strings (max 80 / 500 chars),
`rating` must be an integer 1–5. Invalid input returns `400` with an
`error` message; success returns `201`.

## Going to production

For real deployment, run it with a production server instead of the Flask
dev server, e.g.:

```bash
pip install gunicorn
gunicorn app:app
```

You'll also want to put this behind HTTPS (e.g. via Nginx or a platform
like Render/Railway/PythonAnywhere) and consider adding basic rate
limiting or a moderation step before reviews go public.
