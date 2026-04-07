FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_DATA_DIR=/var/data/face-attendance
ENV APP_LOG_DIR=/var/data/face-attendance/logs

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.deploy.txt ./

RUN pip install --upgrade pip wheel "setuptools==70.3.0" && \
    pip install --no-cache-dir -r requirements.deploy.txt && \
    pip install --no-cache-dir \
        dlib-bin==20.0.0 \
        face-recognition==1.3.0 \
        --no-deps && \
    python -c "import pkg_resources; import PIL; import dlib; import face_recognition_models; import face_recognition; print('deploy-deps-ok')"

COPY . .

RUN mkdir -p /var/data/face-attendance/known_faces \
    /var/data/face-attendance/exports \
    /var/data/face-attendance/logs && \
    python -c "from backend import create_app; app = create_app(); print('app-bootstrap-ok')"

EXPOSE 5000

CMD ["python", "app.py"]
