"""Admin area: dashboard, user management, scheme CRUD, eligibility rules,
categories, broadcast notifications, activity logs and statistics.

Every route is protected by @admin_required.
"""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
)
from flask_login import login_required, current_user

from extensions import db
from models import (
    User, Scheme, EligibilityRule, Category, Application, Document,
    ActivityLog, Notification,
)
from forms import SchemeForm, RuleForm, CategoryForm, NotificationForm
from config import Config
from services.common import log_action, notify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def _guard():
    # Belt-and-braces: block non-admins before any admin view runs.
    if not current_user.is_admin:
        abort(403)


# -------------------- Dashboard & statistics --------------------
@admin_bp.route("/")
def dashboard():
    stats = {
        "users": User.query.count(),
        "admins": User.query.filter_by(role="admin").count(),
        "schemes": Scheme.query.count(),
        "active_schemes": Scheme.query.filter_by(is_active=True).count(),
        "documents": Document.query.count(),
        "applications": Application.query.count(),
    }
    # applications by status (chart data)
    status_counts = {}
    for a in Application.query.all():
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
    # schemes by category
    cat_counts = {}
    for s in Scheme.query.all():
        cat_counts[s.category] = cat_counts.get(s.category, 0) + 1
    recent_logs = (
        ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    )
    return render_template("admin/dashboard.html", stats=stats,
                           status_counts=status_counts, cat_counts=cat_counts,
                           recent_logs=recent_logs)


# -------------------- Users --------------------
@admin_bp.route("/users")
def users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, q=q)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "danger")
        return redirect(url_for("admin.users"))
    user.account_active = not user.account_active
    log_action("user_toggle",
               f"{user.username} active={user.account_active}")
    db.session.commit()
    state = "enabled" if user.account_active else "disabled"
    flash(f"User '{user.username}' {state}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get("role", "")
    if role not in ("user", "admin"):
        flash("Invalid role.", "danger")
    elif user.id == current_user.id and role != "admin":
        flash("You cannot remove your own admin role.", "danger")
    else:
        user.role = role
        log_action("user_role", f"{user.username} -> {role}")
        db.session.commit()
        flash(f"Role updated for '{user.username}'.", "success")
    return redirect(url_for("admin.users"))


# -------------------- Schemes --------------------
@admin_bp.route("/schemes")
def schemes():
    all_schemes = Scheme.query.order_by(Scheme.scheme_name).all()
    return render_template("admin/schemes.html", schemes=all_schemes)


@admin_bp.route("/schemes/new", methods=["GET", "POST"])
def scheme_create():
    form = SchemeForm()
    if form.validate_on_submit():
        scheme = Scheme()
        form.populate_obj(scheme)
        db.session.add(scheme)
        log_action("scheme_create", form.scheme_name.data)
        db.session.commit()
        flash("Scheme created. Add eligibility rules next.", "success")
        return redirect(url_for("admin.scheme_rules", scheme_id=scheme.id))
    return render_template("admin/scheme_form.html", form=form, mode="create")


@admin_bp.route("/schemes/<int:scheme_id>/edit", methods=["GET", "POST"])
def scheme_edit(scheme_id):
    scheme = Scheme.query.get_or_404(scheme_id)
    form = SchemeForm(obj=scheme)
    if form.validate_on_submit():
        form.populate_obj(scheme)
        log_action("scheme_edit", scheme.scheme_name)
        db.session.commit()
        flash("Scheme updated.", "success")
        return redirect(url_for("admin.schemes"))
    return render_template("admin/scheme_form.html", form=form, mode="edit",
                           scheme=scheme)


@admin_bp.route("/schemes/<int:scheme_id>/delete", methods=["POST"])
def scheme_delete(scheme_id):
    scheme = Scheme.query.get_or_404(scheme_id)
    name = scheme.scheme_name
    db.session.delete(scheme)
    log_action("scheme_delete", name)
    db.session.commit()
    flash(f"Scheme '{name}' deleted.", "info")
    return redirect(url_for("admin.schemes"))


# -------------------- Eligibility rules --------------------
@admin_bp.route("/schemes/<int:scheme_id>/rules", methods=["GET", "POST"])
def scheme_rules(scheme_id):
    scheme = Scheme.query.get_or_404(scheme_id)
    form = RuleForm()
    if form.validate_on_submit():
        rule = EligibilityRule(
            scheme_id=scheme.id,
            field=form.field.data,
            operator=form.operator.data,
            value=form.value.data.strip(),
            description=form.description.data or None,
        )
        db.session.add(rule)
        log_action("rule_add", f"{scheme.scheme_name}: {rule.field} {rule.operator}")
        db.session.commit()
        flash("Rule added.", "success")
        return redirect(url_for("admin.scheme_rules", scheme_id=scheme.id))
    return render_template("admin/scheme_rules.html", scheme=scheme, form=form)


@admin_bp.route("/rules/<int:rule_id>/delete", methods=["POST"])
def rule_delete(rule_id):
    rule = EligibilityRule.query.get_or_404(rule_id)
    scheme_id = rule.scheme_id
    db.session.delete(rule)
    log_action("rule_delete", str(rule_id))
    db.session.commit()
    flash("Rule removed.", "info")
    return redirect(url_for("admin.scheme_rules", scheme_id=scheme_id))


# -------------------- Categories --------------------
@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data.strip()).first():
            flash("That category already exists.", "warning")
        else:
            db.session.add(Category(
                name=form.name.data.strip(),
                kind=form.kind.data,
                icon=form.icon.data or None,
            ))
            log_action("category_add", form.name.data)
            db.session.commit()
            flash("Category added.", "success")
        return redirect(url_for("admin.categories"))
    all_categories = Category.query.order_by(Category.kind, Category.name).all()
    return render_template("admin/categories.html", form=form,
                           categories=all_categories,
                           builtin_doc=Config.DOCUMENT_CATEGORIES,
                           builtin_scheme=Config.SCHEME_CATEGORIES)


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    log_action("category_delete", cat.name)
    db.session.commit()
    flash("Category removed.", "info")
    return redirect(url_for("admin.categories"))


# -------------------- Notifications (broadcast) --------------------
@admin_bp.route("/notifications", methods=["GET", "POST"])
def notifications():
    form = NotificationForm()
    if form.validate_on_submit():
        count = 0
        for user in User.query.filter_by(account_active=True).all():
            notify(user.id, form.message.data.strip(), "info")
            count += 1
        log_action("broadcast", f"{count} users")
        db.session.commit()
        flash(f"Notification sent to {count} active users.", "success")
        return redirect(url_for("admin.notifications"))
    recent = (
        Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    )
    return render_template("admin/notifications.html", form=form, recent=recent)


# -------------------- Activity log --------------------
@admin_bp.route("/logs")
def logs():
    entries = (
        ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(200).all()
    )
    return render_template("admin/logs.html", entries=entries)
