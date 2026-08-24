from app.services.validate import FileValidationError, validate_upload


def test_rejects_empty_file():
    try:
        validate_upload("a.pdf", "application/pdf", b"", 10_000)
        raise AssertionError("expected failure")
    except FileValidationError as exc:
        assert "empty" in exc.message.lower()


def test_rejects_unsupported_extension():
    try:
        validate_upload("malware.exe", "application/octet-stream", b"MZ", 10_000)
        raise AssertionError("expected failure")
    except FileValidationError as exc:
        assert exc.status_code == 415


def test_rejects_oversize():
    data = b"%PDF-1.4 " + b"x" * 100
    try:
        validate_upload("a.pdf", "application/pdf", data, max_bytes=20)
        raise AssertionError("expected failure")
    except FileValidationError as exc:
        assert exc.status_code == 413


def test_accepts_pdf_magic():
    data = b"%PDF-1.4\n1 0 obj\n"
    result = validate_upload("notes.pdf", "application/pdf", data, 10_000)
    assert result.content_type == "application/pdf"


def test_rejects_png_named_as_pdf():
    data = b"\x89PNG\r\n\x1a\n" + b"xxxx"
    try:
        validate_upload("fake.pdf", "application/pdf", data, 10_000)
        raise AssertionError("expected failure")
    except FileValidationError:
        pass


def test_accepts_jpeg_magic():
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    result = validate_upload("scan.jpg", "image/jpeg", data, 10_000)
    assert result.content_type == "image/jpeg"
