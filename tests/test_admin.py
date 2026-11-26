"""Admin area tests: scheme CRUD, rules, user management, broadcast."""
from models import Scheme, EligibilityRule, User, Notification


def test_admin_dashboard(auth_admin):
    r = auth_admin.get("/admin/")
    assert r.status_code == 200
    assert b"Admin dashboard" in r.data


def test_admin_create_scheme(auth_admin, app):
    r = auth_admin.post("/admin/schemes/new", data={
        "scheme_name": "New Scheme", "category": "Health",
        "description": "desc", "is_active": "y",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert Scheme.query.filter_by(scheme_name="New Scheme").first() is not None


def test_admin_add_rule(auth_admin, app):
    with app.app_context():
        sid = Scheme.query.first().id
        before = EligibilityRule.query.count()
    auth_admin.post(f"/admin/schemes/{sid}/rules", data={
        "field": "age", "operator": "<=", "value": "60",
    }, follow_redirects=True)
    with app.app_context():
        assert EligibilityRule.query.count() == before + 1


def test_admin_toggle_user(auth_admin, app):
    with app.app_context():
        uid = User.query.filter_by(username="asha").first().id
    auth_admin.post(f"/admin/users/{uid}/toggle", follow_redirects=True)
    with app.app_context():
        assert User.query.get(uid).account_active is False


def test_admin_broadcast(auth_admin, app):
    with app.app_context():
        before = Notification.query.count()
    auth_admin.post("/admin/notifications", data={"message": "Hello all"},
                    follow_redirects=True)
    with app.app_context():
        assert Notification.query.count() > before


def test_disabled_user_cannot_login(auth_admin, client, app):
    with app.app_context():
        uid = User.query.filter_by(username="asha").first().id
    auth_admin.post(f"/admin/users/{uid}/toggle")  # disable asha
    r = client.post("/login", data={"identifier": "asha@test.local",
                                    "password": "Demo@123"},
                    follow_redirects=True)
    assert b"disabled" in r.data.lower()
