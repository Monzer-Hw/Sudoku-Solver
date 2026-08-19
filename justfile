# Task runner for the Sudoku Solver service.
# Run `just` (or `just --list`) to see every recipe.

set windows-shell := ["cmd.exe", "/c"]

# List available recipes.
default:
    @just --list

# Create .venv and install all dependencies (runtime + dev group).
sync:
    uv sync

# Copy .env.example to .env when .env is missing (Settings has no defaults).
env:
    uv run python -c "import pathlib, shutil; p = pathlib.Path('.env'); print('.env already exists') if p.exists() else shutil.copy('.env.example', p)"

# One-shot setup for a fresh clone: dependencies, .env, git hooks.
setup: sync env hooks

# Install the pre-commit and pre-push git hooks.
hooks:
    uv run pre-commit install --install-hooks --hook-type pre-commit --hook-type pre-push

# Run every pre-commit hook over the whole repo.
hooks-run:
    uv run pre-commit run --all-files

# Bump the pinned hook revisions in .pre-commit-config.yaml.
hooks-update:
    uv run pre-commit autoupdate

# Dev server on :8000, docs at /docs.
serve:
    uv run uvicorn src.api.main:app --reload

# Rewrite files with the ruff formatter.
format:
    uv run ruff format .

# Fail if any file is unformatted (what CI checks).
format-check:
    uv run ruff format --check .

# Lint with ruff.
lint:
    uv run ruff check .

# Lint and apply the safe autofixes.
lint-fix:
    uv run ruff check --fix .

# Static type check.
types:
    uv run mypy src tests

# Fast suite: unit + integration, no Tesseract binary needed.
test:
    uv run pytest -m "unit or integration"

# Full suite, including e2e over assets/examples (needs Tesseract).
test-all:
    uv run pytest

# Only the e2e suite (auto-skipped when Tesseract is missing).
test-e2e:
    uv run pytest -m e2e

# Fast suite with the CI coverage floor.
cov:
    uv run pytest -m "unit or integration" --cov=src --cov-report=term-missing --cov-fail-under=90

# Everything CI enforces, in CI order.
check: format-check lint types cov

# Build the sdist and wheel.
build:
    uv build

# Delete caches and build artifacts.
clean:
    uv run python scripts/clean.py

# Build the container image (needs a running Docker daemon).
docker-build:
    docker build -t sudoku-solver:local .

# Run the built image on :8000; Ctrl-C stops and removes it.
docker-run:
    docker run --rm -p 8000:8000 sudoku-solver:local

# Build and start the service through compose, reading .env when present.
docker-up:
    docker compose up --build
