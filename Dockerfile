# AXIOM Portfolio Intelligence — Streamlit runtime
FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-frontend.txt .

RUN pip install --no-cache-dir torch==2.6.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-frontend.txt \
    && pip install --no-cache-dir --upgrade "streamlit>=1.36.0"

# Keep packaging tooling on patched releases so vulnerable vendored
# build dependencies are not retained in the runtime image.
RUN python -m pip install --no-cache-dir --upgrade \
    "pip==26.2.1" \
    "setuptools==84.0.0" \
    "wheel==0.48.0"


COPY frontend/ ./frontend/
COPY src/ ./src/
COPY data/ ./data/

# Fixed UID/GID keeps runtime ownership predictable across Docker and EC2.
RUN groupadd --gid 10001 axiom \
    && useradd --uid 10001 --gid axiom --create-home --home-dir /home/axiom \
        --shell /usr/sbin/nologin axiom \
    && mkdir -p /data /tmp/faiss_index /tmp/plots \
    && chown -R axiom:axiom /app /data /tmp/faiss_index /tmp/plots

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501
ENV HOME=/home/axiom

EXPOSE 8501

USER axiom

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8501}/_stcore/health || exit 1

CMD ["sh", "-c", "streamlit run frontend/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=true --server.enableXsrfProtection=true"]
