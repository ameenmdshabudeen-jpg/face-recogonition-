import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    BASE_DIR = PROJECT_ROOT
    DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(BASE_DIR / "data"))).resolve()
    LOG_DIR = Path(os.getenv("APP_LOG_DIR", str(DATA_DIR / "logs"))).resolve()
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    PROJECT_ROOT = str(BASE_DIR)
    DATABASE_PATH = str(DATA_DIR / "attendance.db")
    SCHEMA_PATH = str(BASE_DIR / "database" / "schema.sql")
    FACE_IMAGE_DIR = str(DATA_DIR / "known_faces")
    EXPORT_DIR = str(DATA_DIR / "exports")
    LOG_FILE = str(LOG_DIR / "attendance.log")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
    FACE_MATCH_TOLERANCE = float(os.getenv("FACE_MATCH_TOLERANCE", "0.48"))
    FRAME_RESIZE_SCALE = float(os.getenv("FRAME_RESIZE_SCALE", "0.25"))
    RECOGNITION_MODEL = os.getenv("RECOGNITION_MODEL", "hog")
