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

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.deploy.txt && \
    pip install --no-cache-dir \
        dlib-bin==20.0.0 \
        face-recognition-models==0.3.0 \
        face-recognition==1.3.0 \
        --no-deps

COPY . .

RUN mkdir -p /var/data/face-attendance/known_faces \
    /var/data/face-attendance/exports \
    /var/data/face-attendance/logs

EXPOSE 5000

CMD ["python", "app.py"]
