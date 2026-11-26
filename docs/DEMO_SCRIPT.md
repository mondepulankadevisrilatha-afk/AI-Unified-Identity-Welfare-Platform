# Demo Script (≈ 6–8 minutes)

A suggested walkthrough for the project demo / viva.

## Setup (before the demo)
```powershell
cd AI_Welfare_Platform
.\venv\Scripts\Activate.ps1
python seed.py      # fresh demo data
python app.py       # http://127.0.0.1:5000
```

## 1. Landing page (30s)
- Open `/`. Point out the hero, the six feature cards, the popular-schemes
  preview, and "How it works".

## 2. Register & profile (1 min)
- Click **Sign up**. Create `demo_student@example.com`. Show the live
  "passwords match" hint.
- Log in. Go to **Profile**. Fill: age 21, Female, income 120000, OBC,
  tick *student*. Save — note the **profile completeness** bar and the flash
  "N schemes re-evaluated".

## 3. Dashboard (30s)
- Show the four stat tiles, top recommendations with match bars, and the two
  mini bar charts (applications by status, documents by category).

## 4. Document Vault + Scanner (1.5 min)
- **Upload** a document (any PDF/PNG/JPG). Show it appears with status
  *Uploaded*.
- Try uploading a `.txt` renamed to `.png` → rejected ("content does not
  match") to demonstrate signature validation.
- Open the document → **Scan document**. On the review screen, point out the
  **masked ID number** and that you can edit values. **Confirm** → status
  becomes *Verified* and details are saved.

## 5. Schemes & recommendations (1.5 min)
- **Schemes** → open "National Scholarship for Students". Show the
  **"Do I qualify?"** panel: result, score, and the plain-language reasons.
- **For You** → show the ranked recommendations; expand **Why?** on one.
  Click **Refresh**.

## 6. Eligibility checker (1 min)
- **Eligibility** → pick a scheme; values are pre-filled from the profile.
  Change income to a high value → result flips to *Not Eligible* with the
  failing reason. Submit a passing case → open the **print** sheet.

## 7. Application tracker (1 min)
- From a scheme, **Track an application**. Note the checklist is auto-seeded
  from the scheme's required documents.
- Tick checklist items (progress bar moves), change **status**, set a
  **reminder date**, open the **print** summary.

## 8. Admin (1.5 min) — log in as `admin@welfare.local` / `Admin@123`
- **Admin dashboard**: statistics + charts + recent activity.
- **Schemes** → create a scheme → add an eligibility **rule**.
- **Users** → disable the demo user; try logging in as them in a private
  window → blocked.
- **Notifications** → broadcast a message; show the bell badge on the user.
- **Activity log** → show the audit trail.

## Closing line
> "The recommendation engine is rule-based and fully transparent — every
> decision shows its reasons — and the OCR flow never stores anything the user
> hasn't confirmed, with ID numbers masked throughout."
