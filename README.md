# Document Summary Assistant

Upload a PDF or image, extract text (with OCR when needed), and generate short, medium, or long AI summaries with key points. Each signed-in user only sees their own history and can download a summary PDF.

This is a student/technical-assessment project designed to run at **₹0 / $0** using free-tier services and local tools. Do not enter a credit card for any required step. If a signup asks for payment, stop and choose another free option.

## Features

- Email OTP sign-in (Supabase Auth)
- PDF / PNG / JPG / JPEG upload with size, type, and magic-byte checks
- Native PDF text extraction (PyMuPDF)
- Tesseract OCR for images and scanned PDFs
- Gemini summaries: short, medium, long, plus key points
- Map-reduce chunking for large documents
- Per-user history with RLS
- Summary PDF export (ReportLab)
- Loading and error states

## Architecture

```
React (Vite)  →  FastAPI  →  PyMuPDF / Tesseract / Gemini
                    ↓
              Supabase Auth + Postgres (RLS)
```

Uploaded files are processed in a temporary directory and deleted after extraction. Postgres stores extracted text and summaries, not original binaries.

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | React, TypeScript, Vite, simple CSS |
| Backend | Python, FastAPI |
| Auth / DB | Supabase free (email OTP + Postgres) |
| Extraction | PyMuPDF |
| OCR | Tesseract + pytesseract + Pillow |
| LLM | Google Gemini (`gemini-2.5-flash` by default, configurable) |
| PDF export | ReportLab |

## Workflow

1. User requests an email OTP and verifies it.
2. Frontend sends the Supabase JWT to FastAPI.
3. FastAPI validates the JWT and never trusts a client-supplied user id.
4. Upload is validated, text is extracted or OCRed, then the temp file is deleted.
5. Gemini returns a summary and key points for the chosen length.
6. History lists only that user's rows. PDF download is generated on the server.

## Project structure

```
frontend/     React SPA
backend/      FastAPI app
supabase/     schema.sql (tables, indexes, RLS)
docs/         short assignment write-up
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Tesseract OCR (`eng`) on PATH, **or** Docker
- Free [Supabase](https://supabase.com) project
- Free [Google AI Studio](https://aistudio.google.com) API key

## Installation

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# frontend
cd ../frontend
npm install
```

Copy `.env.example` to `backend/.env` and `frontend/.env`.

## Environment variables

Backend: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `MAX_UPLOAD_BYTES`, `MAX_PDF_PAGES`, `MAX_EXTRACTED_CHARS`, `CORS_ORIGINS`.

Frontend (public only): `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`.

Never put `GEMINI_API_KEY` or `SUPABASE_JWT_SECRET` in the frontend.

## Supabase setup

1. Create a free project.
2. Authentication → Providers → Email: enable **OTP** (email). You do not need a custom SMTP for a demo; default mail has rate limits.
3. Project Settings → API: copy URL, anon key, and JWT secret.
4. SQL editor: run `supabase/schema.sql`.

## Gemini setup

1. Open Google AI Studio and create an API key **without enabling billing**.
2. Set `GEMINI_API_KEY` and `GEMINI_MODEL=gemini-2.5-flash`.
3. If that model id is rejected, try another current **free-tier Flash** id and update the env var. Do not use deprecated models.

Free-tier prompts may be used by Google to improve products. Rate limits apply (requests per minute/day).

## Tesseract / OCR setup

Windows (local): install Tesseract from the official installer and add it to PATH.

Docker: `backend/Dockerfile` installs `tesseract-ocr`.

English only in v1.

## Running the backend

```bash
cd backend
uvicorn app.main:app --reload --timeout-keep-alive 300
```

Health check: `GET http://localhost:8000/api/health`

## Running the frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## Testing

```bash
cd backend
pytest
```

Manual checks: OTP login, PDF upload, image OCR, invalid/oversize files, three summary lengths, history isolation, PDF download, logout.

## Deployment

Local-first. Production-ready pieces: Dockerfile, env-based URLs, temp file processing, no committed secrets.

Suggested **₹0** path if signups do not ask for a card:

- Frontend: Render static site, Cloudflare Pages, or Netlify
- Backend: Render free Docker/Python web service
- Database/auth: stay on Supabase free (do not use a 30-day trial database that expires)

If a host requires a credit card, **do not proceed** with that host. Keep the API local.

Free Render services sleep when idle; the first request can be slow. 512 MB RAM: keep PDF page/DPI limits as configured.

## API overview

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/health` | No |
| POST | `/api/documents` | JWT |
| GET | `/api/documents` | JWT |
| GET | `/api/documents/{id}` | JWT |
| DELETE | `/api/documents/{id}` | JWT |
| POST | `/api/documents/{id}/summaries` | JWT |
| GET | `/api/summaries/{id}/pdf` | JWT |

JSON errors: `{ "detail": "..." }`.

## Security considerations

- JWT verification on every document/summary route
- RLS so `user_id = auth.uid()`
- Upload allowlist + magic bytes + 10 MB cap
- Document text treated as untrusted (prompt delimiters)
- No service-role key in the browser
- `.env` is gitignored

## Limitations

- English OCR only
- Page and size caps for free-tier RAM and Gemini quota
- Supabase default email is rate-limited
- OCR quality depends on scan quality
- Gemini free tier can return HTTP 429

## Future improvements

Background jobs, more OCR languages, optional object storage, streaming tokens. Intentionally omitted to keep the assessment small and reliable.
