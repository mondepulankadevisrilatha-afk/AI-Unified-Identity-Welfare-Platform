"""Application tracker: create/edit applications, manage a checklist,
update status, set reminders, print a summary.
"""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
)
from flask_login import login_required, current_user

from extensions import db
from models import Scheme, Application, ApplicationChecklist
from forms import ApplicationForm, ChecklistItemForm
from config import Config
from services.common import owned_or_404, log_action, notify

applications_bp = Blueprint("applications", __name__, url_prefix="/applications")


def _scheme_choices():
    schemes = Scheme.query.filter_by(is_active=True).order_by(Scheme.scheme_name).all()
    return [(s.id, s.scheme_name) for s in schemes]


@applications_bp.route("/")
@login_required
def list_applications():
    apps = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.updated_at.desc())
        .all()
    )
    due = [a for a in apps if a.is_reminder_due]
    return render_template("applications/list.html", apps=apps, due=due,
                           statuses=Config.APPLICATION_STATUSES)


@applications_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = ApplicationForm()
    form.scheme_id.choices = _scheme_choices()
    # allow pre-selecting a scheme via ?scheme_id=
    preset = request.args.get("scheme_id", type=int)
    if preset and not form.is_submitted():
        form.scheme_id.data = preset

    if form.validate_on_submit():
        app_row = Application(
            user_id=current_user.id,
            scheme_id=form.scheme_id.data,
            status=form.status.data,
            reference_number=form.reference_number.data or None,
            submitted_on=form.submitted_on.data,
            reminder_date=form.reminder_date.data,
            notes=form.notes.data or None,
        )
        db.session.add(app_row)
        db.session.flush()
        # seed the checklist from the scheme's required documents
        scheme = Scheme.query.get(form.scheme_id.data)
        if scheme:
            for item in scheme.required_documents_list():
                db.session.add(ApplicationChecklist(
                    application_id=app_row.id, item=item))
        notify(current_user.id,
               f"Application started for "
               f"{scheme.scheme_name if scheme else 'a scheme'}.", "info")
        log_action("application_create", str(app_row.id))
        db.session.commit()
        flash("Application created.", "success")
        return redirect(url_for("applications.detail", app_id=app_row.id))
    return render_template("applications/form.html", form=form, mode="create")


@applications_bp.route("/<int:app_id>")
@login_required
def detail(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    checklist_form = ChecklistItemForm()
    done = sum(1 for c in app_row.checklist if c.is_done)
    total = len(app_row.checklist)
    progress = int(round((done / total) * 100)) if total else 0
    return render_template("applications/detail.html", app=app_row,
                           checklist_form=checklist_form, progress=progress)


@applications_bp.route("/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
def edit(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    form = ApplicationForm(obj=app_row)
    form.scheme_id.choices = _scheme_choices()
    if form.validate_on_submit():
        form.populate_obj(app_row)
        log_action("application_edit", str(app_row.id))
        db.session.commit()
        flash("Application updated.", "success")
        return redirect(url_for("applications.detail", app_id=app_row.id))
    return render_template("applications/form.html", form=form, mode="edit", app=app_row)


@applications_bp.route("/<int:app_id>/status", methods=["POST"])
@login_required
def update_status(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    new_status = request.form.get("status", "")
    if new_status in Config.APPLICATION_STATUSES:
        app_row.status = new_status
        notify(current_user.id,
               f"Application status changed to '{new_status}'.", "info")
        log_action("application_status", f"{app_row.id} -> {new_status}")
        db.session.commit()
        flash("Status updated.", "success")
    else:
        flash("Invalid status.", "danger")
    return redirect(url_for("applications.detail", app_id=app_row.id))


@applications_bp.route("/<int:app_id>/checklist/add", methods=["POST"])
@login_required
def add_checklist(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    form = ChecklistItemForm()
    if form.validate_on_submit():
        db.session.add(ApplicationChecklist(
            application_id=app_row.id, item=form.item.data.strip()))
        db.session.commit()
        flash("Checklist item added.", "success")
    return redirect(url_for("applications.detail", app_id=app_row.id))


@applications_bp.route("/checklist/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_checklist(item_id):
    item = ApplicationChecklist.query.get_or_404(item_id)
    owned_or_404(item.application)   # ownership via parent application
    item.is_done = not item.is_done
    db.session.commit()
    return redirect(url_for("applications.detail", app_id=item.application_id))


@applications_bp.route("/checklist/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_checklist(item_id):
    item = ApplicationChecklist.query.get_or_404(item_id)
    owned_or_404(item.application)
    app_id = item.application_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("applications.detail", app_id=app_id))


@applications_bp.route("/<int:app_id>/delete", methods=["POST"])
@login_required
def delete(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    db.session.delete(app_row)
    log_action("application_delete", str(app_id))
    db.session.commit()
    flash("Application deleted.", "info")
    return redirect(url_for("applications.list_applications"))


@applications_bp.route("/<int:app_id>/print")
@login_required
def print_view(app_id):
    app_row = owned_or_404(Application.query.get(app_id))
    return render_template("applications/print.html", app=app_row)
