# TAA — application image (E00-S02).
# Multi-stage: builder compiles wheels, runtime is thin. Non-root user from
# day one (project-context R10 §9 — production hygiene). Base is Python 3.12
# slim; matches project-context §2 tech stack.

# ---------------------------------------------------------------------------
# Stage 1 — builder: install build deps, compile wheels from requirements.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build toolchain needed only in this stage (removed in runtime image).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements first so pip layer caches when only source changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime: thin image, non-root user, prod-ready ASGI entrypoint.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:${PATH}"

# libpq5 only — psycopg[binary] wheels bundle libpq but keep it available
# for future story if we switch to source psycopg.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy pre-built site-packages from builder.
COPY --from=builder /install /usr/local

WORKDIR /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# /health/ endpoint lands in a later story (bot foundation). Healthcheck
# stub documented here so ops surface is ready when it does.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

CMD ["uvicorn", "taa.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
