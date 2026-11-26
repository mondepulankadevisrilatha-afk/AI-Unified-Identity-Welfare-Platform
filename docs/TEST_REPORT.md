# Test Report

AI-Based Unified Identity Documentation & Social Welfare Assistance Platform

**Date:** 24 November 2026
**Environment:** Windows 11, Python 3.14, Flask 3.1, pytest 8.3
**Command:** `pytest -q`
**Result:** **49 passed, 0 failed**

---

## 1. Automated test summary

| Test file | Tests | Area covered |
|-----------|------:|--------------|
| `test_rules_engine.py` | 10 | Rule operators, eligible / not-eligible / need-info classification, scoring, profile completion |
| `test_ocr_parsing.py` | 9 | Field extraction (name, DOB, address, ID), Aadhaar/PAN/Voter masking, empty-input safety |
| `test_auth.py` | 10 | Landing page, registration, duplicate guard, password hashing, login/logout, access control, admin gate |
| `test_documents.py` | 8 | MIME detection by signature, stream reset, valid upload, fake-file rejection, ownership 404 |
| `test_schemes_eligibility.py` | 6 | Scheme list/detail, eligibility check + history, recommendations refresh, application checklist seeding, print view |
| `test_admin.py` | 6 | Admin dashboard, scheme create, rule add, user enable/disable, broadcast, disabled-user login block |
| **Total** | **49** | |

All tests run against an **in-memory SQLite** database with a fresh, seeded
state per test (see `tests/conftest.py`).

## 2. Defects found and fixed during testing

| # | Defect | How found | Fix |
|---|--------|-----------|-----|
| 1 | Aadhaar regex used `\s?` between digit groups, so it matched across a newline — a 4-digit DOB year on the line above (`2004\n1234 5678`) was mis-read as part of the ID number. | `test_extract_id_number_is_masked` returned `XXXX XXXX 5678` instead of `9012`. | Changed the separator to a literal optional space ` ?` so matches never span lines (`services/ocr_service.py`). |
| 2 | Registration with a `.local` email appeared to silently fail. | Register tests. | Confirmed correct behaviour — `email-validator` rejects reserved `.local` domains. Test data corrected to a valid domain; app behaviour unchanged. |

## 3. Manual / exploratory checks

| Check | Expected | Status |
|-------|----------|--------|
| App boots and auto-creates tables | No error, `instance/welfare.db` created | Pass |
| `python seed.py` | 4 users, 8 schemes created, idempotent on re-run | Pass |
| Every Python module imports (via app factory + pytest) | No import errors | Pass (29/29 files, 0 syntax errors via `ast`) |
| Security headers present on responses | CSP, X-Frame-Options, nosniff | Pass (set in `app.after_request`) |
| Non-admin hitting `/admin/` | HTTP 403 | Pass |
| Upload of a non-image renamed `.png` | Rejected ("content does not match") | Pass |

## 4. Not executed in this environment

- **Live Tesseract OCR** on real images: the OCR *text-parsing and masking*
  logic is fully unit-tested, but running Tesseract on an actual image/PDF
  requires the Tesseract binary, which is not installed in the build
  environment. The pipeline is wired and degrades gracefully (a clear flash
  message) when the engine is absent.
- **Browser/JS behaviour** (menu toggle, scroll reveal, password hint): these
  are progressive enhancements; the app is fully functional without them and
  they are not covered by automated tests.

## 5. How to reproduce

```powershell
cd AI_Welfare_Platform
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```
