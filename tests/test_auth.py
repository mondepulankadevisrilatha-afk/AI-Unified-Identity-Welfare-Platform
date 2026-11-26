"""Authentication & access-control tests."""
from models import User


def test_landing_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"welfare" in r.data.lower()


def test_register_creates_user(client, app):
    r = client.post("/register", data={
        "username": "newuser", "email": "new@example.com",
        "full_name": "New User", "password": "secret1", "confirm": "secret1",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username="newuser").first() is not None


def test_register_duplicate_username(client):
    r = client.post("/register", data={
        "username": "asha", "email": "other@example.com",
        "password": "secret1", "confirm": "secret1",
    }, follow_redirects=True)
    assert b"already taken" in r.data


def test_password_is_hashed(app):
    with app.app_context():
        u = User.query.filter_by(username="asha").first()
        assert u.password_hash != "Demo@123"
        assert u.check_password("Demo@123")


def test_login_logout(client):
    r = client.post("/login", data={"identifier": "asha@test.local",
                                    "password": "Demo@123"},
                    follow_redirects=True)
    assert b"Welcome back" in r.data
    r = client.post("/logout", follow_redirects=True)
    assert b"logged out" in r.data


def test_login_wrong_password(client):
    r = client.post("/login", data={"identifier": "asha@test.local",
                                    "password": "wrong"},
                    follow_redirects=True)
    assert b"Invalid credentials" in r.data


def test_dashboard_requires_login(client):
    r = client.get("/dashboard", follow_redirects=True)
    assert b"log in" in r.data.lower() or b"Welcome back" not in r.data


def test_dashboard_when_logged_in(auth_user):
    r = auth_user.get("/dashboard")
    assert r.status_code == 200
    assert b"snapshot" in r.data.lower()


def test_admin_blocked_for_user(auth_user):
    r = auth_user.get("/admin/")
    assert r.status_code == 403


def test_admin_ok_for_admin(auth_admin):
    r = auth_admin.get("/admin/")
    assert r.status_code == 200
