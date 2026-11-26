# Viva Questions & Answers

Likely examiner questions with concise, honest answers.

### 1. What problem does this project solve?
Citizens struggle to know which welfare schemes they qualify for and to keep
their identity documents organised. The platform unifies document storage,
automatic detail extraction, transparent eligibility matching, and application
tracking in one place.

### 2. Why Flask and SQLite?
Flask is a lightweight, well-documented micro-framework ideal for a focused
app and for learning the request/response cycle. SQLite needs no separate
server — perfect for a college project — and the code uses SQLAlchemy, so
moving to PostgreSQL later is just a config change (`DATABASE_URL`).

### 3. Is this "AI"? Where is the intelligence?
The matching engine is **rule-based and transparent** by design. For benefits
decisions, explainability matters more than a black-box model: every result
lists the exact conditions that passed or failed. The OCR (Tesseract) is the
machine-perception part. This is a deliberate, defensible engineering choice.

### 4. How does the eligibility engine work?
Each scheme has rules `(field, operator, value)`. A profile is checked rule by
rule; each rule is pass, fail, or missing. Any fail → Not Eligible; a missing
value → Need More Info; all pass → Eligible; otherwise Likely Eligible. The
score is the percentage of rules passed. The logic is a pure function with no
Flask/DB dependency, so it is unit-tested directly.

### 5. How do you keep user data private in the OCR flow?
Extracted values are shown on a review page and kept only in the session;
nothing is written until the user confirms. ID numbers (Aadhaar, PAN, Voter)
are **masked** by regex before display or storage (e.g. `XXXX XXXX 9012`).

### 6. How do you validate uploaded files?
Three layers: the form allows only `.pdf/.png/.jpg/.jpeg`; the 5 MB
`MAX_CONTENT_LENGTH` limit; and a **content-signature check** that reads the
file's magic bytes so a text file renamed to `.png` is rejected. Files are
saved under random UUID names, and serving them uses a path-traversal-safe
resolver.

### 7. How is authentication handled?
Flask-Login manages sessions. Passwords are hashed with Werkzeug's PBKDF2
(never stored in plain text). Login accepts email or username, supports
remember-me, and logout is POST-only (so it can't be triggered by a GET/CSRF).

### 8. What stops one user seeing another's data?
Every record-level route calls `owned_or_404`, which 404s unless the row's
`user_id` matches the current user (admins excepted). Admin routes are guarded
by a blueprint `before_request` that checks the role.

### 9. How is CSRF handled?
Flask-WTF's `CSRFProtect` is enabled globally; every form renders a hidden
token (`form.hidden_tag()` or an explicit `csrf_token()` field for plain POST
forms like logout, delete, status change).

### 10. What are the main tables and relationships?
11 tables: users, documents, schemes, eligibility_rules, recommendations,
eligibility_checks, applications, application_checklist, notifications,
activity_logs, categories. A user owns documents/recommendations/checks/
applications/notifications (cascade delete); a scheme owns its rules; an
application owns its checklist items.

### 11. How did you test it, and did you find bugs?
49 pytest tests cover logic and every route area, using an in-memory DB.
Testing found a real OCR bug: the Aadhaar regex matched across a newline and
mis-read a date-of-birth year as part of the ID. It was fixed by restricting
the group separator to a literal space. (See TEST_REPORT.md.)

### 12. What are the limitations / future work?
- OCR accuracy depends on scan quality; only the first PDF page is read.
- Rules are simple single-field conditions (no AND/OR groups across fields yet).
- No email/SMS reminders — reminders are shown in-app only.
- Future: real identity-provider verification, document expiry alerts,
  multi-language UI, and richer rule composition.

### 13. How would you deploy this?
Run behind a production WSGI server (gunicorn/waitress) instead of the dev
server, set a strong `SECRET_KEY` and `DATABASE_URL` from the environment,
serve static files via the web server, and enable HTTPS so the secure cookies
take effect.

### 14. Why a service layer?
To separate business logic from HTTP handling. Routes stay thin; the rules
engine and OCR parsing are pure and testable; swapping the UI or adding an API
later would not touch the core logic.
