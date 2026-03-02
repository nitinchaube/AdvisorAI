# ============================================================
# AdvisorAI Backend – Production Docker Image
# Deploys to Google Cloud Run
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# System dependencies needed by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code + VectorDB + data files
COPY . .

# Remove dev-only files that shouldn't be in the image
RUN rm -f .env .env.example

# Cloud Run sets PORT=8080 by default
EXPOSE 8080

# uvicorn with FastAPI — runs the async chat endpoints natively and
# mounts the Flask app via WSGIMiddleware for all other routes.
# --workers 2: each worker handles hundreds of concurrent SSE streams
# --limit-concurrency 200: prevent overload
# --timeout-keep-alive 30: clean up idle SSE connections
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--limit-concurrency", "200", "--timeout-keep-alive", "30", "--access-log", "--log-level", "info"]
