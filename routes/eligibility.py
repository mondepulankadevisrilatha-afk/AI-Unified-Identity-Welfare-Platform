"""Manual eligibility checker with saved history and a print view."""
import json

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
)
from flask_login import login_required, current_user

from extensions import db
from models import Scheme, EligibilityCheck
from forms import EligibilityForm
from services import rules_engine
from services.common import owned_or_404, log_action

eligibility_bp = Blueprint("eligibility", __name__, url_prefix="/eligibility")

_PROFILE_KEYS = [
    "age", "gender", "annual_income", "social_category",
    "occupation", "state", "is_student", "is_farmer", "is_differently_abled",
]


@eligibility_bp.route("/", methods=["GET", "POST"])
@login_required
def check():
    form = EligibilityForm()
    schemes = Scheme.query.filter_by(is_active=True).order_by(Scheme.scheme_name).all()
    form.scheme_id.choices = [(s.id, s.scheme_name) for s in schemes]

    # Pre-fill from the user's profile on first GET
    if not form.is_submitted():
        for key in _PROFILE_KEYS:
            field = getattr(form, key, None)
            if field is not None:
                field.data = getattr(current_user, key)

    result = None
    checked_scheme = None
    if form.validate_on_submit():
        scheme = Scheme.query.get_or_404(form.scheme_id.data)
        checked_scheme = scheme
        profile = {k: getattr(form, k).data for k in _PROFILE_KEYS}
        result = rules_engine.evaluate(profile, scheme.rules)

        check_row = EligibilityCheck(
            user_id=current_user.id,
            scheme_id=scheme.id,
            result=result["result"],
            score=result["score"],
            reasons="\n".join(result["reasons"]),
            input_snapshot=json.dumps(profile, default=str),
        )
        db.session.add(check_row)
        log_action("eligibility_check", f"{scheme.scheme_name} -> {result['result']}")
        db.session.commit()

    history = (
        EligibilityCheck.query.filter_by(user_id=current_user.id)
        .order_by(EligibilityCheck.checked_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "eligibility/check.html",
        form=form,
        result=result,
        checked_scheme=checked_scheme,
        history=history,
    )


@eligibility_bp.route("/<int:check_id>/print")
@login_required
def print_view(check_id):
    check = owned_or_404(EligibilityCheck.query.get(check_id))
    snapshot = {}
    if check.input_snapshot:
        try:
            snapshot = json.loads(check.input_snapshot)
        except (ValueError, TypeError):
            snapshot = {}
    return render_template("eligibility/print.html", check=check, snapshot=snapshot)
