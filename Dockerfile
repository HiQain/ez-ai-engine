# ez — AI Takeoff engine (FastAPI + Celery). Pure-Python deps (pypdf, pymysql),
# so no system build tools or poppler are needed — just Python + curl for the
# container healthcheck. Base image matches the dev Python (3.14); change it if
# you pin a different version.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install deps first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Where uploaded drawings are written (mount a volume here to persist them).
RUN mkdir -p /app/uploads/takeoffs

EXPOSE 8000

# The web process. The worker/beat process overrides this command in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
