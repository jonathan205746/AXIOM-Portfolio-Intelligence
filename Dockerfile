# AI-Powered Portfolio Optimizer — Streamlit Dashboard Dockerfile
FROM python:3.10-slim-bookworm

# ── System dependencies ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Set working directory ──
WORKDIR /app

# ── Copy requirements first (for layer caching) ──
COPY requirements-frontend.txt .

# ── Install Python dependencies ──
# Use CPU-only PyTorch to save ~2GB image size
# FIXED: torch==2.2.0 matches requirements-frontend.txt
RUN pip install --no-cache-dir torch==2.2.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-frontend.txt

# ── Copy application code ──
COPY frontend/ ./frontend/
COPY src/ ./src/
COPY data/ ./data/

# ── Create directories for runtime data ──
RUN mkdir -p /tmp/faiss_index /tmp/plots

# ── Environment variables ──
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501
ENV DB_DIR=/tmp/data
# ── Expose port ──
EXPOSE 8501

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Start Streamlit (Render injects $PORT) ──
CMD ["sh", "-c", "streamlit run frontend/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false"]
