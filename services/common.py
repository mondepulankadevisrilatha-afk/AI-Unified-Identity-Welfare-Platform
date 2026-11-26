"""Cross-cutting helpers: file validation, safe storage names, ownership
checks, admin guard, notifications and activity logging.
"""
import os
import uuid
import functools

from flask import abort, request, current_app
from flask_login import current_user

from extensions import db
from models import Notification, ActivityLog


# --------------------------------------------------------------------------
#  File validation (by content signature, not just extension)
# --------------------------------------------------------------------------
_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


def detect_mime(stream):
    """Read the first bytes of a file stream and return a mime type or None.

    Resets the stream position afterwards so the caller can still save it.
    """
    pos = stream.tell()
    head = stream.read(8)
    stream.seek(pos)
    for sig, mime in _SIGNATURES.items():
        if head.startswith(sig):
            return mime
    return None


def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def random_stored_name(original_name):
    """Return an unguessable storage filename, keeping the real extension."""
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
        # only keep a known-safe extension
        if ext.lstrip(".") not in current_app.config["ALLOWED_EXTENSIONS"]:
            ext = ""
    return uuid.uuid4().hex + ext


def safe_upload_path(stored_name):
    """Resolve a stored filename inside the upload folder, blocking traversal."""
    base = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    target = os.path.abspath(os.path.join(base, stored_name))
    if os.path.commonpath([base, target]) != base:
        abort(404)
    return target


# --------------------------------------------------------------------------
#  Authorisation helpers
# --------------------------------------------------------------------------
def owned_or_404(obj):
    """Abort 404 unless the object belongs to the current user (or user is admin)."""
    if obj is None:
        abort(404)
    if getattr(current_user, "is_admin", False):
        return obj
    if getattr(obj, "user_id", None) != current_user.id:
        abort(404)
    return obj


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


# --------------------------------------------------------------------------
#  Notifications & audit log
# --------------------------------------------------------------------------
def notify(user_id, message, category="info"):
    note = Notification(user_id=user_id, message=message, category=category)
    db.session.add(note)
    return note


def log_action(action, detail="", user_id=None):
    try:
        uid = user_id
        if uid is None and current_user.is_authenticated:
            uid = current_user.id
    except Exception:
        uid = None
    entry = ActivityLog(
        user_id=uid,
        action=action,
        detail=detail[:255] if detail else "",
        ip_address=(request.remote_addr if request else None),
    )
    db.session.add(entry)
    return entry
