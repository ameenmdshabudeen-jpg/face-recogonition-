from typing import Any

from backend.database import get_db
from backend.utils.time_utils import current_timestamp_string


def create_student(
    name: str,
    roll_number: str,
    department: str,
    face_encoding: str,
    face_image_path: str,
) -> dict[str, Any]:
    connection = get_db()
    current_timestamp = current_timestamp_string()
    cursor = connection.execute(
        """
        INSERT INTO students (
            name,
            roll_number,
            department,
            face_encoding,
            face_image_path,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            name,
            roll_number,
            department,
            face_encoding,
            face_image_path,
            current_timestamp,
            current_timestamp,
        ),
    )
    connection.commit()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(student)


def list_students(limit: int | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT id, name, roll_number, department, face_image_path, created_at
        FROM students
        ORDER BY created_at DESC
    """
    params: tuple[Any, ...] = ()

    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    rows = get_db().execute(query, params).fetchall()
    return [dict(row) for row in rows]


def list_students_with_encodings() -> list[dict[str, Any]]:
    rows = get_db().execute(
        """
        SELECT id, name, roll_number, department, face_encoding, face_image_path, updated_at
        FROM students
        ORDER BY id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_student_count() -> int:
    row = get_db().execute("SELECT COUNT(*) AS total FROM students").fetchone()
    return int(row["total"])


def update_student_encoding(student_id: int, face_encoding: str) -> None:
    connection = get_db()
    connection.execute(
        """
        UPDATE students
        SET face_encoding = ?, updated_at = ?
        WHERE id = ?
        """,
        (face_encoding, current_timestamp_string(), student_id),
    )
    connection.commit()
