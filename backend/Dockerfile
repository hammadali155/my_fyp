# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-cache

FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

# Copy venv and app code from builder
COPY --from=builder /app/.venv /app/.venv
# uv binary is needed at runtime for `uv run`
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Render injects env vars (DATABASE_URL, JWT_SECRET, etc.) at runtime.
# .env is gitignored and only used for local development.
CMD sh -c "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
