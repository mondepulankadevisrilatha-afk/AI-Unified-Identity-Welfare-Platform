"""Document vault: upload, list, view, preview/download, replace, delete."""
import os

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    send_file, abort, current_app,
)
from flask_login import login_required, current_user

from extensions import db
from models import Document
from forms import DocumentUploadForm, DocumentReplaceForm
from services.common import (
    owned_or_404, random_stored_name, safe_upload_path, detect_mime,
    allowed_file, log_action, notify,
)

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")


def _save_upload(file_storage):
    """Validate and store an uploaded file. Returns (stored_name, mime)."""
    if not allowed_file(file_storage.filename):
        raise ValueError("File type not allowed.")
    mime = detect_mime(file_storage.stream)
    if mime is None:
        raise ValueError("File content does not match an allowed type "
                         "(PDF, PNG, JPG).")
    stored = random_stored_name(file_storage.filename)
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    path = safe_upload_path(stored)
    file_storage.save(path)
    return stored, mime


@documents_bp.route("/")
@login_required
def list_documents():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Document.query.filter_by(user_id=current_user.id)
    if q:
        query = query.filter(Document.document_name.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    docs = query.order_by(Document.uploaded_at.desc()).all()
    return render_template(
        "documents/list.html",
        docs=docs,
        q=q,
        category=category,
        categories=current_app.config["DOCUMENT_CATEGORIES"],
    )


@documents_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = DocumentUploadForm()
    if form.validate_on_submit():
        try:
            stored, mime = _save_upload(form.file.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("documents/upload.html", form=form)
        doc = Document(
            user_id=current_user.id,
            document_name=form.document_name.data.strip(),
            category=form.category.data,
            file_path=stored,
            original_name=form.file.data.filename,
            mime_type=mime,
            status="Uploaded",
        )
        db.session.add(doc)
        db.session.flush()
        notify(current_user.id, f"Document '{doc.document_name}' uploaded.", "success")
        log_action("document_upload", doc.document_name)
        db.session.commit()
        flash("Document uploaded. You can now scan it to extract details.", "success")
        return redirect(url_for("documents.detail", doc_id=doc.id))
    return render_template("documents/upload.html", form=form)


@documents_bp.route("/<int:doc_id>")
@login_required
def detail(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    return render_template("documents/detail.html", doc=doc)


@documents_bp.route("/<int:doc_id>/file")
@login_required
def file(doc_id):
    """Stream the stored file inline (preview) or as attachment (download)."""
    doc = owned_or_404(Document.query.get(doc_id))
    path = safe_upload_path(doc.file_path)
    if not os.path.exists(path):
        abort(404)
    as_attachment = request.args.get("download") == "1"
    return send_file(
        path,
        mimetype=doc.mime_type or "application/octet-stream",
        as_attachment=as_attachment,
        download_name=doc.original_name or doc.document_name,
    )


@documents_bp.route("/<int:doc_id>/replace", methods=["GET", "POST"])
@login_required
def replace(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    form = DocumentReplaceForm()
    if form.validate_on_submit():
        try:
            stored, mime = _save_upload(form.file.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("documents/replace.html", form=form, doc=doc)
        # remove the old file
        old = safe_upload_path(doc.file_path)
        if os.path.exists(old):
            os.remove(old)
        doc.file_path = stored
        doc.original_name = form.file.data.filename
        doc.mime_type = mime
        doc.status = "Uploaded"
        doc.is_confirmed = False
        doc.extracted_name = doc.extracted_dob = None
        doc.extracted_address = doc.extracted_number = None
        log_action("document_replace", doc.document_name)
        db.session.commit()
        flash("File replaced. Previous extracted data was cleared.", "success")
        return redirect(url_for("documents.detail", doc_id=doc.id))
    return render_template("documents/replace.html", form=form, doc=doc)


@documents_bp.route("/<int:doc_id>/status", methods=["POST"])
@login_required
def update_status(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    new_status = request.form.get("status", "")
    if new_status in ("Uploaded", "Verified", "Expired"):
        doc.status = new_status
        log_action("document_status", f"{doc.document_name} -> {new_status}")
        db.session.commit()
        flash("Status updated.", "success")
    else:
        flash("Invalid status.", "danger")
    return redirect(url_for("documents.detail", doc_id=doc.id))


@documents_bp.route("/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete(doc_id):
    doc = owned_or_404(Document.query.get(doc_id))
    path = safe_upload_path(doc.file_path)
    if os.path.exists(path):
        os.remove(path)
    name = doc.document_name
    db.session.delete(doc)
    log_action("document_delete", name)
    db.session.commit()
    flash(f"Document '{name}' deleted.", "info")
    return redirect(url_for("documents.list_documents"))
