import re


def normalize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\x00", " ")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def is_meaningful_text(text: str, page_count: int) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    if len(compact) < 200:
        return False
    min_chars = max(200, page_count * 40)
    return len(compact) >= min_chars


def chunk_text(text: str, chunk_size: int = 10_000, overlap: int = 200) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            window = text[start:end]
            split_at = window.rfind("\n\n")
            if split_at < chunk_size * 0.4:
                split_at = window.rfind("\n")
            if split_at >= chunk_size * 0.4:
                end = start + split_at
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks
