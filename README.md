# AI-Based Unified Identity Documentation & Social Welfare Assistance Platform

A Flask + SQLite web application that lets a citizen keep their identity
documents in one secure vault, extract key details from them with OCR,
discover the government welfare schemes they qualify for through a
**transparent rules engine**, check eligibility, and track applications —
all explained in plain language.

Built as a college **Software Engineering** project. All data shipped with
the app is **fictional** and for demonstration only.

---

## 1. Features

- **Accounts & profiles** — register, log in (email *or* username, remember-me),
  change password. Passwords are stored hashed (Werkzeug PBKDF2).
- **Document Vault** — upload PDF/PNG/JPG (max 5 MB), with the file type
  verified by its **content signature**, not just the extension. Files are
  stored under random, unguessable names. Search, filter, replace, delete.
- **Smart Scanner (OCR)** — Tesseract reads a document; the app extracts
  name, date of birth, address and ID number. **Aadhaar/PAN/Voter numbers are
  masked** before anything is shown or stored, and **nothing is saved until
  you confirm** it on the review screen.
- **Scheme Explorer** — browse schemes by category with search.
- **Recommendations** — every active scheme is scored against your profile by
  a readable rules engine; each result shows **why**.
- **Eligibility Checker** — test any scheme with editable values, save the
  history, and print a result sheet.
- **Application Tracker** — track status, keep a document checklist
  (auto-seeded from the scheme's required documents), set reminders, print a
  summary.
- **Admin area** — dashboard with statistics, user management (enable/disable,
  role), scheme CRUD, per-scheme eligibility rules, categories, broadcast
  notifications, and a full activity/audit log.
- **Security** — CSRF protection on every form, per-user ownership checks,
  path-traversal-safe file serving, security headers (CSP, X-Frame-Options,
  nosniff), and friendly 403/404/413/500 error pages.

---

## 2. Requirements

- **Python 3.11+** (developed and tested on 3.14)
- **Tesseract OCR** — only needed to actually scan documents. The rest of the
  app runs without it.
  - Windows: install from <https://github.com/UB-Mannheim/tesseract/wiki>
    and either add it to `PATH` or set `TESSERACT_CMD` (see below).

---

## 3. Installation (Windows PowerShell)

```powershell
# 1. Go to the project folder
cd AI_Welfare_Platform

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) point to Tesseract if it is not on PATH
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"

# 5. Seed the database with demo data
python seed.py

# 6. Run the app
python app.py
```

On macOS / Linux the only differences are `source venv/bin/activate` and
`export TESSERACT_CMD=...`.

Then open **http://127.0.0.1:5000** in a browser.

> Set a real secret in production: `set SECRET_KEY=<something-random>`.

---

## 4. Demo credentials

| Role  | Login                 | Password   |
|-------|-----------------------|------------|
| Admin | `admin@welfare.local` | `Admin@123`|
| User  | `asha@example.com`    | `Demo@123` |
| User  | `ravi@example.com`    | `Demo@123` |
| User  | `meena@example.com`   | `Demo@123` |

---

## 5. Running the tests

```powershell
pip install -r requirements.txt
pytest -q
```

49 tests cover the rules engine, OCR text parsing & masking, authentication,
access control, the document vault, schemes, eligibility, applications, and
the admin area. See [docs/TEST_REPORT.md](docs/TEST_REPORT.md).

---

## 6. Project layout

```
AI_Welfare_Platform/
├── app.py                 # application factory, blueprints, error pages
├── config.py              # central settings & category lists
├── extensions.py          # db, login_manager, csrf instances
├── models.py              # 11 SQLAlchemy models
├── forms.py               # WTForms (CSRF-protected)
├── seed.py                # demo admin, users, schemes + rules
├── requirements.txt
├── routes/                # blueprints (auth, main, documents, scanner,
│                          #   schemes, recommendations, eligibility,
│                          #   applications, admin)
├── services/              # rules_engine, ocr_service, recommendation_service,
│                          #   common (file validation, auth, logging)
├── templates/             # Jinja2 templates (base + per-feature folders)
├── static/                # css/style.css, js/main.js, uploads/
├── tests/                 # pytest suite
├── docs/                  # documentation, test report, demo script, viva Q&A
└── instance/              # SQLite database (created at runtime)
```

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for architecture, the data
model, and the rules-engine design.

---

## 7. A note on the "AI"

The recommendation/eligibility engine is **rule-based and transparent** on
purpose: every decision is a set of readable conditions, and the app always
shows the reasons. This keeps the system explainable and verifiable — the
right choice for benefits decisions — rather than an opaque model.
