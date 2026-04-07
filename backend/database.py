import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE_PATH"])
        database_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection

    return g.db


def close_db(_error=None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    database_path = Path(current_app.config["DATABASE_PATH"])
    schema_path = Path(current_app.config["SCHEMA_PATH"])

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        # The schema file keeps table creation in one predictable place.
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_path.read_text(encoding="utf-8"))


def seed_default_admin() -> None:
    connection = get_db()
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    existing_admin = connection.execute(
        "SELECT id FROM admins WHERE username = ?",
        (username,),
    ).fetchone()

    if existing_admin:
        return

    connection.execute(
        """
        INSERT INTO admins (username, password_hash, created_at, updated_at)
        VALUES (?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
        """,
        (
            username,
            generate_password_hash(current_app.config["DEFAULT_ADMIN_PASSWORD"]),
        ),
    )
    connection.commit()


def init_app(app) -> None:
    Path(app.config["FACE_IMAGE_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["LOG_FILE"]).parent.mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
        seed_default_admin()
