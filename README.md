# 🧼 Doc Sanitizer (PoC)

Upload a PDF, replace sensitive words/phrases, download a sanitized version.
Designed to help users share documents with AI without leaking private info.

## Features
- Upload PDF + replacements map
- Status tracking: queued → processing → done/failed
- Download sanitized PDF via link
- History view of all submissions
- Rating (good/bad via 1–5) stored for future learning
- Extensive logs with request-id

## Tech
- Backend: FastAPI + SQLite + PyMuPDF
- Frontend: HTML/CSS/JS (mobile-first)

## How it works
1. User uploads a PDF
2. User provides JSON replacements: { "John Doe": "Client A", ... }
3. Backend:
   - saves upload
   - creates submission row (queued)
   - processes in background:
     - searches for text occurrences
     - redacts original text boxes
     - inserts replacement text in same area
   - writes output PDF
   - updates status + output path
4. UI polls history and shows download link when ready

## Limitations (PoC)
- Works best with text-based PDFs.
- Scanned/image PDFs need OCR (planned).
- Exact string matching only (no fuzzy matching yet).

## Run (Backend)
... commands ...

## Run (Frontend)
... open index.html or serve folder ...

## API quick reference
- POST /api/submissions (multipart: file + replacements_json)
- GET /api/submissions
- GET /api/submissions/{id}
- GET /api/submissions/{id}/download
- POST /api/submissions/{id}/rate

## Logging & Debugging
- Every request returns `x-request-id`
- Server logs include the request-id and processing steps


```
cd backend
python -m venv .venv
# windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```