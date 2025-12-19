# Conker Tweaks
A Python-powered web app for product management and orders with user auth and a clean UI.

> **Licensing note:** The **code** is MIT-licensed. All **design & visual assets** (HTML layouts, CSS, images, logos, screenshots, and other UI/UX artwork) are licensed under **CC BY 4.0** — reuse is allowed **with attribution**. See [LICENSE](./LICENSE) and [LICENSE-DESIGN.md](./LICENSE-DESIGN.md).

---

## ✨ Features
- User authentication (login/register), profiles, and sessions
- Products & orders modules
- API routes and view layer
- Form validation & (optional) reCAPTCHA
- SQLite database by default (`conker.db`), easy to switch to Postgres/MySQL
- Static assets for styling under `static/`

---

## 🧱 Tech Stack
- **Python 3.10+**
- **Web framework:** defined in `requirements.txt` (the project is structured to run with a standard WSGI/ASGI app in `main.py`/`start.py`)
- **Database:** SQLite (dev) via `conker.db`
- **Environment:** `.env` for secrets/config
- **Deps:** see `requirements.txt`

---

## 📁 Project Structure
```text
.
├── api/                # API route modules
├── auth/               # authentication utilities/routes
├── models/             # ORM/data models
├── orders/             # orders module
├── products/           # products module
├── schemas/            # request/response schemas & validation
├── static/             # CSS, images, JS (design assets)
├── utils/              # helpers (e.g., recaptcha)
├── view/               # server-rendered views/templates
├── .env                # environment variables (not committed in prod)
├── conker.db           # SQLite database (dev)
├── database.py         # DB connection/setup
├── init_db.py          # create/seed database
├── main.py             # app entry (WSGI/ASGI)
├── requirements.txt    # dependencies
└── start.py            # convenience runner
```

---

## 🚀 Getting Started (Local)

### 1) Clone & setup
```bash
git clone https://github.com/PeterTech-Dev/Conker-Tweaks.git
cd Conker-Tweaks

# create & activate a virtual env (Windows PowerShell shown; adjust for macOS/Linux)
python -m venv .venv
. .venv/Scripts/Activate.ps1   # Windows
# source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

### 2) Environment variables
Copy or create a `.env` file (example values):
```bash
APP_ENV=development
SECRET_KEY=change-this
DATABASE_URL=sqlite:///conker.db
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
```
> If you keep using SQLite, `DATABASE_URL` can be `sqlite:///conker.db` (relative) or `sqlite:////absolute/path/to/conker.db`.

### 3) Initialize the database
```bash
python init_db.py
# or, if migrations/seeders are included, run them here
```

### 4) Run the app
Try one of the following depending on your entry point:

```bash
# Typical runner
python start.py

# Or directly (if main.py exposes app)
python main.py

# If ASGI app is named `app` inside main.py:
# uvicorn main:app --reload --port 8000
```
Open: <http://127.0.0.1:8000> (or the port printed by your runner).

---

## 🧪 Testing (optional)
Add tests (pytest) and document how to run them here:
```bash
pytest -q
```

---

## ⚙️ Configuration Notes
- Set proper secrets in `.env` for production.
- Replace SQLite with a hosted DB by changing `DATABASE_URL` and updating your DB client/ORM.
- If you use reCAPTCHA, ensure keys are set and network access is allowed.
- Static files are served from `static/`; see **License** below for attribution requirements.

---

## 🧾 License & Attribution (dual-license)
- **Code:** [MIT](./LICENSE) © 2025 PeterTech‑Dev — free to use/modify with the MIT notice retained.
- **Design & Visual Assets (UI/UX):** [CC BY 4.0](./LICENSE-DESIGN.md) — **attribution required** for any public use, including forks and commercial use.
  - **What counts as “design assets”?** HTML layout structure, CSS stylesheets, themes, color systems, images, icons, logos, mockups, and screenshots in this repo.
  - **Preferred attribution:**  
    *“Design by PeterTech‑Dev – https://github.com/PeterTech-Dev”*  
    Include this in your project README, site footer, or credits page.
  - If you prefer stricter terms (e.g., non‑commercial use), swap to **CC BY‑NC 4.0** and update this section.

See [ATTRIBUTION.md](./ATTRIBUTION.md) for a drop‑in credit snippet.

---

## 🤝 Contributing
Pull requests are welcome. By contributing, you agree your code contributions will be licensed under MIT; design contributions under CC BY 4.0 unless otherwise stated.

---

## 📬 Contact
Questions or license exceptions? Open an issue or reach out via GitHub.
