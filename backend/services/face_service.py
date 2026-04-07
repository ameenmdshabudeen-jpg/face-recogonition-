import base64
import binascii
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import face_recognition
import numpy as np
from flask import current_app
from werkzeug.utils import secure_filename

from backend.database import get_db


logger = logging.getLogger(__name__)


class FaceService:
    def __init__(self) -> None:
        self.known_faces: list[dict[str, Any]] = []

    def decode_base64_image(self, image_data: str) -> np.ndarray:
        if not image_data:
            raise ValueError("No image was received from the browser.")

        encoded_image = image_data.split(",", 1)[1] if "," in image_data else image_data

        try:
            image_bytes = base64.b64decode(encoded_image)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("The captured image payload is invalid.") from exc

        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image_bgr is None:
            raise ValueError("The captured image could not be decoded.")

        return image_bgr

    def extract_single_face_encoding(self, image_bgr: np.ndarray) -> np.ndarray:
        rgb_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(
            rgb_image,
            model=current_app.config["RECOGNITION_MODEL"],
        )

        if not locations:
            raise ValueError("No face detected. Please keep the face centered and try again.")

        if len(locations) > 1:
            raise ValueError(
                "Multiple faces detected. Registration requires exactly one face in the frame."
            )

        encodings = face_recognition.face_encodings(rgb_image, locations, model="small")
        if not encodings:
            raise ValueError("Face detected, but encoding failed. Please capture a sharper image.")

        return encodings[0]

    def encoding_to_json(self, face_encoding: np.ndarray) -> str:
        return json.dumps(face_encoding.tolist())

    def save_face_image(self, image_bgr: np.ndarray, roll_number: str) -> str:
        output_dir = Path(current_app.config["FACE_IMAGE_DIR"])
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_roll_number = secure_filename(roll_number)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"{safe_roll_number}_{timestamp}.jpg"

        if not cv2.imwrite(str(file_path), image_bgr):
            raise ValueError("Unable to save the captured face image to disk.")

        data_dir = Path(current_app.config["DATA_DIR"])
        return file_path.relative_to(data_dir).as_posix()

    def load_known_faces(self) -> None:
        rows = get_db().execute(
            """
            SELECT id, name, roll_number, department, face_encoding
            FROM students
            ORDER BY id ASC
            """
        ).fetchall()

        known_faces: list[dict[str, Any]] = []
        for row in rows:
            try:
                known_faces.append(
                    {
                        "student_id": row["id"],
                        "name": row["name"],
                        "roll_number": row["roll_number"],
                        "department": row["department"],
                        "encoding": np.array(json.loads(row["face_encoding"]), dtype=np.float64),
                    }
                )
            except json.JSONDecodeError:
                logger.warning("Skipping student %s because the face encoding is invalid.", row["id"])

        self.known_faces = known_faces
        logger.info("Loaded %s face encoding(s) into memory.", len(self.known_faces))

    def recognize_faces(self, image_bgr: np.ndarray) -> list[dict[str, Any]]:
        resize_scale = current_app.config["FRAME_RESIZE_SCALE"]
        tolerance = current_app.config["FACE_MATCH_TOLERANCE"]

        # Downscaling the frame keeps real-time recognition responsive on normal lab machines.
        small_frame = cv2.resize(image_bgr, (0, 0), fx=resize_scale, fy=resize_scale)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(
            rgb_small_frame,
            model=current_app.config["RECOGNITION_MODEL"],
        )
        if not locations:
            return []

        encodings = face_recognition.face_encodings(rgb_small_frame, locations, model="small")
        results: list[dict[str, Any]] = []
        known_encodings = [face["encoding"] for face in self.known_faces]

        for location, encoding in zip(locations, encodings):
            matched_face = None
            best_distance = None

            if known_encodings:
                # Distance-based matching is faster than reloading or recomputing stored encodings per request.
                distances = face_recognition.face_distance(known_encodings, encoding)
                best_index = int(np.argmin(distances))
                best_distance = float(distances[best_index])
                matches = face_recognition.compare_faces(
                    known_encodings,
                    encoding,
                    tolerance=tolerance,
                )
                if matches[best_index] and best_distance <= tolerance:
                    matched_face = self.known_faces[best_index]

            top, right, bottom, left = self._scale_location(location, resize_scale)
            results.append(
                {
                    "student_id": matched_face["student_id"] if matched_face else None,
                    "name": matched_face["name"] if matched_face else "Unknown",
                    "roll_number": matched_face["roll_number"] if matched_face else None,
                    "department": matched_face["department"] if matched_face else None,
                    "confidence": self._confidence_percentage(best_distance),
                    "location": {
                        "top": top,
                        "right": right,
                        "bottom": bottom,
                        "left": left,
                    },
                }
            )

        return results

    def retrain_all_faces(self) -> dict[str, Any]:
        connection = get_db()
        students = connection.execute(
            """
            SELECT id, roll_number, face_image_path
            FROM students
            ORDER BY id ASC
            """
        ).fetchall()

        retrained = 0
        skipped: list[str] = []

        for student in students:
            image_path = self.resolve_storage_path(student["face_image_path"])
            image_bgr = cv2.imread(str(image_path))

            if image_bgr is None:
                skipped.append(f"{student['roll_number']}: saved image not found or unreadable.")
                continue

            try:
                encoding = self.extract_single_face_encoding(image_bgr)
            except ValueError as exc:
                skipped.append(f"{student['roll_number']}: {exc}")
                continue

            connection.execute(
                """
                UPDATE students
                SET face_encoding = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (self.encoding_to_json(encoding), student["id"]),
            )
            retrained += 1

        connection.commit()
        self.load_known_faces()

        return {
            "total": len(students),
            "retrained": retrained,
            "skipped": skipped,
        }

    def get_known_face_count(self) -> int:
        return len(self.known_faces)

    def resolve_storage_path(self, stored_path: str) -> Path:
        candidate = Path(stored_path)

        if candidate.is_absolute():
            return candidate

        data_dir = Path(current_app.config["DATA_DIR"])
        data_path = data_dir / candidate
        if data_path.exists():
            return data_path

        # Backward compatibility for records created before external data directories were introduced.
        project_root = Path(current_app.config["PROJECT_ROOT"])
        return project_root / candidate

    def _scale_location(
        self,
        location: tuple[int, int, int, int],
        resize_scale: float,
    ) -> tuple[int, int, int, int]:
        top, right, bottom, left = location
        return (
            int(top / resize_scale),
            int(right / resize_scale),
            int(bottom / resize_scale),
            int(left / resize_scale),
        )

    def _confidence_percentage(self, distance: float | None) -> float:
        if distance is None:
            return 0.0
        return round(max(0.0, (1.0 - distance) * 100), 2)


face_service = FaceService()


def get_face_service() -> FaceService:
    return face_service
