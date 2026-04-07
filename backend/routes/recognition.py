from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

from backend.services.attendance_service import mark_attendance
from backend.services.face_service import get_face_service
from backend.utils.decorators import login_required


recognition_bp = Blueprint("recognition", __name__)


@recognition_bp.route("/recognize")
@login_required
def recognize_page():
    return render_template("recognize.html")


@recognition_bp.route("/api/recognize", methods=["POST"])
@login_required
def recognize_faces():
    payload = request.get_json(silent=True) or {}
    frame_data = payload.get("frame", "")

    if not frame_data:
        return jsonify({"error": "No frame was received for recognition."}), 400

    try:
        face_service = get_face_service()
        frame_bgr = face_service.decode_base64_image(frame_data)
        results = face_service.recognize_faces(frame_bgr)
        attendance_events = []

        for result in results:
            if not result["student_id"]:
                result["attendance_status"] = "unknown"
                continue

            # Attendance writes are safe to call on every frame because duplicates are blocked in the service layer.
            attendance_result = mark_attendance(result["student_id"])
            result["attendance_status"] = attendance_result["status"]

            if attendance_result["status"] == "marked":
                attendance_events.append(attendance_result["record"])

        return jsonify(
            {
                "processed_at": datetime.now().strftime("%H:%M:%S"),
                "results": results,
                "attendance_events": attendance_events,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Recognition request failed.")
        return jsonify({"error": "Face recognition failed due to an unexpected server error."}), 500
