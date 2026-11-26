"""Document scanner (OCR).

Flow: pick a document -> run OCR -> review the extracted & masked fields ->
confirm. Only confirmed data is written back to the Document row, so the
user always stays in control of what is stored.
"""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session,
)
from flask_login import login_required, current_user

from extensions import db
from models import Document
from services.common import owned_or_404, safe_upload_path, log_action
from services import ocr_service

scanner_bp = Blueprint("scanner", __name__, url_prefix="/scanner")


@scanner_bp.route("/")
@login_required
def list_scanner():
    docs = (
        Document.query.filter_by(user_id=current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return render_template("scanner/list.html", docs=docs)


@scanner_bp.route("/<int:doc_id>/run", methods=["POST"])
@login_required
def run_ocr_route(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    path = safe_upload_path(doc.file_path)
    try:
        text, conf = ocr_service.run_ocr(path)
    except RuntimeError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("scanner.list_scanner"))

    fields = ocr_service.parse_fields(text)
    # Stash the proposed values in the session for the review step; nothing
    # is written to the database until the user confirms.
    session[f"ocr_{doc.id}"] = {
        "extracted_name": fields["extracted_name"],
        "extracted_dob": fields["extracted_dob"],
        "extracted_address": fields["extracted_address"],
        "extracted_number": fields["extracted_number"],
        "confidence": conf,
    }
    log_action("ocr_run", doc.document_name)
    return redirect(url_for("scanner.review", doc_id=doc.id))


@scanner_bp.route("/<int:doc_id>/review")
@login_required
def review(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    proposed = session.get(f"ocr_{doc.id}")
    if not proposed:
        flash("Please run the scan first.", "info")
        return redirect(url_for("scanner.list_scanner"))
    return render_template("scanner/review.html", doc=doc, proposed=proposed)


@scanner_bp.route("/<int:doc_id>/confirm", methods=["POST"])
@login_required
def confirm(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    # The review form lets the user edit the values before confirming.
    doc.extracted_name = request.form.get("extracted_name") or None
    doc.extracted_dob = request.form.get("extracted_dob") or None
    doc.extracted_address = request.form.get("extracted_address") or None
    doc.extracted_number = request.form.get("extracted_number") or None
    doc.is_confirmed = True
    doc.status = "Verified"
    session.pop(f"ocr_{doc.id}", None)
    log_action("ocr_confirm", doc.document_name)
    db.session.commit()
    flash("Extracted details confirmed and saved.", "success")
    return redirect(url_for("documents.detail", doc_id=doc.id))
