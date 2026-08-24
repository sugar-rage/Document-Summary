# Backend

FastAPI service for authentication-gated document upload, extraction, OCR, Gemini summarization, history, and PDF export.

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --timeout-keep-alive 300
```

Install Tesseract OCR and ensure `tesseract` is on PATH.

## Tests

```bash
pytest
```
