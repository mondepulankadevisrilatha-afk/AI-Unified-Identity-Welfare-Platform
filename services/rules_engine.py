"""Transparent, rule-based eligibility engine.

This module is deliberately PURE Python: it imports neither Flask nor the
database. That keeps the decision logic easy to unit-test and easy to
explain in a viva — there is no hidden "AI black box", only readable rules.

A rule is a dict/record with: field, operator, value.
Supported operators: <=, >=, <, >, ==, !=, in, is_true, is_false.

evaluate() returns a result dict:
    {
        "result": "Eligible" | "Likely Eligible" | "Not Eligible" | "Need More Info",
        "score": 0-100,
        "reasons": [ ... human readable lines ... ],
    }
"""

RESULT_ELIGIBLE = "Eligible"
RESULT_LIKELY = "Likely Eligible"
RESULT_NOT_ELIGIBLE = "Not Eligible"
RESULT_NEED_INFO = "Need More Info"

# Profile fields the engine understands (used for completion scoring)
PROFILE_FIELDS = [
    "age", "gender", "annual_income", "social_category",
    "occupation", "state", "is_student", "is_farmer", "is_differently_abled",
]


def _coerce(value):
    """Turn a stored string rule value into int/bool/str as appropriate."""
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value).strip()
    low = text.lower()
    if low in ("true", "yes", "1"):
        return True
    if low in ("false", "no", "0"):
        return False
    try:
        return int(text)
    except (ValueError, TypeError):
        try:
            return float(text)
        except (ValueError, TypeError):
            return text


def check_rule(profile, field, operator, value):
    """Evaluate ONE rule against a profile dict.

    Returns a tuple: (passed: bool | None, reason: str)
    `None` means the profile is missing the data needed to decide.
    """
    actual = profile.get(field, None)

    # Missing data -> cannot decide this rule
    if actual is None or actual == "":
        return None, f"Missing information: {field.replace('_', ' ')}"

    expected = _coerce(value)
    label = field.replace("_", " ")

    try:
        if operator == "<=":
            passed = actual <= expected
            txt = f"{label} ({actual}) must be at most {expected}"
        elif operator == ">=":
            passed = actual >= expected
            txt = f"{label} ({actual}) must be at least {expected}"
        elif operator == "<":
            passed = actual < expected
            txt = f"{label} ({actual}) must be below {expected}"
        elif operator == ">":
            passed = actual > expected
            txt = f"{label} ({actual}) must be above {expected}"
        elif operator == "==":
            passed = str(actual).lower() == str(expected).lower()
            txt = f"{label} must be {expected}"
        elif operator == "!=":
            passed = str(actual).lower() != str(expected).lower()
            txt = f"{label} must not be {expected}"
        elif operator == "in":
            options = [o.strip().lower() for o in str(value).split("|")]
            passed = str(actual).lower() in options
            txt = f"{label} must be one of: {', '.join(options)}"
        elif operator == "is_true":
            passed = bool(actual) is True
            txt = f"{label} must be yes"
        elif operator == "is_false":
            passed = bool(actual) is False
            txt = f"{label} must be no"
        else:
            return None, f"Unknown rule operator '{operator}'"
    except TypeError:
        return None, f"Could not compare {label}"

    mark = "OK" if passed else "Not met"
    return passed, f"[{mark}] {txt}"


def evaluate(profile, rules):
    """Evaluate a profile against a list of rules for one scheme.

    `rules` is an iterable of objects/dicts exposing .field .operator .value
    (EligibilityRule rows) OR plain 3-key dicts.
    """
    normalised = []
    for r in rules:
        if isinstance(r, dict):
            normalised.append((r["field"], r["operator"], r["value"]))
        else:
            normalised.append((r.field, r.operator, r.value))

    if not normalised:
        return {
            "result": RESULT_LIKELY,
            "score": 60,
            "reasons": ["No specific rules are defined for this scheme; "
                        "most applicants may apply. Please verify on the "
                        "official portal."],
        }

    reasons = []
    passed_count = 0
    failed_count = 0
    missing_count = 0

    for field, operator, value in normalised:
        passed, reason = check_rule(profile, field, operator, value)
        reasons.append(reason)
        if passed is True:
            passed_count += 1
        elif passed is False:
            failed_count += 1
        else:
            missing_count += 1

    total = len(normalised)
    score = int(round((passed_count / total) * 100)) if total else 0

    if failed_count > 0:
        result = RESULT_NOT_ELIGIBLE
    elif missing_count > 0:
        result = RESULT_NEED_INFO
    elif passed_count == total:
        result = RESULT_ELIGIBLE
    else:
        result = RESULT_LIKELY

    return {"result": result, "score": score, "reasons": reasons}


def profile_completion(profile):
    """Return 0-100 completeness of the profile fields the engine uses."""
    filled = 0
    for f in PROFILE_FIELDS:
        v = profile.get(f, None)
        # booleans always count as answered
        if isinstance(v, bool):
            filled += 1
        elif v not in (None, ""):
            filled += 1
    return int(round((filled / len(PROFILE_FIELDS)) * 100))
