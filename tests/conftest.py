"""Shared pytest fixtures: an app configured for testing with an in-memory
database, a test client, and a seeded admin + user.
"""
import os
import sys
import tempfile

import pytest

# Make the project root importable when pytest runs from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from app import create_app
from extensions import db as _db
from models import User, Scheme, EligibilityRule


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False               # simplifies form posts in tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp()
    with app.app_context():
        _db.create_all()
        _seed()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed():
    admin = User(username="admin", email="admin@test.local", role="admin")
    admin.set_password("Admin@123")
    user = User(username="asha", email="asha@test.local", role="user",
                age=21, gender="Female", annual_income=120000,
                social_category="OBC", is_student=True)
    user.set_password("Demo@123")
    _db.session.add_all([admin, user])

    scheme = Scheme(scheme_name="Student Scholarship", category="Education",
                    description="For students.", is_active=True,
                    required_documents="Aadhaar Card, Income Certificate")
    _db.session.add(scheme)
    _db.session.flush()
    _db.session.add_all([
        EligibilityRule(scheme_id=scheme.id, field="is_student",
                        operator="is_true", value="true"),
        EligibilityRule(scheme_id=scheme.id, field="annual_income",
                        operator="<=", value="250000"),
    ])
    _db.session.commit()


@pytest.fixture()
def auth_user(client):
    """Log in as the demo user and return the client."""
    client.post("/login", data={"identifier": "asha@test.local",
                                "password": "Demo@123"})
    return client


@pytest.fixture()
def auth_admin(client):
    client.post("/login", data={"identifier": "admin@test.local",
                                "password": "Admin@123"})
    return client
