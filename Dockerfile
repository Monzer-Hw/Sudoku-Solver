# syntax=docker/dockerfile:1

# Two stages: the builder resolves dependencies into a virtualenv, the runtime
# stage keeps only that virtualenv, the source and the OCR binary. Building this
# way keeps uv and its caches out of the shipped image.


# --- builder -----------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Only the dependencies are installed here, never the project itself: the app is
# run from /app/src in the runtime stage (see the note there). Bind-mounting the
# manifests instead of copying them keeps this layer cached until they change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project


# --- runtime -----------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# pytesseract shells out to a real tesseract binary, so it has to be installed.
# tesseract-ocr-eng carries the English traineddata and is only a *recommended*
# dependency of tesseract-ocr: with --no-install-recommends it must be named
# explicitly, or OCR fails at request time instead of at build time.
# libglib2.0-0 is the one system library opencv-python-headless still needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Settings has no defaults, so without these the first request fails on a
# missing environment variable. FILE_ALLOWED_TYPES is parsed as JSON by
# pydantic-settings, so it has to stay a bracketed list literal.
ENV APP_NAME="Sudoku-Solver-API" \
    APP_VERSION="0.1.0" \
    FILE_ALLOWED_TYPES='["image/png", "image/jpeg", "image/jpg"]' \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# Created before the COPYs so --chown can set ownership in place; a later
# `chown -R` over the virtualenv would duplicate every file in a new layer.
RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

# The project is deliberately not pip-installed. src/api/routes/sudoku.py finds
# the OCR mask by walking three directories up from itself, so the source has to
# sit at /app/src for that to resolve to /app/assets/mask.png. Installed into
# site-packages it would resolve there instead and OCR would break silently.
COPY --chown=app:app src ./src

# mask.png is the only asset needed at runtime; the example photos and the
# README diagram are excluded by .dockerignore.
COPY --chown=app:app assets/mask.png ./assets/mask.png

USER app

EXPOSE 8000

# /base/ returns the app name and version, which makes it a cheap liveness probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/base/').read()"

# --host 0.0.0.0 is required, or the server is unreachable from outside the
# container. Add --workers to the override command if one process is not enough.
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
