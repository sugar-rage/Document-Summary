# Assignment write-up

Document Summary Assistant helps a student or researcher turn a PDF or image into a usable short, medium, or long summary with key points, without paying for hosting, auth, or an LLM plan.

The backend validates uploads, extracts digital PDF text with PyMuPDF, and falls back to Tesseract OCR for images and scanned pages. Large text is chunked, summarized in parts, then combined so Gemini’s free-tier limits are respected. Document content is wrapped as untrusted data so prompt-injection lines cannot override the summarizer.

Users sign in with Supabase email OTP. FastAPI checks the JWT and stores rows in Postgres under that user id, with row-level security so history is private. Summaries download as a real ReportLab PDF. Files are processed in temp storage and deleted; only text and summaries persist. The React client stays simple: login, dashboard, history. The stack is deployment-ready with env-based URLs and Docker, remaining on free tiers.
