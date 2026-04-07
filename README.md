# Face Recognition Attendance System

A production-style college attendance system built with Flask, SQLite, OpenCV, and the `face_recognition` library. The browser handles webcam capture, while the backend handles face encoding, real-time recognition, duplicate attendance prevention, logging, and CSV export.

## Features

- Admin login with session-based authentication
- Student registration with webcam face capture
- Face encoding storage in SQLite
- Real-time face recognition using webcam frames from the browser
- Attendance auto-marking for recognized faces
- Duplicate attendance prevention for the same student on the same day
- Multi-face recognition support in a single frame
- Dashboard for attendance search, filtering, and CSV export
- Retraining module to rebuild stored encodings from saved face images
- Logging and friendly error handling for camera or face-detection issues

## Project Structure

```text
apps/face-attendance
|-- app.py
|-- README.md
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- backend
|   |-- __init__.py
|   |-- config.py
|   |-- database.py
|   |-- logging_utils.py
|   |-- routes
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- dashboard.py
|   |   `-- recognition.py
|   |-- services
|   |   |-- __init__.py
|   |   |-- attendance_service.py
|   |   |-- face_service.py
|   |   `-- student_service.py
|   `-- utils
|       |-- __init__.py
|       `-- decorators.py
|-- frontend
|   |-- static
|   |   |-- css
|   |   |   `-- styles.css
|   |   `-- js
|   |       |-- dashboard.js
|   |       |-- recognize.js
|   |       `-- register.js
|   `-- templates
|       |-- base.html
|       |-- dashboard.html
|       |-- error.html
|       |-- login.html
|       |-- recognize.html
|       `-- register_student.html
|-- database
|   `-- schema.sql
|-- data
|   |-- attendance.db            # created automatically on first run
|   |-- exports
|   |-- known_faces
|   |-- exports/.gitkeep
|   `-- known_faces/.gitkeep
`-- logs
    |-- attendance.log           # created automatically on first run
    `-- .gitkeep
```

## Database Schema

The database schema lives in [database/schema.sql](./database/schema.sql) and creates:

- `admins`: admin login credentials
- `students`: student profile, roll number, department, saved image path, and face encoding
- `attendance`: one attendance record per student per day using a unique constraint on `(student_id, attendance_date)`

## Setup Instructions

### Fastest Windows setup

If you are on Windows PowerShell, the project now includes helper scripts:

```powershell
cd apps/face-attendance
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\run_localhost.ps1
```

Then open:

```text
http://127.0.0.1:5000/login
```

### 1. Move into the project directory

```bash
cd apps/face-attendance
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install system prerequisites

The `face_recognition` package depends on `dlib`, so make sure your machine has:

- Python 3.10 or 3.11 recommended
- CMake installed
- A C++ build toolchain

On Windows, the easiest path is:

- Install Visual Studio Build Tools with the C++ workload
- Install [CMake](https://cmake.org/download/)

### 4. Install Python packages

```bash
pip install -r requirements.txt
```

On some Windows machines, `face_recognition` tries to build `dlib` from source. If that happens, use the included `setup_windows.ps1` script instead because it installs a prebuilt Windows `dlib` package path.

### 5. Create the environment file

Copy `.env.example` to `.env`.

Example:

```bash
copy .env.example .env
```

Update values if needed:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `FACE_MATCH_TOLERANCE`
- `FRAME_RESIZE_SCALE`

### 6. Start the application

Development mode:

```bash
python app.py
```

Production-style mode with Waitress:

```bash
waitress-serve --listen=0.0.0.0:5000 app:app
```

When `FLASK_DEBUG=false`, running `python app.py` already uses Waitress automatically.

### 7. Open the dashboard

Visit:

```text
http://127.0.0.1:5000/login
```

Default seeded credentials:

- Username: `admin`
- Password: `Admin@123`

If you changed `ADMIN_USERNAME` or `ADMIN_PASSWORD` in `.env` before the first run, the app will seed those credentials instead.

## How the Workflow Operates

### Student registration

1. Admin signs in.
2. Admin opens the Register Student page.
3. Browser captures one webcam frame.
4. Backend validates that exactly one face exists.
5. Backend stores:
   - student details
   - saved face image path
   - encoded face vector in SQLite
6. In-memory face cache is refreshed.

### Live recognition

1. Admin opens the Live Recognition page.
2. Browser sends frames to `/api/recognize` on a timer.
3. Backend downsizes the frame for better speed.
4. All faces in the frame are detected and compared with cached encodings.
5. Recognized students are matched and attendance is marked.
6. Unknown faces are labeled as `Unknown`.
7. Duplicate attendance on the same day is blocked by both:
   - application logic
   - database unique constraint

## Recognition Tuning

The app exposes two helpful settings in `.env`:

- `FACE_MATCH_TOLERANCE=0.48`
  - Lower values make matching stricter.
  - Higher values make matching looser.
- `FRAME_RESIZE_SCALE=0.25`
  - Lower values improve speed.
  - Higher values preserve more detail.

Good defaults for a college lab machine are already included.

## Export and Logs

- CSV exports are saved under `data/exports/`
- Application logs are written to `logs/attendance.log`

## Beginner Notes

- SQLite is used by default because it is simple to set up and good for a single-machine deployment.
- For larger campuses or multi-device deployments, you can replace the storage layer with MySQL or PostgreSQL later.
- If the camera page says access is blocked, allow webcam permission in the browser and refresh the page.
- If registration fails with `No face detected`, improve lighting and keep only one person in the frame.
