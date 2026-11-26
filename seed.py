"""Seed the database with a demo admin, demo users and sample schemes +
eligibility rules. All data here is FICTIONAL and for demonstration only.

Run:  python seed.py
"""
from app import create_app
from extensions import db
from models import User, Scheme, EligibilityRule, Category
from config import Config


DEMO_USERS = [
    # username, email, password, role, profile
    ("admin", "admin@welfare.local", "Admin@123", "admin", {
        "full_name": "Platform Administrator",
    }),
    ("asha", "asha@example.com", "Demo@123", "user", {
        "full_name": "Asha Kumari", "age": 21, "gender": "Female",
        "annual_income": 120000, "social_category": "OBC",
        "occupation": "Student", "state": "Tamil Nadu", "is_student": True,
    }),
    ("ravi", "ravi@example.com", "Demo@123", "user", {
        "full_name": "Ravi Patel", "age": 44, "gender": "Male",
        "annual_income": 90000, "social_category": "General",
        "occupation": "Farmer", "state": "Gujarat", "is_farmer": True,
    }),
    ("meena", "meena@example.com", "Demo@123", "user", {
        "full_name": "Meena Devi", "age": 67, "gender": "Female",
        "annual_income": 60000, "social_category": "SC",
        "occupation": "Retired", "state": "Bihar",
    }),
]


# Each scheme: dict of fields + a list of (field, operator, value, description)
SCHEMES = [
    {
        "scheme_name": "National Scholarship for Students",
        "category": "Education",
        "description": "Financial assistance for students from low-income "
                       "families pursuing higher education.",
        "benefits": "Up to INR 20,000 per year towards tuition and materials.",
        "official_url": "https://scholarships.gov.in",
        "required_documents": "Aadhaar Card, Income Certificate, Bank Passbook",
        "rules": [
            ("is_student", "is_true", "true", "Applicant must be a student"),
            ("annual_income", "<=", "250000", "Family income at most INR 2.5 lakh"),
            ("age", "<=", "30", "Age 30 or below"),
        ],
    },
    {
        "scheme_name": "PM Kisan Support",
        "category": "Agriculture",
        "description": "Income support for small and marginal farmer families.",
        "benefits": "INR 6,000 per year in three equal instalments.",
        "official_url": "https://pmkisan.gov.in",
        "required_documents": "Aadhaar Card, Bank Passbook, Land records",
        "rules": [
            ("is_farmer", "is_true", "true", "Applicant must be a farmer"),
            ("annual_income", "<=", "200000", "Income at most INR 2 lakh"),
        ],
    },
    {
        "scheme_name": "Senior Citizen Pension",
        "category": "Senior Citizen",
        "description": "Monthly pension for elderly citizens below the "
                       "poverty line.",
        "benefits": "INR 1,000 monthly pension.",
        "official_url": "https://nsap.nic.in",
        "required_documents": "Aadhaar Card, Age proof, Bank Passbook",
        "rules": [
            ("age", ">=", "60", "Age 60 or above"),
            ("annual_income", "<=", "120000", "Income at most INR 1.2 lakh"),
        ],
    },
    {
        "scheme_name": "Housing for All",
        "category": "Housing",
        "description": "Subsidised housing assistance for eligible families "
                       "without a permanent home.",
        "benefits": "Interest subsidy on home loans and direct assistance.",
        "official_url": "https://pmaymis.gov.in",
        "required_documents": "Aadhaar Card, Income Certificate, Ration Card",
        "rules": [
            ("annual_income", "<=", "600000", "Income at most INR 6 lakh"),
        ],
    },
    {
        "scheme_name": "Women Entrepreneurship Grant",
        "category": "Women & Child",
        "description": "Seed grant and mentoring for women starting small "
                       "businesses.",
        "benefits": "Grant up to INR 50,000 plus mentoring.",
        "official_url": "https://www.standupmitra.in",
        "required_documents": "Aadhaar Card, PAN Card, Bank Passbook",
        "rules": [
            ("gender", "==", "Female", "Applicant must be female"),
            ("age", ">=", "18", "Age 18 or above"),
        ],
    },
    {
        "scheme_name": "Skill Development & Employment",
        "category": "Employment",
        "description": "Free skill training and placement assistance for "
                       "unemployed youth.",
        "benefits": "Free certified training and placement support.",
        "official_url": "https://www.pmkvyofficial.org",
        "required_documents": "Aadhaar Card, Education certificate",
        "rules": [
            ("age", ">=", "18", "Age 18 or above"),
            ("age", "<=", "45", "Age 45 or below"),
        ],
    },
    {
        "scheme_name": "Health Coverage Scheme",
        "category": "Health",
        "description": "Cashless health insurance cover for economically "
                       "weaker families.",
        "benefits": "Health cover up to INR 5 lakh per family per year.",
        "official_url": "https://pmjay.gov.in",
        "required_documents": "Aadhaar Card, Ration Card",
        "rules": [
            ("annual_income", "<=", "180000", "Income at most INR 1.8 lakh"),
        ],
    },
    {
        "scheme_name": "Financial Inclusion Account",
        "category": "Financial Inclusion",
        "description": "Zero-balance bank account with accident insurance "
                       "for unbanked citizens.",
        "benefits": "Zero-balance account, RuPay card and accident cover.",
        "official_url": "https://pmjdy.gov.in",
        "required_documents": "Aadhaar Card",
        "rules": [
            ("age", ">=", "10", "Age 10 or above"),
        ],
    },
]


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Users
        for username, email, password, role, profile in DEMO_USERS:
            if User.query.filter_by(username=username).first():
                continue
            user = User(username=username, email=email, role=role, **profile)
            user.set_password(password)
            db.session.add(user)

        # Categories (admin-managed copies of the built-ins)
        for name in Config.DOCUMENT_CATEGORIES:
            if not Category.query.filter_by(name=name, kind="document").first():
                db.session.add(Category(name=name, kind="document"))
        for name in Config.SCHEME_CATEGORIES:
            if not Category.query.filter_by(name=name, kind="scheme").first():
                db.session.add(Category(
                    name=name, kind="scheme",
                    icon=Config.SCHEME_CATEGORY_ICONS.get(name)))

        # Schemes + rules
        for s in SCHEMES:
            if Scheme.query.filter_by(scheme_name=s["scheme_name"]).first():
                continue
            scheme = Scheme(
                scheme_name=s["scheme_name"],
                category=s["category"],
                description=s["description"],
                benefits=s["benefits"],
                official_url=s["official_url"],
                required_documents=s["required_documents"],
                is_active=True,
            )
            db.session.add(scheme)
            db.session.flush()
            for field, operator, value, desc in s["rules"]:
                db.session.add(EligibilityRule(
                    scheme_id=scheme.id, field=field, operator=operator,
                    value=value, description=desc))

        db.session.commit()
        print("Seed complete.")
        print("  Admin login : admin@welfare.local / Admin@123")
        print("  Demo user   : asha@example.com   / Demo@123")
        print(f"  Schemes     : {Scheme.query.count()}")
        print(f"  Users       : {User.query.count()}")


if __name__ == "__main__":
    run()
