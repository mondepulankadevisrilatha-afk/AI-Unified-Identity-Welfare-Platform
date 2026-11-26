"""Application factory.

Creates the Flask app, wires up the extensions, security headers, error
pages, a notification-badge context processor, and registers every
blueprint. Run with:  python app.py   (or  flask --app app run).
"""
import os

from flask import Flask, render_template
from flask_login import current_user

from config import Config
from extensions import db, login_manager, csrf


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # Make sure the instance and upload folders exist
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from models import User, Notification

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ---- Security headers on every response ----
    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com"
        )
        return resp

    # ---- Notification badge available to all templates ----
    @app.context_processor
    def inject_badge():
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return {"unread_notifications": unread}

    # ---- Error pages ----
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403,
                               message="You do not have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404,
                               message="The page you requested was not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413,
                               message="That file is larger than the 5 MB limit."), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500,
                               message="Something went wrong on our side."), 500

    # ---- Blueprints ----
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.documents import documents_bp
    from routes.scanner import scanner_bp
    from routes.schemes import schemes_bp
    from routes.recommendations import recommendations_bp
    from routes.eligibility import eligibility_bp
    from routes.applications import applications_bp
    from routes.admin import admin_bp

    for bp in (main_bp, auth_bp, documents_bp, scanner_bp, schemes_bp,
               recommendations_bp, eligibility_bp, applications_bp, admin_bp):
        app.register_blueprint(bp)

    # ---- CLI helper: flask --app app init-db ----
    @app.cli.command("init-db")
    def init_db():
        """Create all tables."""
        db.create_all()
        print("Database tables created.")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
