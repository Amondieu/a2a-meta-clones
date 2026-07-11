# a2a-meta-clones Dockerfile
# Shared by all 3 Railway service slots via ROOT_DIRECTORY=services/slot-X.

# === Stage 1: builder ===
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# === Stage 2: runtime ===
FROM python:3.12-slim

WORKDIR /app

# Python deps from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application code
COPY services/ /app/services/
COPY clone_specs/ /app/clone_specs/
COPY server_manifests/ /app/server_manifests/

# PYTHONPATH so the slots can import services.shared.*
ENV PYTHONPATH=/app

# Railway sets $PORT; default to 8080 for local.
ENV PORT=8080

EXPOSE 8080

# Healthcheck (per Phase C Railway config)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health').read()" || exit 1

# Default command: uvicorn. Railway overrides this per service via
# the per-slot railway.toml's startCommand field. Each slot has its
# own CLONE_X_ID env vars that select which clones the multiplexer
# serves.
CMD ["uvicorn", "services.shared.multiplexer.app:app", "--host", "0.0.0.0", "--port", "8080"]
