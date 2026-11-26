"""Central configuration for the AI Welfare Platform.

All tunable settings live here so the rest of the code never hard-codes
paths, limits, or category lists. Secrets come from the environment; a
development fallback is used only when the variable is not set.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Security -------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # token valid for the whole session

    # Remember-me cookie hardening
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Database -------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "welfare.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads --------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB hard limit
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

    # --- OCR ------------------------------------------------------------
    # Path to the Tesseract executable. On Windows this is typically
    # C:\Program Files\Tesseract-OCR\tesseract.exe. Leave blank to use PATH.
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")

    # --- Domain category lists -----------------------------------------
    DOCUMENT_CATEGORIES = [
        "Aadhaar Card",
        "PAN Card",
        "Voter ID",
        "Ration Card",
        "Driving License",
        "Income Certificate",
        "Caste Certificate",
        "Bank Passbook",
        "Other",
    ]

    SCHEME_CATEGORIES = [
        "Education",
        "Health",
        "Housing",
        "Employment",
        "Agriculture",
        "Women & Child",
        "Senior Citizen",
        "Financial Inclusion",
    ]

    SCHEME_CATEGORY_ICONS = {
        "Education": "fa-graduation-cap",
        "Health": "fa-heart-pulse",
        "Housing": "fa-house",
        "Employment": "fa-briefcase",
        "Agriculture": "fa-wheat-awn",
        "Women & Child": "fa-children",
        "Senior Citizen": "fa-person-cane",
        "Financial Inclusion": "fa-piggy-bank",
    }

    GENDERS = ["Male", "Female", "Other"]
    CATEGORIES_SOCIAL = ["General", "OBC", "SC", "ST", "EWS"]

    APPLICATION_STATUSES = [
        "Not Started",
        "Documents Ready",
        "Submitted",
        "Under Review",
        "Approved",
        "Rejected",
    ]
