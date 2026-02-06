import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import aiofiles
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .logging_conf import setup_logging
from .db import init_db, get_conn
from .models import SubmissionOut, RateIn
from .config import settings
from .storage import ensure_dirs, safe_join
from .pdf_service import replace_text_in_pdf

log = logging.getLogger("app")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def make_output_url(submission_id: str) -> str:
    return f"/api/submissions/{submission_id}/download"

def db_row_to_out(row) -> SubmissionOut:
    (id_, filename, content_type, status, created_at, updated_at,
     replacements_json, output_path, error, rating, rating_note) = row

    return SubmissionOut(
        id=id_,
        filename=filename,
        content_type=content_type,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        output_url=make_output_url(id_) if output_path else None,
        error=error,
        rating=rating,
        rating_note=rating_note,
    )

def create_app() -> FastAPI:
    setup_logging()
    ensure_dirs()
    init_db()

    app = FastAPI(title="Doc Sanitizer PoC", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # PoC; tighten later
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id

        class RequestIdFilter(logging.Filter):
            def filter(self, record):
                record.request_id = request_id
                return True

        root = logging.getLogger()
        root.addFilter(RequestIdFilter())
        try:
            resp = await call_next(request)
            resp.headers["x-request-id"] = request_id
            return resp
        finally:
            root.removeFilter(RequestIdFilter())

    def update_status(submission_id: str, status: str, output_path: Optional[str] = None, error: Optional[str] = None):
        with get_conn() as conn:
            conn.execute(
                "UPDATE submissions SET status=?, updated_at=?, output_path=?, error=? WHERE id=?",
                (status, now_iso(), output_path, error, submission_id),
            )
            conn.commit()

    def process_submission(submission_id: str, upload_path: Path, replacements: Dict[str, str]):
        log.info(f"[PROCESS] start submission_id={submission_id}")
        update_status(submission_id, "processing")

        try:
            out_name = f"{submission_id}.sanitized.pdf"
            out_path = safe_join(settings.outputs_dir, out_name)

            replaced_count, err = replace_text_in_pdf(
                str(upload_path),
                str(out_path),
                replacements,
            )

            log.info(f"[PROCESS] done submission_id={submission_id} replaced_count={replaced_count}")
            update_status(submission_id, "done", output_path=str(out_path), error=None)

        except Exception as e:
            log.exception(f"[PROCESS] failed submission_id={submission_id}")
            update_status(submission_id, "failed", output_path=None, error=str(e))

    #--- FRONTEND SERVING (HTML + JS + CSS) ---

    BASE_DIR = Path(__file__).resolve().parents[2]   # doc-sanitizer/
    FRONTEND_DIR = BASE_DIR / "frontend"

    # Serve CSS / JS
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static",
    )

    # Serve index.html at /
    @app.get("/", response_class=HTMLResponse)
    def serve_frontend():
        index_file = FRONTEND_DIR / "index.html"
        return index_file.read_text(encoding="utf-8")

    @app.get("/api/health")
    def health():
        return {"ok": True, "time": now_iso()}

    @app.post("/api/submissions", response_model=SubmissionOut)
    async def create_submission(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        replacements_json: str = Form(...),
    ):
        if file.content_type not in ("application/pdf",):
            raise HTTPException(status_code=400, detail="Only PDF supported in this PoC.")

        try:
            replacements = json.loads(replacements_json)
            if not isinstance(replacements, dict):
                raise ValueError("replacements_json must be a JSON object.")
            # normalize to str->str
            replacements = {str(k): str(v) for k, v in replacements.items()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid replacements_json: {e}")

        submission_id = uuid.uuid4().hex
        created = now_iso()

        upload_name = f"{submission_id}.upload.pdf"
        upload_path = safe_join(settings.uploads_dir, upload_name)

        log.info(f"[UPLOAD] start filename={file.filename} content_type={file.content_type} submission_id={submission_id}")

        async with aiofiles.open(upload_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await f.write(chunk)

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO submissions
                (id, filename, content_type, status, created_at, updated_at, replacements_json, output_path, error, rating, rating_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """,
                (
                    submission_id,
                    file.filename,
                    file.content_type,
                    "queued",
                    created,
                    created,
                    json.dumps(replacements),
                ),
            )
            conn.commit()

        background_tasks.add_task(process_submission, submission_id, upload_path, replacements)

        with get_conn() as conn:
            row = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()

        log.info(f"[UPLOAD] queued submission_id={submission_id}")
        return db_row_to_out(row)

    @app.get("/api/submissions", response_model=list[SubmissionOut])
    def list_submissions(limit: int = 50, offset: int = 0):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM submissions ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [db_row_to_out(r) for r in rows]

    @app.get("/api/submissions/{submission_id}", response_model=SubmissionOut)
    def get_submission(submission_id: str):
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return db_row_to_out(row)

    @app.get("/api/submissions/{submission_id}/download")
    def download(submission_id: str):
        with get_conn() as conn:
            row = conn.execute("SELECT output_path, status FROM submissions WHERE id=?", (submission_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")

        output_path, status = row
        if status != "done" or not output_path:
            raise HTTPException(status_code=400, detail="File not ready")

        p = Path(output_path)
        if not p.exists():
            raise HTTPException(status_code=404, detail="Output file missing")

        return FileResponse(str(p), media_type="application/pdf", filename=p.name)

    @app.post("/api/submissions/{submission_id}/rate", response_model=SubmissionOut)
    def rate_submission(submission_id: str, payload: RateIn):
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Not found")

            conn.execute(
                "UPDATE submissions SET rating=?, rating_note=?, updated_at=? WHERE id=?",
                (payload.rating, payload.note, now_iso(), submission_id),
            )
            conn.commit()

            row2 = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
        return db_row_to_out(row2)

    return app

app = create_app()
