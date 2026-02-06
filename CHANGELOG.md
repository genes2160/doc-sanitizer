# Changelog

## [0.1.0] - Initial PoC
### Added
- FastAPI Swagger backend for PDF sanitization
- Upload endpoint with replacements map (JSON)
- Background processing with status tracking
- SQLite storage for submissions, status, output link, errors
- Download endpoint for sanitized PDFs
- Rating endpoint (1–5) stored per submission
- Mobile-friendly HTML/CSS/JS UI with history + download + rating
- Request-id + step-by-step logs for tracing failures
