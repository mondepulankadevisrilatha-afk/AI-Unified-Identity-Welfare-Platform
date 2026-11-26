"""Database models (SQLAlchemy ORM).

Eleven tables covering users, their documents, the scheme catalogue, the
transparent eligibility engine, recommendations, saved eligibility checks,
the application tracker with its checklist, in-app notifications, an audit
log, and admin-managed categories.

Field names follow the Phase 3 naming decided in the original build
(`username`, `document_name`, `file_path`, `extracted_name`,
`scheme_name`, `official_url`, ...).
"""
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


def _now():
    return datetime.utcnow()


# --------------------------------------------------------------------------
# 1. User
# --------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user | admin
    account_active = db.Column(db.Boolean, nullable=False, default=True)

    # Profile fields used by the eligibility engine
    full_name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    annual_income = db.Column(db.Integer)          # in INR
    social_category = db.Column(db.String(20))     # General / OBC / SC / ST / EWS
    occupation = db.Column(db.String(80))
    state = db.Column(db.String(80))
    is_student = db.Column(db.Boolean, default=False)
    is_farmer = db.Column(db.Boolean, default=False)
    is_differently_abled = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    documents = db.relationship("Document", backref="owner", lazy=True,
                                cascade="all, delete-orphan")
    recommendations = db.relationship("Recommendation", backref="user", lazy=True,
                                      cascade="all, delete-orphan")
    eligibility_checks = db.relationship("EligibilityCheck", backref="user", lazy=True,
                                         cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="user", lazy=True,
                                   cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy=True,
                                    cascade="all, delete-orphan")

    # -- password helpers ----------------------------------------------
    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self):
        return self.role == "admin"

    # Flask-Login treats account_active == False as a disabled account
    @property
    def is_active(self):
        return bool(self.account_active)

    def profile_dict(self):
        """The subset of fields the rules engine reads."""
        return {
            "age": self.age,
            "gender": self.gender,
            "annual_income": self.annual_income,
            "social_category": self.social_category,
            "occupation": self.occupation,
            "state": self.state,
            "is_student": self.is_student,
            "is_farmer": self.is_farmer,
            "is_differently_abled": self.is_differently_abled,
        }

    def __repr__(self):
        return f"<User {self.username}>"


# --------------------------------------------------------------------------
# 2. Document
# --------------------------------------------------------------------------
class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    document_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)   # stored (random) filename
    original_name = db.Column(db.String(255))
    mime_type = db.Column(db.String(60))
    status = db.Column(db.String(30), default="Uploaded")   # Uploaded | Verified | Expired

    # Data extracted by OCR (only after the user confirms it in the scanner)
    extracted_name = db.Column(db.String(150))
    extracted_dob = db.Column(db.String(40))
    extracted_address = db.Column(db.Text)
    extracted_number = db.Column(db.String(60))             # masked ID number
    is_confirmed = db.Column(db.Boolean, default=False)

    uploaded_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return f"<Document {self.document_name}>"


# --------------------------------------------------------------------------
# 3. Scheme
# --------------------------------------------------------------------------
class Scheme(db.Model):
    __tablename__ = "schemes"

    id = db.Column(db.Integer, primary_key=True)
    scheme_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    benefits = db.Column(db.Text)
    official_url = db.Column(db.String(255))
    required_documents = db.Column(db.Text)   # comma-separated list
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    rules = db.relationship("EligibilityRule", backref="scheme", lazy=True,
                            cascade="all, delete-orphan")

    def required_documents_list(self):
        if not self.required_documents:
            return []
        return [d.strip() for d in self.required_documents.split(",") if d.strip()]

    def __repr__(self):
        return f"<Scheme {self.scheme_name}>"


# --------------------------------------------------------------------------
# 4. EligibilityRule  (transparent, admin-editable rules per scheme)
# --------------------------------------------------------------------------
class EligibilityRule(db.Model):
    __tablename__ = "eligibility_rules"

    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey("schemes.id"),
                          nullable=False, index=True)

    field = db.Column(db.String(60), nullable=False)      # e.g. age, annual_income
    operator = db.Column(db.String(20), nullable=False)   # <=, >=, ==, in, is_true
    value = db.Column(db.String(120), nullable=False)     # compared value(s)
    description = db.Column(db.String(200))               # human-readable rule

    def __repr__(self):
        return f"<Rule {self.field} {self.operator} {self.value}>"


# --------------------------------------------------------------------------
# 5. Recommendation
# --------------------------------------------------------------------------
class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey("schemes.id"), nullable=False, index=True)

    result = db.Column(db.String(30), nullable=False)   # Eligible / Likely / Not Eligible / Need More Info
    score = db.Column(db.Integer, default=0)            # 0-100 match score
    reasons = db.Column(db.Text)                        # newline-joined explanation
    generated_at = db.Column(db.DateTime, default=_now)

    scheme = db.relationship("Scheme", lazy=True)

    def reasons_list(self):
        return [r for r in (self.reasons or "").split("\n") if r]


# --------------------------------------------------------------------------
# 6. EligibilityCheck  (saved history of manual checks)
# --------------------------------------------------------------------------
class EligibilityCheck(db.Model):
    __tablename__ = "eligibility_checks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey("schemes.id"), nullable=False, index=True)

    result = db.Column(db.String(30), nullable=False)
    score = db.Column(db.Integer, default=0)
    reasons = db.Column(db.Text)
    input_snapshot = db.Column(db.Text)   # JSON of the values used
    checked_at = db.Column(db.DateTime, default=_now)

    scheme = db.relationship("Scheme", lazy=True)

    def reasons_list(self):
        return [r for r in (self.reasons or "").split("\n") if r]


# --------------------------------------------------------------------------
# 7. Application  (tracker)
# --------------------------------------------------------------------------
class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey("schemes.id"), nullable=False, index=True)

    status = db.Column(db.String(30), nullable=False, default="Not Started")
    notes = db.Column(db.Text)
    reference_number = db.Column(db.String(80))
    submitted_on = db.Column(db.Date)
    reminder_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    scheme = db.relationship("Scheme", lazy=True)
    checklist = db.relationship("ApplicationChecklist", backref="application", lazy=True,
                                cascade="all, delete-orphan")

    @property
    def is_reminder_due(self):
        return bool(self.reminder_date and self.reminder_date <= date.today())


# --------------------------------------------------------------------------
# 8. ApplicationChecklist
# --------------------------------------------------------------------------
class ApplicationChecklist(db.Model):
    __tablename__ = "application_checklist"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"),
                               nullable=False, index=True)
    item = db.Column(db.String(150), nullable=False)
    is_done = db.Column(db.Boolean, default=False)


# --------------------------------------------------------------------------
# 9. Notification
# --------------------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(30), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_now)


# --------------------------------------------------------------------------
# 10. ActivityLog  (audit trail)
# --------------------------------------------------------------------------
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.String(255))
    ip_address = db.Column(db.String(60))
    created_at = db.Column(db.DateTime, default=_now)


# --------------------------------------------------------------------------
# 11. Category  (admin-managed document / scheme categories)
# --------------------------------------------------------------------------
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    kind = db.Column(db.String(20), nullable=False)   # document | scheme
    icon = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=_now)
