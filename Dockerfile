FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_DATA_DIR=/var/data/face-attendance
ENV APP_LOG_DIR=/var/data/face-attendance/logs

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.deploy.txt ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.deploy.txt

COPY . .

RUN mkdir -p /var/data/face-attendance/known_faces \
    /var/data/face-attendance/exports \
    /var/data/face-attendance/logs

EXPOSE 5000

CMD ["python", "app.py"]
