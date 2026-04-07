from flask import Flask, render_template

from backend.config import Config, PROJECT_ROOT
from backend.database import init_app as init_database
from backend.logging_utils import configure_logging
from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.recognition import recognition_bp
from backend.services.face_service import get_face_service


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
        static_folder=str(PROJECT_ROOT / "frontend" / "static"),
    )
    app.config.from_object(Config)

    configure_logging(app)
    init_database(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(recognition_bp)

    with app.app_context():
        get_face_service().load_known_faces()

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                title="Page not found",
                message="The page you requested does not exist.",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(_error):
        return (
            render_template(
                "error.html",
                title="Server error",
                message="Something went wrong while processing your request. Check the log file for details.",
            ),
            500,
        )

    return app
