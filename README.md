# softly, mia ♡

A small bilingual lifestyle blog for a fictional girl called Mia. It is built
with Python, Flask, Jinja2, SQLite and plain HTML/CSS/JavaScript — no build
step, no npm, no accounts and no paid services.

The site is fully available in **English** and **Russian**, with the same
English content at `/en/` and Russian at `/ru/`.

---

## What is inside

| Page | English URL | Russian URL |
| --- | --- | --- |
| Home | `/en/` | `/ru/` |
| Journal | `/en/journal` | `/ru/journal` |
| Journal category | `/en/journal?category=beauty` | `/ru/journal?category=beauty` |
| Article | `/en/journal/<slug>` | `/ru/journal/<slug>` |
| Wishlist | `/en/wishlist` | `/ru/wishlist` |
| Dear Mia | `/en/dear-mia` | `/ru/dear-mia` |

Features:

- Six complete posts in both languages across four categories: Beauty,
  Wellness, Little Things and Wishlist.
- Category filtering, related posts and estimated reading time.
- Like buttons that save a shared total in SQLite and remember *your* like
  in `localStorage`, so it survives refreshes and works on both language
  versions of the same post.
- A six-item wishlist board with original illustrations.
- A working “Dear Mia” form with server-side validation, a character counter,
  a thank-you state and notes stored in SQLite.
- Language choice remembered in `localStorage`, with a cookie fallback. The
  root URL sends returning visitors to their last language and new visitors
  to English (or a tiny chooser if JavaScript is unavailable).
- Responsive layout, mobile menu, accessible focus states, reduced-motion
  support, local SVG artwork and Google Fonts with system fallbacks.
- No real personal data is required or displayed. All stories, wishes and
  names are fictional.

---

## Run it locally

You need **Python 3.10 or newer** and pip.

### Windows (PowerShell)

```powershell
cd softly-mia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
cd softly-mia
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000/** in your browser. The root page will take you
to `/en/` or `/ru/` depending on your saved language.

To stop the development server, press `Ctrl+C`.

### Another way to start it

```bash
flask --app app run --debug
```

The app creates `softly_mia.db` automatically the first time it starts and
seeds the six posts. Starting it again does **not** create duplicates and
does **not** reset likes.

---

## Project structure

```text
softly-mia/
├── app.py                 # Flask routes, SQLite schema and seed logic
├── content.py             # All six posts and six wishes, in EN + RU
├── i18n.py                # Every interface string, in EN + RU
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   ├── css/style.css      # The whole design and responsive layout
│   ├── js/main.js         # Menu, language memory, likes, form behaviour
│   └── images/            # Original local SVG illustrations
└── templates/
    ├── base.html          # Header, navigation, footer, language switch
    ├── index.html         # Home page
    ├── journal.html       # Journal + category filters
    ├── post.html          # Single article
    ├── wishlist.html      # Wish board
    ├── dear_mia.html      # Note form and success state
    ├── 404.html
    ├── redirect.html      # Root language chooser
    └── partials/
        ├── post_card.html
        └── like_button.html
```

### Where to change things

- **Text of a post or wish:** `content.py`. Each item has `en` and `ru`
  versions. Post paragraphs are separated by a blank line.
- **Navigation, buttons, labels, error messages:** `i18n.py`.
- **Colours, fonts, spacing:** the custom properties at the top of
  `static/css/style.css`.
- **Images:** replace any file in `static/images/` and keep its name, or
  update the image path in `content.py`.

---

## How the data works

SQLite database: `softly_mia.db` (created next to `app.py`).

Two tables are used:

- `posts` — the six published posts, their English and Russian versions, and
  the shared like count.
- `notes` — messages submitted through the Dear Mia form (`name`, `message`,
  `lang`, `created_at`).

The database file is excluded from Git by `.gitignore`. To start over from a
clean demo, stop the server, delete `softly_mia.db`, and run `python app.py`
again. The posts will be seeded fresh.

The like endpoint is:

```text
POST /<lang>/api/posts/<slug>/like
Content-Type: application/json

{"action": "like"}    # or {"action": "unlike"}
```

It returns `{"slug": "...", "likes": 149, "liked": true}`. The count is
clamped at zero, so repeated removals cannot make a negative total.

The Dear Mia form posts normally (no JavaScript required), validates on the
server, inserts the note, then redirects back to a thank-you state with
`?sent=1#note` so refreshing does not send the message twice.

---

## Accessibility and responsiveness

- Every page has a “skip to content” link and a visible keyboard focus style.
- The mobile menu uses `aria-expanded` and closes with `Escape`.
- Like buttons expose `aria-pressed` and update their label.
- Form fields have real labels, a required message field and an error summary.
- Animations fade in with `IntersectionObserver` and switch off when
  `prefers-reduced-motion` is set.
- The layout has breakpoints at 1060 px, 860 px and 560 px and was checked at
  desktop, tablet and phone widths.
- All artwork is local SVG, so there are no broken image links and the site
  works offline apart from the optional Google Fonts request. The CSS font
  stacks fall back to Georgia, Segoe UI and a system sans-serif.

---

## Good to know

- This is a **fictional demo**. “Mia”, the stories and the wishes are invented.
  The form asks for a first name at most and warns visitors not to send real
  personal details.
- There is no authentication, no admin panel, no payments and no external
  APIs. Notes are stored only in your local SQLite file.
- There is deliberately no CSRF token because the project is a single-user
  local demo. If you deploy it publicly, add CSRF protection, a real secret
  key from an environment variable, rate limiting and HTTPS first.
- The fonts are loaded from Google Fonts when online. Offline, the site still
  looks complete thanks to the fallback font stacks.

---

## Быстрый старт по-русски

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Откройте `http://127.0.0.1:5000/` — сайт сам предложит английскую или русскую
версию. Переключить язык можно в шапке сайта; выбор запоминается. Все записи и
пожелания вымышлены, а сообщения из формы «Напиши Мие» сохраняются только в
локальной базе `softly_mia.db`.

---

Made slowly, with a soft playlist. ♡
