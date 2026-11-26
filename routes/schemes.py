"""Scheme explorer and scheme detail."""
from flask import (
    Blueprint, render_template, request, current_app,
)
from flask_login import current_user

from models import Scheme
from services import rules_engine

schemes_bp = Blueprint("schemes", __name__, url_prefix="/schemes")


@schemes_bp.route("/")
def explore():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Scheme.query.filter_by(is_active=True)
    if q:
        query = query.filter(Scheme.scheme_name.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    schemes = query.order_by(Scheme.scheme_name.asc()).all()
    return render_template(
        "schemes/list.html",
        schemes=schemes,
        q=q,
        category=category,
        categories=current_app.config["SCHEME_CATEGORIES"],
        icons=current_app.config["SCHEME_CATEGORY_ICONS"],
    )


@schemes_bp.route("/<int:scheme_id>")
def detail(scheme_id):
    scheme = Scheme.query.get_or_404(scheme_id)
    outcome = None
    if current_user.is_authenticated:
        outcome = rules_engine.evaluate(current_user.profile_dict(), scheme.rules)
    return render_template("schemes/detail.html", scheme=scheme, outcome=outcome)
