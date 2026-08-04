# AI-Powered Portfolio Optimizer — FastAPI Backend
# Build: docker build -f backend/Dockerfile -t portfolio-backend .

FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc g++ curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# FIXED: requirements-backend.txt is at PROJECT ROOT
COPY requirements-backend.txt .

RUN pip install --no-cache-dir torch==2.2.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements-backend.txt

COPY backend/ ./backend/
COPY src/ ./src/
COPY data/ ./data/

RUN mkdir -p /tmp/faiss_index /tmp/plots

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

# IMPORTANT: Match this to your actual main.py location
# If backend/app/main.py  →  backend.app.main:app
# If backend/main.py     →  backend.main:app
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
