from app.utils.text import chunk_text, is_meaningful_text, normalize_text


def test_normalize_collapses_whitespace():
    assert normalize_text("hello   world") == "hello world"
    assert normalize_text("hello   \n\n\n  world") == "hello\n\nworld"


def test_meaningless_short_text():
    assert is_meaningful_text("hi", page_count=3) is False


def test_meaningful_long_text():
    text = "This is a sentence about testing extraction quality. " * 20
    assert is_meaningful_text(text, page_count=1) is True


def test_chunk_text_splits_and_covers():
    text = ("Paragraph one talks about alpha.\n\n" * 80) + (
        "Paragraph two talks about beta.\n\n" * 80
    )
    chunks = chunk_text(text, chunk_size=400, overlap=40)
    assert len(chunks) > 1
    assert all(chunks)
