# Question Paper Intelligence System

A runnable, privacy-first MVP for turning mixed university-PDF archives into individually indexed, searchable question papers.

## What is included

- Upload and automatic split detection for digital PDFs
- Resilient metadata extraction: values absent from a paper become `Unknown`
- Per-paper local storage, full-text search, in-browser download and duplicate protection
- Modern responsive dashboard with an optional dark theme
- OpenAPI documentation at `/docs`, database layer ready for PostgreSQL
- Docker configuration and extractor tests

## Run locally

```powershell
cd 'C:\Users\PATTI VENU\Documents\Codex\2026-08-07\r\outputs\question-paper-intelligence-system'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://localhost:8000/app/](http://localhost:8000/app/). Use a digital PDF first; the service detects new papers by combining exam/header signals, then writes one file per detected boundary. API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

If packages cannot be installed, use the dependency-free runner instead:

```powershell
"C:\Users\PATTI VENU\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" serve.mjs
```

It starts the dashboard and supports actual PDF text extraction, automatic boundary detection and splitting, metadata extraction, search, and downloading without a Python package install.

## Architecture

```text
Browser dashboard → FastAPI routes → extraction service (PyMuPDF)
                                  ├→ SQLAlchemy database (SQLite / PostgreSQL)
                                  └→ local object storage (S3-compatible seam)
```

The `extractor` service is deliberately isolated: add OCR for pages without text and an LLM classifier as a second-pass metadata resolver without changing routes or persistence. For production, run uploads as a queue worker, replace SQLite with PostgreSQL and local storage with S3, and add JWT/RBAC at the API gateway.

## API surface

- `POST /api/uploads` — process a digital PDF
- `GET /api/papers?q=` — metadata and full-text search
- `GET /api/papers/{id}/download` — download one split paper
- `GET /api/dashboard` — dashboard metrics

## Docker

```powershell
docker compose up --build
```
