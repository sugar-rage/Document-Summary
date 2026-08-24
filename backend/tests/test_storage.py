from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.storage import SupabaseStorageService


def test_storage_headers():
    service = SupabaseStorageService("test-jwt-token")
    headers = service._headers({"Content-Type": "application/pdf"})
    assert headers["Authorization"] == "Bearer test-jwt-token"
    assert headers["Content-Type"] == "application/pdf"
    assert "apikey" in headers


@patch("httpx.post")
def test_storage_upload_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    service = SupabaseStorageService("test-jwt-token")
    result = service.upload_file("user-id/test.pdf", b"fake pdf data", "application/pdf")
    assert result == "user-id/test.pdf"
    assert mock_post.called


@patch("httpx.get")
def test_storage_download_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"pdf-content-bytes"
    mock_get.return_value = mock_response

    service = SupabaseStorageService("test-jwt-token")
    data = service.download_file("user-id/test.pdf")
    assert data == b"pdf-content-bytes"


@patch("httpx.get")
def test_storage_download_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    service = SupabaseStorageService("test-jwt-token")
    with pytest.raises(HTTPException) as exc_info:
        service.download_file("non-existent-user/missing.pdf")
    assert exc_info.value.status_code == 404
