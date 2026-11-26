"""Authentication & profile routes."""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegisterForm, LoginForm, ProfileForm
from services.common import log_action, notify
from services import recommendation_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "danger")
        elif User.query.filter_by(email=form.email.data.lower()).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.lower().strip(),
                full_name=form.full_name.data or None,
                role="user",
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            notify(user.id, "Welcome! Complete your profile to get scheme "
                            "recommendations.", "info")
            log_action("register", f"user {user.username}", user_id=user.id)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        ident = form.identifier.data.strip()
        user = (
            User.query.filter(
                (User.email == ident.lower()) | (User.username == ident)
            ).first()
        )
        if user and user.check_password(form.password.data):
            if not user.account_active:
                flash("This account has been disabled. Contact an administrator.",
                      "danger")
                return render_template("login.html", form=form)
            login_user(user, remember=form.remember.data)
            log_action("login", f"user {user.username}", user_id=user.id)
            db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials. Please try again.", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_action("logout", f"user {current_user.username}")
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        log_action("profile_update", "profile saved")
        db.session.commit()
        # recompute recommendations now that the profile changed
        count = recommendation_service.refresh_for_user(current_user)
        flash(f"Profile saved. {count} schemes re-evaluated.", "success")
        return redirect(url_for("auth.profile"))
    from services.rules_engine import profile_completion
    completion = profile_completion(current_user.profile_dict())
    return render_template("profile.html", form=form, completion=completion)
