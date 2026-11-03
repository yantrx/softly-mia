"""softly, mia ♡ — a small bilingual Flask blog.

Run the site with:

    python app.py

The SQLite database is created automatically on the first run. Posts are
seeded once; running the app again will not create duplicates or reset likes.
"""

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    abort,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from content import POSTS, WISHLIST
from i18n import CATEGORY_ORDER, DEFAULT_LANG, LANGUAGES, UI

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "softly_mia.db"

app = Flask(__name__)
app.config["DATABASE"] = str(DATABASE_PATH)
app.config["SECRET_KEY"] = "local-demo-only-not-a-real-secret"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    published_at TEXT NOT NULL,
    cover TEXT NOT NULL,
    title_en TEXT NOT NULL,
    title_ru TEXT NOT NULL,
    excerpt_en TEXT NOT NULL,
    excerpt_ru TEXT NOT NULL,
    quote_en TEXT NOT NULL,
    quote_ru TEXT NOT NULL,
    body_en TEXT NOT NULL,
    body_ru TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    message TEXT NOT NULL,
    lang TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_category ON posts (category);
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts (published_at);
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables and add the demo posts if they are missing."""
    db = get_db()
    db.executescript(SCHEMA)

    for post in POSTS:
        db.execute(
            """
            INSERT OR IGNORE INTO posts (
                slug, category, published_at, cover,
                title_en, title_ru, excerpt_en, excerpt_ru,
                quote_en, quote_ru, body_en, body_ru, likes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post["slug"],
                post["category"],
                post["published_at"],
                post["cover"],
                post["title"]["en"],
                post["title"]["ru"],
                post["excerpt"]["en"],
                post["excerpt"]["ru"],
                post["quote"]["en"],
                post["quote"]["ru"],
                post["body"]["en"],
                post["body"]["ru"],
                post["likes"],
            ),
        )

    db.commit()


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def require_lang(lang):
    """Reject URLs that try to use a language the site does not support."""
    if lang not in LANGUAGES:
        abort(404)
    return lang


def plural_ru(number, forms):
    """Pick the right Russian word form for 1 / 2–4 / 5+."""
    number = abs(number)
    last_two = number % 100
    last_one = number % 10
    if last_one == 1 and last_two != 11:
        return forms[0]
    if 2 <= last_one <= 4 and not 12 <= last_two <= 14:
        return forms[1]
    return forms[2]


def format_date(value, lang):
    """Turn '2026-10-29' into a friendly, localised date."""
    try:
        date = datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return value

    if lang == "ru":
        return f"{date.day} {UI['ru']['months'][date.month - 1]} {date.year}"
    return f"{UI['en']['months'][date.month - 1]} {date.day}, {date.year}"


def localize_post(row, lang):
    """Convert a database row into a post ready for the templates."""
    body = row[f"body_{lang}"]
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    word_count = len(re.findall(r"\w+", body, flags=re.UNICODE))

    return {
        "id": row["id"],
        "slug": row["slug"],
        "category": row["category"],
        "published_at": row["published_at"],
        "date": format_date(row["published_at"], lang),
        "cover": row["cover"],
        "title": row[f"title_{lang}"],
        "excerpt": row[f"excerpt_{lang}"],
        "quote": row[f"quote_{lang}"],
        "paragraphs": paragraphs,
        "likes": row["likes"],
        "reading_time": max(1, round(word_count / 200)),
    }


