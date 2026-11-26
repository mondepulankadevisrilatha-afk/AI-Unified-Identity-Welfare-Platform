"""Pure-logic tests for the eligibility rules engine (no Flask needed)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import rules_engine as re


def test_check_rule_pass_and_fail():
    passed, _ = re.check_rule({"age": 20}, "age", "<=", "30")
    assert passed is True
    passed, _ = re.check_rule({"age": 40}, "age", "<=", "30")
    assert passed is False


def test_check_rule_missing_returns_none():
    passed, reason = re.check_rule({}, "age", "<=", "30")
    assert passed is None
    assert "Missing" in reason


def test_boolean_operators():
    assert re.check_rule({"is_student": True}, "is_student", "is_true", "true")[0] is True
    assert re.check_rule({"is_student": False}, "is_student", "is_true", "true")[0] is False
    assert re.check_rule({"is_farmer": False}, "is_farmer", "is_false", "true")[0] is True


def test_in_operator():
    assert re.check_rule({"social_category": "SC"}, "social_category", "in", "SC|ST|OBC")[0] is True
    assert re.check_rule({"social_category": "General"}, "social_category", "in", "SC|ST")[0] is False


def test_equality_case_insensitive():
    assert re.check_rule({"gender": "female"}, "gender", "==", "Female")[0] is True


def test_evaluate_eligible():
    profile = {"age": 20, "annual_income": 100000, "is_student": True}
    rules = [
        {"field": "is_student", "operator": "is_true", "value": "true"},
        {"field": "annual_income", "operator": "<=", "value": "250000"},
        {"field": "age", "operator": "<=", "value": "30"},
    ]
    out = re.evaluate(profile, rules)
    assert out["result"] == re.RESULT_ELIGIBLE
    assert out["score"] == 100


def test_evaluate_not_eligible():
    profile = {"age": 20, "annual_income": 900000, "is_student": True}
    rules = [{"field": "annual_income", "operator": "<=", "value": "250000"}]
    out = re.evaluate(profile, rules)
    assert out["result"] == re.RESULT_NOT_ELIGIBLE


def test_evaluate_need_more_info():
    profile = {"is_student": True}  # income missing
    rules = [
        {"field": "is_student", "operator": "is_true", "value": "true"},
        {"field": "annual_income", "operator": "<=", "value": "250000"},
    ]
    out = re.evaluate(profile, rules)
    assert out["result"] == re.RESULT_NEED_INFO


def test_evaluate_no_rules_is_likely():
    out = re.evaluate({}, [])
    assert out["result"] == re.RESULT_LIKELY


def test_profile_completion():
    assert re.profile_completion({}) == 0
    full = {f: (True if f.startswith("is_") else "x") for f in re.PROFILE_FIELDS}
    assert re.profile_completion(full) == 100
