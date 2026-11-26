"""Personalised recommendations with a refresh button and category filter."""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, current_app,
)
from flask_login import login_required, current_user

from models import Recommendation
from services import recommendation_service

recommendations_bp = Blueprint("recommendations", __name__,
                               url_prefix="/recommendations")


@recommendations_bp.route("/")
@login_required
def index():
    category = request.args.get("category", "").strip()
    recs = (
        Recommendation.query.filter_by(user_id=current_user.id)
        .order_by(Recommendation.score.desc())
        .all()
    )
    if category:
        recs = [r for r in recs if r.scheme and r.scheme.category == category]
    return render_template(
        "recommendations/index.html",
        recs=recs,
        category=category,
        categories=current_app.config["SCHEME_CATEGORIES"],
    )


@recommendations_bp.route("/refresh", methods=["POST"])
@login_required
def refresh():
    count = recommendation_service.refresh_for_user(current_user)
    flash(f"Recommendations refreshed — {count} schemes evaluated.", "success")
    return redirect(url_for("recommendations.index"))
