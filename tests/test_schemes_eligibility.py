"""Scheme explorer, eligibility checker, recommendations, applications."""
from models import Scheme, EligibilityCheck, Application, Recommendation


def test_schemes_list_public(client):
    assert client.get("/schemes/").status_code == 200


def test_scheme_detail(client, app):
    with app.app_context():
        sid = Scheme.query.first().id
    r = client.get(f"/schemes/{sid}")
    assert r.status_code == 200
    assert b"About this scheme" in r.data


def test_eligibility_check_saves_history(auth_user, app):
    with app.app_context():
        sid = Scheme.query.first().id
    r = auth_user.post("/eligibility/", data={
        "scheme_id": sid, "age": 21, "annual_income": 100000,
        "is_student": "y",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b"Eligible" in r.data
    with app.app_context():
        assert EligibilityCheck.query.count() == 1


def test_recommendations_refresh(auth_user, app):
    r = auth_user.post("/recommendations/refresh", follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert Recommendation.query.count() >= 1


def test_create_application_seeds_checklist(auth_user, app):
    with app.app_context():
        sid = Scheme.query.first().id
    r = auth_user.post("/applications/new", data={
        "scheme_id": sid, "status": "Not Started",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        app_row = Application.query.first()
        assert app_row is not None
        # scheme had 2 required documents -> 2 checklist items
        assert len(app_row.checklist) == 2


def test_eligibility_print(auth_user, app):
    with app.app_context():
        sid = Scheme.query.first().id
    auth_user.post("/eligibility/", data={
        "scheme_id": sid, "age": 21, "annual_income": 100000, "is_student": "y",
    })
    with app.app_context():
        cid = EligibilityCheck.query.first().id
    r = auth_user.get(f"/eligibility/{cid}/print")
    assert r.status_code == 200
    assert b"Eligibility Result" in r.data
