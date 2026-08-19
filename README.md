# Sudoku Solver 🧩

This computer vision application solves 9x9 Sudoku puzzles from images through a multi-stage process: It detects and extracts Sudoku grids from input images, recognizes existing digits using Tesseract OCR with custom preprocessing, solves the puzzle using an efficient backtracking algorithm, and finally overlays the digital solution back onto the original image for clear visualization.

<div align="center">
  <img src="assets/workflow.png" alt="Workflow" style="width:100%;"/>
</div>


## Installation ⚙️

### Prerequisites
Tesseract OCR installed on your system ([Installation guide](https://github.com/UB-Mannheim/tesseract/wiki))
### Clone the repository
```bash
git clone https://github.com/Monzer-Hw/sudoku-solver.git
```

### Prepare the environment using uv
```bash
uv sync
```
this will create a virtual environment and install the required dependencies.

### Or do the whole setup with just
[`just`](https://github.com/casey/just) is the task runner for this repo
(`uv tool install rust-just` if you do not have it yet):
```bash
just setup    # uv sync + create .env from .env.example + install the git hooks
```


## Task runner ⚡
Every routine command lives in the `justfile`; `just` on its own lists them.

| Recipe | What it runs |
|--------|--------------|
| `just sync` | `uv sync` |
| `just env` | Copy `.env.example` to `.env` when `.env` is missing |
| `just hooks` | Install the pre-commit and pre-push git hooks |
| `just hooks-run` | Run every hook over the whole repo |
| `just hooks-update` | `pre-commit autoupdate` |
| `just serve` | Dev server on `:8000` |
| `just format` / `just format-check` | `ruff format` (rewrite / check only) |
| `just lint` / `just lint-fix` | `ruff check` (report / autofix) |
| `just types` | `mypy src tests` |
| `just test` / `just test-e2e` / `just test-all` | Fast suite / e2e only / everything |
| `just cov` | Fast suite with the 90% coverage floor |
| `just check` | Everything CI enforces, in CI order |
| `just build` | `uv build` |
| `just clean` | Delete caches and build artifacts |
| `just docker-build` | Build the container image |
| `just docker-run` | Run the built image on `:8000` |
| `just docker-up` | Build and start the service through compose |


## Git hooks 🪝
[`pre-commit`](https://pre-commit.com) is configured in `.pre-commit-config.yaml`
and installed by `just hooks`:

- **pre-commit** — whitespace, end-of-file, large-file and private-key checks,
  `ruff format`, `ruff check --fix`, `mypy`, and `uv lock --check`.
- **pre-push** — the unit + integration suite behind the same 90% coverage floor
  as CI.

ruff, mypy, pytest and uv run as local `uv run` hooks, so a hook always uses the
version pinned in `uv.lock` instead of a separately pinned copy.
Skip a hook run with `git commit --no-verify` only when you know why.


## Usage 🚀
- Start the FastAPI server:
    ```bash
    uv run uvicorn src.api.main:app --reload
    ```

- Open interactive API docs:
    - `http://127.0.0.1:8000/docs`

- Solve (JSON response):
    ```bash
    curl -F "file=@assets/examples/1.jpg" http://127.0.0.1:8000/sudoku/solve
    ```

- Solve and return overlaid image (PNG):
    ```bash
    curl -o solved.png -F "file=@assets/examples/1.jpg" "http://127.0.0.1:8000/sudoku/solve:image"
    ```

> Tesseract is located via the `TESSERACT_CMD` environment variable, falling
> back to the binary on `PATH` and then to the default Windows install path.


## Docker 🐳
The image ships Tesseract and its English traineddata, so nothing needs to be
installed on the host beyond Docker itself.

```bash
just docker-build    # docker build -t sudoku-solver:local .
just docker-run      # docker run --rm -p 8000:8000 sudoku-solver:local
just docker-up       # build and start through compose
```

The endpoints are then the same ones as above, on `:8000`:
```bash
curl -F "file=@assets/examples/1.jpg" http://127.0.0.1:8000/sudoku/solve
```

`APP_NAME`, `APP_VERSION` and `FILE_ALLOWED_TYPES` are baked in as defaults, so
the container starts without a `.env`. Override them with `docker run -e`, or
create a `.env` and use compose — it reads one when present and starts fine
without it.

The build is two-stage: dependencies go into a virtualenv, then only that
virtualenv, `src/` and `assets/mask.png` are copied into a clean runtime image
that runs as a non-root user. The project is deliberately **not** pip-installed,
because `assets/mask.png` is located relative to `src/api/routes/sudoku.py` and
would not resolve from `site-packages`.


## Testing 🧪
The suite is split into three layers, selectable with pytest markers:

| Marker | Scope |
|--------|-------|
| `unit` | Single module in isolation (solver, detector, OCR, visualizer, config). |
| `integration` | API routes and the core pipeline wired together, with OCR stubbed. |
| `e2e` | Real HTTP requests over real example photos using the installed Tesseract. |

```bash
# Everything
uv run pytest

# Fast feedback: no OCR binary required
uv run pytest -m "unit or integration"

# Full stack against assets/examples (skipped when Tesseract is missing)
uv run pytest -m e2e

# With a coverage report
uv run pytest --cov=src --cov-report=term-missing
```

Lint, format and type checks:
```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
```

The same layers are available as `just test`, `just test-e2e`, `just test-all`,
`just cov`, and `just check` for the full lint + type + coverage gate.


## Continuous Integration 🔁
`.github/workflows/ci.yml` runs on every push to `main` and on every pull request:

- **Lint & format** — `ruff format --check`, `ruff check`, `mypy`.
- **Tests** — unit/integration with a 90% coverage floor, plus the e2e suite
  against a Tesseract installed on the runner; coverage reports are uploaded as
  artifacts.
- **Build** — `uv build` produces the sdist and wheel, which are installed into a
  clean environment to verify the app imports.
- **Docker image** — builds the image, starts the container and posts a real
  example photo to `/sudoku/solve`, asserting a complete 9x9 solution comes
  back. That is what proves Tesseract, its traineddata and the `assets/mask.png`
  lookup all work inside the image, rather than only on a developer machine.


## Project Structure 📁
```
sudoku-solver/
├── .github/
│ └── workflows/
│   └── ci.yml              # Lint & format, tests, build, Docker image
├── assets/
├── notebooks/
│ └── prototype.ipynb
├── scripts/
│ └── clean.py             # Cache/artifact cleanup behind `just clean`
├── tests/
│ ├── conftest.py           # Shared fixtures
│ ├── helpers.py            # Synthetic grid images & board checks
│ ├── unit/
│ ├── integration/
│ └── e2e/
├── src/
│ ├── __init__.py
│ ├── core/
│ │ ├── __init__.py
│ │ ├── detector.py      # Grid detection & processing
│ │ ├── ocr.py           # Digit recognition
│ │ ├── solver.py        # Puzzle solving logic
│ │ └── visualizer.py    # Solution visualization
│ └── api/
│   ├── __init__.py
│   ├── routes/
│   │ ├── __init__.py
│   │ ├── base.py
│   │ └── sudoku.py
│   ├── schemas/
│   │ ├── __init__.py
│   │ └── sudoku.py
│   ├── config.py
│   └── main.py          # FastAPI application entry point
├── pyproject.toml            # Dependencies
├── justfile                  # Task runner recipes
├── Dockerfile                # Two-stage image with Tesseract baked in
├── .dockerignore
├── compose.yml               # Single-service local wrapper
├── .pre-commit-config.yaml   # Git hook definitions
├── .env.example
├── requirements.txt
├── .gitignore
├── .python-version
├── README.md
├── LICENSE
└── uv.lock
```


## License 📄
MIT License - See [LICENSE](LICENSE) for details
