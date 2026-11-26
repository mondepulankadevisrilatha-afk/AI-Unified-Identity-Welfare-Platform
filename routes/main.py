"""Landing page, dashboard, notifications and settings."""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Document, Application, Recommendation, Notification, Scheme
from forms import PasswordChangeForm
from services.common import log_action
from services import recommendation_service
from services.rules_engine import profile_completion

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    schemes = Scheme.query.filter_by(is_active=True).limit(6).all()
    return render_template("index.html", schemes=schemes)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    doc_count = Document.query.filter_by(user_id=uid).count()
    app_count = Application.query.filter_by(user_id=uid).count()
    rec_count = Recommendation.query.filter_by(user_id=uid).filter(
        Recommendation.result.in_(["Eligible", "Likely Eligible"])
    ).count()

    completion = profile_completion(current_user.profile_dict())
    top = recommendation_service.top_recommendations(current_user, limit=3)

    # chart data: applications grouped by status
    status_counts = {}
    for app in Application.query.filter_by(user_id=uid).all():
        status_counts[app.status] = status_counts.get(app.status, 0) + 1

    # documents by category (for a small chart)
    cat_counts = {}
    for d in Document.query.filter_by(user_id=uid).all():
        cat_counts[d.category] = cat_counts.get(d.category, 0) + 1

    reminders = (
        Application.query.filter_by(user_id=uid)
        .filter(Application.reminder_date.isnot(None))
        .order_by(Application.reminder_date.asc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        doc_count=doc_count,
        app_count=app_count,
        rec_count=rec_count,
        completion=completion,
        top=top,
        status_counts=status_counts,
        cat_counts=cat_counts,
        reminders=reminders,
    )


@main_bp.route("/notifications")
@login_required
def notifications():
    notes = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    # mark all as read on view
    for n in notes:
        n.is_read = True
    db.session.commit()
    return render_template("notifications.html", notes=notes)


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            log_action("password_change", "password updated")
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("main.settings"))
    return render_template("settings.html", form=form)
