import csv
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from flask import current_app

from backend.database import get_db


def mark_attendance(student_id: int) -> dict[str, Any]:
    connection = get_db()
    today = date.today().isoformat()

    existing_record = connection.execute(
        """
        SELECT attendance.id, attendance.attendance_date, attendance.attendance_time,
               students.name, students.roll_number, students.department
        FROM attendance
        INNER JOIN students ON students.id = attendance.student_id
        WHERE attendance.student_id = ? AND attendance.attendance_date = ?
        """,
        (student_id, today),
    ).fetchone()

    # Returning early here prevents duplicate attendance for the same student on the same day.
    if existing_record:
        return {"status": "already_marked", "record": dict(existing_record)}

    cursor = connection.execute(
        """
        INSERT INTO attendance (student_id, attendance_date, attendance_time, created_at)
        VALUES (?, date('now', 'localtime'), time('now', 'localtime'), datetime('now', 'localtime'))
        """,
        (student_id,),
    )
    connection.commit()

    created_record = connection.execute(
        """
        SELECT attendance.id, attendance.attendance_date, attendance.attendance_time,
               students.name, students.roll_number, students.department
        FROM attendance
        INNER JOIN students ON students.id = attendance.student_id
        WHERE attendance.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()

    return {"status": "marked", "record": dict(created_record)}


def get_attendance_records(
    selected_date: str = "",
    search_term: str = "",
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[str] = []

    if selected_date:
        conditions.append("attendance.attendance_date = ?")
        params.append(selected_date)

    if search_term:
        conditions.append(
            "(students.name LIKE ? OR students.roll_number LIKE ? OR students.department LIKE ?)"
        )
        wildcard = f"%{search_term}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    rows = get_db().execute(
        f"""
        SELECT attendance.id, attendance.attendance_date, attendance.attendance_time,
               students.name, students.roll_number, students.department
        FROM attendance
        INNER JOIN students ON students.id = attendance.student_id
        {where_clause}
        ORDER BY attendance.attendance_date DESC, attendance.attendance_time DESC
        """,
        tuple(params),
    ).fetchall()

    return [dict(row) for row in rows]


def get_recent_attendance(limit: int = 8) -> list[dict[str, Any]]:
    rows = get_db().execute(
        """
        SELECT attendance.id, attendance.attendance_date, attendance.attendance_time,
               students.name, students.roll_number, students.department
        FROM attendance
        INNER JOIN students ON students.id = attendance.student_id
        ORDER BY attendance.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


def get_today_attendance_count() -> int:
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE attendance_date = date('now', 'localtime')
        """
    ).fetchone()
    return int(row["total"])


def export_attendance_to_csv(
    selected_date: str = "",
    search_term: str = "",
) -> tuple[str, str]:
    attendance_records = get_attendance_records(selected_date, search_term)
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    export_timestamp = datetime.now()
    export_date_label = export_timestamp.strftime("%Y-%m-%d")
    export_datetime_label = export_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    attendance_date_label = selected_date or "All Dates"
    search_label = search_term or "All Records"

    # Add export context so the CSV itself clearly shows when and for which date it was created.
    writer.writerow(["Export Generated On", export_datetime_label])
    writer.writerow(["Attendance Date Filter", attendance_date_label])
    writer.writerow(["Search Filter", search_label])
    writer.writerow([])
    writer.writerow(["Name", "Roll Number", "Department", "Date", "Time"])
    for record in attendance_records:
        writer.writerow(
            [
                record["name"],
                record["roll_number"],
                record["department"],
                record["attendance_date"],
                record["attendance_time"],
            ]
        )

    export_dir = Path(current_app.config["EXPORT_DIR"])
    export_dir.mkdir(parents=True, exist_ok=True)
    filename_date = selected_date or export_date_label
    export_file = export_dir / f"attendance_export_{filename_date}.csv"
    export_file.write_text(csv_buffer.getvalue(), encoding="utf-8")
    return str(export_file), f"attendance_records_{filename_date}.csv"
