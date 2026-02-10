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

# gunicorn with 1 worker + 4 threads (ML models need single-process)
# --timeout 300 to handle slow LLM / web-scrape calls
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
