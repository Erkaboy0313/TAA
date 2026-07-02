# TAA — application image (E00-S02 / E00-S03).
# Multi-stage: builder compiles wheels, runtime is thin. Non-root user from
# day one (project-context R10 §9 — production hygiene). Base is Python 3.12
# slim; matches project-context §2 tech stack.
#
# Two final targets (E00-S03):
#   - `dev`     — includes dev tooling (ruff, pytest, factory-boy) so
#                 `docker compose exec app pytest` works locally.
#   - `runtime` — production image, runtime dependencies only. Keeps prod
#                 image lean (project-context R6 — no dev bloat in prod).
# docker-compose.yml targets `dev`; the eventual prod build targets `runtime`.

# ---------------------------------------------------------------------------
# Stage 1 — builder: install build deps, compile wheels from requirements.
# Installs BOTH runtime and dev requirements into a shared prefix. The
# runtime stage cherry-picks only runtime wheels via a second install pass
# from `requirements.txt` in the `runtime-deps` stage below.
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
COPY requirements.txt requirements-dev.txt ./

# Runtime-only install prefix (goes into `runtime` final stage).
RUN pip install --no-cache-dir --prefix=/install-runtime -r requirements.txt

# Full install prefix (runtime + dev; goes into `dev` final stage).
# Simpler than juggling separate wheelhouses — R1: simplicity wins.
RUN pip install --no-cache-dir --prefix=/install-dev \
        -r requirements.txt -r requirements-dev.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime-base: shared OS layer for both `dev` and `runtime`
# final stages. libpq5 only — psycopg[binary] wheels bundle libpq but keep
# it available for future story if we switch to source psycopg.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 3a — runtime: production image. Only runtime wheels copied.
# ---------------------------------------------------------------------------
FROM runtime-base AS runtime

COPY --from=builder /install-runtime /usr/local

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# /health/ endpoint lands in a later story (bot foundation). Healthcheck
# stub documented here so ops surface is ready when it does.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

CMD ["uvicorn", "taa.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------------------
# Stage 3b — dev: local image. Runtime + dev wheels; used by docker-compose.
# ---------------------------------------------------------------------------
FROM runtime-base AS dev

COPY --from=builder /install-dev /usr/local

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

CMD ["uvicorn", "taa.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
