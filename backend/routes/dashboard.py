import sqlite3
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from backend.services.attendance_service import (
    export_attendance_to_csv,
    get_attendance_records,
    get_recent_attendance,
    get_today_attendance_count,
)
from backend.services.face_service import get_face_service
from backend.services.student_service import create_student, get_student_count, list_students
from backend.utils.time_utils import local_now
from backend.utils.decorators import login_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    if session.get("admin_id"):
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    selected_date = request.args.get("date", "").strip()
    search_term = request.args.get("search", "").strip()
    face_service = get_face_service()

    return render_template(
        "dashboard.html",
        selected_date=selected_date,
        search_term=search_term,
        student_count=get_student_count(),
        today_count=get_today_attendance_count(),
        known_face_count=face_service.get_known_face_count(),
        attendance_records=get_attendance_records(selected_date, search_term),
        recent_attendance=get_recent_attendance(),
        recent_students=list_students(limit=6),
        today_label=local_now().strftime("%d %b %Y"),
    )


@dashboard_bp.route("/students/register")
@login_required
def register_student_page():
    return render_template("register_student.html")


@dashboard_bp.route("/students", methods=["POST"])
@login_required
def register_student():
    payload = request.get_json(silent=True) or {}

    name = payload.get("name", "").strip()
    roll_number = payload.get("roll_number", "").strip().upper()
    department = payload.get("department", "").strip()
    face_image = payload.get("face_image", "")

    if not all([name, roll_number, department, face_image]):
        return jsonify({"error": "Name, roll number, department, and face capture are required."}), 400

    face_service = get_face_service()
    saved_image_path = None

    try:
        image_bgr = face_service.decode_base64_image(face_image)
        face_encoding = face_service.extract_single_face_encoding(image_bgr)
        saved_image_path = face_service.save_face_image(image_bgr, roll_number)

        student = create_student(
            name=name,
            roll_number=roll_number,
            department=department,
            face_encoding=face_service.encoding_to_json(face_encoding),
            face_image_path=saved_image_path,
        )
        face_service.load_known_faces()

        current_app.logger.info("Registered student %s (%s).", student["name"], student["roll_number"])
        return jsonify(
            {
                "message": "Student registered successfully.",
                "redirect_url": url_for("dashboard.dashboard"),
                "student": {
                    "name": student["name"],
                    "roll_number": student["roll_number"],
                    "department": student["department"],
                },
            }
        )
    except sqlite3.IntegrityError:
        if saved_image_path:
            image_path = face_service.resolve_storage_path(saved_image_path)
            if image_path.exists():
                image_path.unlink()
        return jsonify({"error": "That roll number is already registered."}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        if saved_image_path:
            image_path = face_service.resolve_storage_path(saved_image_path)
            if image_path.exists():
                image_path.unlink()
        current_app.logger.exception("Student registration failed.")
        return jsonify({"error": "Registration failed due to an unexpected server error."}), 500


@dashboard_bp.route("/students/retrain", methods=["POST"])
@login_required
def retrain_faces():
    try:
        result = get_face_service().retrain_all_faces()
        if result["skipped"]:
            flash(
                f"Retrained {result['retrained']} face(s). Skipped {len(result['skipped'])} record(s). Check logs if needed.",
                "warning",
            )
        else:
            flash(f"Retrained {result['retrained']} face(s) successfully.", "success")
    except Exception:
        current_app.logger.exception("Face retraining failed.")
        flash("Face retraining failed. Please review the log file.", "danger")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/attendance/export")
@login_required
def export_attendance():
    selected_date = request.args.get("date", "").strip()
    search_term = request.args.get("search", "").strip()

    try:
        export_file, download_name = export_attendance_to_csv(selected_date, search_term)
        current_app.logger.info("Attendance export created at %s.", export_file)
        return send_file(
            export_file,
            as_attachment=True,
            download_name=download_name,
            mimetype="text/csv",
        )
    except Exception:
        current_app.logger.exception("Attendance export failed.")
        flash("Attendance export failed. Please try again.", "danger")
        return redirect(url_for("dashboard.dashboard"))