def fetch_posts(lang, category=None):
    db = get_db()
    if category:
        rows = db.execute(
            "SELECT * FROM posts WHERE category = ? ORDER BY published_at DESC, id DESC",
            (category,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM posts ORDER BY published_at DESC, id DESC"
        ).fetchall()
    return [localize_post(row, lang) for row in rows]


def build_filters(lang, selected):
    t = UI[lang]
    filters = [
        {
            "key": None,
            "label": t["journal"]["all"],
            "url": url_for("journal", lang=lang),
            "active": selected is None,
        }
    ]
    for key in CATEGORY_ORDER:
        filters.append(
            {
                "key": key,
                "label": t["categories"][key],
                "url": url_for("journal", lang=lang, category=key),
                "active": selected == key,
            }
        )
    return filters


# ---------------------------------------------------------------------------
# Template context
# ---------------------------------------------------------------------------

@app.context_processor
def inject_shared_context():
    view_lang = (request.view_args or {}).get("lang")
    if view_lang in LANGUAGES:
        lang = view_lang
    else:
        first_segment = request.path.strip("/").split("/")[0]
        lang = first_segment if first_segment in LANGUAGES else DEFAULT_LANG

    t = UI[lang]

    def localized_url(target_lang):
        """Build the same page in the other language."""
        endpoint = request.endpoint
        if endpoint in (None, "root"):
            return url_for("index", lang=target_lang)

        args = dict(request.view_args or {})
        args["lang"] = target_lang
        query = request.args.to_dict(flat=True)
        query.pop("lang", None)

        try:
            return url_for(endpoint, **args, **query)
        except Exception:
            return url_for("index", lang=target_lang)

    def count_notes(number):
        if lang == "ru":
            word = plural_ru(number, ("заметка", "заметки", "заметок"))
        else:
            word = "note" if number == 1 else "notes"
        return f"{number} {word}"

    other_lang = "ru" if lang == "en" else "en"
    return {
        "lang": lang,
        "t": t,
        "other_lang": other_lang,
        "alt_url": localized_url(other_lang),
        "lang_urls": {code: localized_url(code) for code in LANGUAGES},
        "count_notes": count_notes,
        "current_year": datetime.now().year,
        "category_order": CATEGORY_ORDER,
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Send visitors to their saved language, or English on a first visit.

    A tiny cookie is set by main.js after a language page loads. When it is
    missing (a brand-new visitor), redirect.html checks localStorage instead.
    """
    saved = request.cookies.get("mia_lang")
    if saved in LANGUAGES:
        return redirect(url_for("index", lang=saved))
    return render_template("redirect.html")


@app.get("/<lang>/")
def index(lang):
    lang = require_lang(lang)
    t = UI[lang]
    posts = fetch_posts(lang)
    db = get_db()
    counts = dict(
        db.execute("SELECT category, COUNT(*) FROM posts GROUP BY category").fetchall()
    )

    topics = []
    for key in CATEGORY_ORDER:
        topics.append(
            {
                "key": key,
                "label": t["categories"][key],
                "description": t["home"]["topics"][key],
                "url": url_for("journal", lang=lang, category=key),
                "count": counts.get(key, 0),
            }
        )

    return render_template(
        "index.html",
        latest_posts=posts[:3],
        topics=topics,
        total_posts=len(posts),
    )


@app.get("/<lang>/journal")
def journal(lang):
    lang = require_lang(lang)
    selected = request.args.get("category")
    if selected and selected not in CATEGORY_ORDER:
        abort(404)

    posts = fetch_posts(lang, selected)
    return render_template(
        "journal.html",
        posts=posts,
        filters=build_filters(lang, selected),
        selected_category=selected,
    )


@app.get("/<lang>/journal/<slug>")
def post(lang, slug):
    lang = require_lang(lang)
    db = get_db()
    row = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        abort(404)

    item = localize_post(row, lang)
    related_rows = db.execute(
        """
        SELECT * FROM posts
        WHERE slug != ?
        ORDER BY CASE WHEN category = ? THEN 0 ELSE 1 END,
                 published_at DESC
        LIMIT 3
        """,
        (slug, row["category"]),
    ).fetchall()
    related = [localize_post(related_row, lang) for related_row in related_rows]

    return render_template("post.html", post=item, related=related)


@app.get("/<lang>/wishlist")
def wishlist(lang):
    lang = require_lang(lang)
    items = []
    for number, item in enumerate(WISHLIST, start=1):
        items.append(
            {
                "id": item["id"],
                "image": item["image"],
                "title": item["title"][lang],
                "note": item["note"][lang],
                "number": f"{number:02d}",
            }
        )
    return render_template("wishlist.html", items=items)


@app.route("/<lang>/dear-mia", methods=["GET", "POST"])
def dear_mia(lang):
    lang = require_lang(lang)
    t = UI[lang]
    form = {"name": "", "message": ""}
    errors = []
    sent = request.args.get("sent") == "1"

    if request.method == "POST":
        form["name"] = (request.form.get("name") or "").strip()
        form["message"] = (request.form.get("message") or "").strip()

        if not form["message"]:
            errors.append(t["dear"]["error_empty"])
        elif len(form["message"]) > 1000:
            errors.append(t["dear"]["error_long"])

        if len(form["name"]) > 60:
            errors.append(t["dear"]["error_name_long"])

        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO notes (name, message, lang, created_at) VALUES (?, ?, ?, ?)",
                (
                    form["name"] or None,
                    form["message"],
                    lang,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            db.commit()
            return redirect(url_for("dear_mia", lang=lang, sent=1) + "#note")

    if request.method == "GET":
        sent = request.args.get("sent") == "1"

    status = 400 if errors else 200
    return (
        render_template(
            "dear_mia.html",
            form=form,
            errors=errors,
            sent=sent,
        ),
        status,
    )


# ---------------------------------------------------------------------------
# Like API
# ---------------------------------------------------------------------------

@app.post("/<lang>/api/posts/<slug>/like")
def toggle_like(lang, slug):
    """Increment or decrement a post's aggregate like count.

    The browser stores whether *this* browser liked a post in localStorage.
    The database stores the shared total for both language versions.
    """
    lang = require_lang(lang)
    data = request.get_json(silent=True) or request.form
    action = data.get("action")

    if action not in ("like", "unlike"):
        return jsonify({"error": "invalid_action"}), 400

    db = get_db()
    delta = 1 if action == "like" else -1
    cursor = db.execute(
        "UPDATE posts SET likes = MAX(0, likes + ?) WHERE slug = ?",
        (delta, slug),
    )
    if cursor.rowcount == 0:
        return jsonify({"error": "post_not_found"}), 404

    db.commit()
    row = db.execute("SELECT likes FROM posts WHERE slug = ?", (slug,)).fetchone()
    return jsonify(
        {
            "slug": slug,
            "likes": row["likes"],
            "liked": action == "like",
        }
    )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# Initialise the database when the module is imported (works with
# `python app.py` and with `flask --app app run`).
with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
