# Technical Documentation

AI-Based Unified Identity Documentation & Social Welfare Assistance Platform

---

## 1. System architecture

```
                 ┌──────────────────────────────────────────┐
   Browser  ───▶ │  Flask app (app.py – application factory) │
                 │                                            │
                 │   Blueprints (routes/)                     │
                 │   ├─ main        landing, dashboard        │
                 │   ├─ auth        register/login/profile    │
                 │   ├─ documents   vault                     │
                 │   ├─ scanner     OCR + review              │
                 │   ├─ schemes     explorer                  │
                 │   ├─ recommendations                       │
                 │   ├─ eligibility checker + history         │
                 │   ├─ applications tracker + checklist      │
                 │   └─ admin       management + audit        │
                 │                                            │
                 │   Services (services/)                     │
                 │   ├─ rules_engine         (pure logic)     │
                 │   ├─ ocr_service          (Tesseract+parse)│
                 │   ├─ recommendation_service                │
                 │   └─ common  (validation, auth, logging)   │
                 │                                            │
                 │   Extensions: SQLAlchemy, Login, CSRF      │
                 └───────────────────┬────────────────────────┘
                                     │
                            SQLite (instance/welfare.db)
                            Files   (static/uploads/)
```

Layering is deliberate: **routes** handle HTTP and templates, **services**
hold business logic, **models** hold persistence. The rules engine and OCR
text parsing are pure functions with no Flask/DB imports, so they are trivial
to unit-test.

## 2. Module responsibilities

| Layer | File | Responsibility |
|-------|------|----------------|
| Config | `config.py` | Secret key (env), DB URI, upload limits, category lists |
| Core | `extensions.py` | Single `db`, `login_manager`, `csrf` instances |
| Core | `app.py` | App factory, blueprint registration, security headers, error handlers, notification-badge context processor |
| Data | `models.py` | 11 ORM models + relationships + helpers |
| Input | `forms.py` | WTForms with validation + automatic CSRF |
| Logic | `services/rules_engine.py` | Rule evaluation, result categories, scoring, profile completion |
| Logic | `services/ocr_service.py` | Tesseract pipeline + pure field extraction & ID masking |
| Logic | `services/recommendation_service.py` | Evaluate all schemes, persist recommendations |
| Logic | `services/common.py` | MIME detection by signature, safe paths, ownership guard, admin guard, notifications, audit log |

## 3. Data model (11 tables)

| Table | Purpose | Key fields |
|-------|---------|-----------|
| `users` | Accounts + profile for eligibility | username, email, password_hash, role, account_active, age, gender, annual_income, social_category, occupation, state, is_student/farmer/differently_abled |
| `documents` | Vault entries | document_name, category, file_path, mime_type, status, extracted_name/dob/address/number, is_confirmed |
| `schemes` | Scheme catalogue | scheme_name, category, description, benefits, official_url, required_documents, is_active |
| `eligibility_rules` | Admin-editable rules per scheme | scheme_id, field, operator, value, description |
| `recommendations` | Stored per-user results | user_id, scheme_id, result, score, reasons |
| `eligibility_checks` | Saved manual checks | user_id, scheme_id, result, score, reasons, input_snapshot |
| `applications` | Tracker | user_id, scheme_id, status, reference_number, submitted_on, reminder_date, notes |
| `application_checklist` | Per-application to-dos | application_id, item, is_done |
| `notifications` | In-app messages | user_id, message, category, is_read |
| `activity_logs` | Audit trail | user_id, action, detail, ip_address |
| `categories` | Admin-managed categories | name, kind, icon |

### Relationships
- `User` 1─∞ `Document`, `Recommendation`, `EligibilityCheck`, `Application`,
  `Notification` (all cascade-delete with the user).
- `Scheme` 1─∞ `EligibilityRule` (cascade), and is referenced by
  recommendations / checks / applications.
- `Application` 1─∞ `ApplicationChecklist` (cascade).

## 4. The rules engine

A scheme's eligibility is a list of rules `(field, operator, value)`.
Operators: `<= >= < > == != in is_true is_false`.

For a profile, each rule returns **pass / fail / missing**:

- any **fail** → `Not Eligible`
- no fail but some **missing** → `Need More Info`
- all **pass** → `Eligible`
- mixed pass with none failing/missing → `Likely Eligible`
- no rules defined → `Likely Eligible` (verify on portal)

`score = passed / total * 100`. Every result carries a `reasons` list such as
`[OK] age (21) must be at most 30`, so the UI can always explain itself.

## 5. OCR flow and privacy

1. User uploads a file → stored with a random name; MIME verified by signature.
2. User runs the scanner → Tesseract OCR → raw text.
3. Pure functions extract name / DOB / address and a **masked** ID number
   (e.g. `XXXX XXXX 9012`). The full text is masked too.
4. The proposed values are held in the **session only** and shown on a review
   page. Nothing touches the database.
5. User edits/confirms → only then are the confirmed fields written, and the
   document is marked `Verified`.

This "confirm before store" design keeps the user in control of their data.

## 6. Security measures

- **CSRF** on every form via Flask-WTF `CSRFProtect`.
- **Password hashing** with Werkzeug (`generate_password_hash`).
- **Ownership checks** (`owned_or_404`) so users can only touch their own rows.
- **Admin guard** via a blueprint `before_request` + role check.
- **Upload safety**: content-signature MIME check, 5 MB limit, random stored
  names, `safe_upload_path` blocks `..` path traversal.
- **Security headers**: CSP, `X-Frame-Options: SAMEORIGIN`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy`.
- **Account disable**: admins can disable an account; disabled users cannot log
  in (enforced by `User.is_active`).
- **Audit log** of sensitive actions with IP.

## 7. Extending the app

- **Add a scheme**: Admin → Schemes → New, then add rules.
- **Add a rule field**: add a profile column to `User`, expose it in
  `User.profile_dict()`, `ProfileForm`/`EligibilityForm`, and `RuleForm`
  choices.
- **Swap the database**: set `DATABASE_URL` to e.g. a Postgres URI.
