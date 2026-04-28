# syntax=docker/dockerfile:1.6
# ============================================================
# AdvisorAI Backend — Production Docker Image
# Multi-stage build: smaller runtime layer, faster cold starts.
# Same image is used by the Cloud Run service (uvicorn) AND the
# Cloud Run Job for scheduled scraping (different CMD override).
# ============================================================

# ----- Stage 1: builder -----
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ----- Stage 2: runtime -----
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

EXPOSE 8080

# Default CMD: serve the API. The Cloud Run Job overrides this to:
#   ["python", "run_unified_scraper.py"]
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "2", \
     "--limit-concurrency", "200", \
     "--timeout-keep-alive", "30", \
     "--access-log", \
     "--log-level", "info"]
