from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.auth import CurrentUser
from app.core.config import settings


class SupabaseStorageService:
    def __init__(self, token: str):
        self._token = token
        self._base = settings.supabase_url.rstrip("/") + "/storage/v1"
        self._bucket = settings.supabase_storage_bucket or "documents"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "apikey": settings.supabase_anon_key,
        }
        if extra:
            headers.update(extra)
        return headers

    def upload_file(self, path: str, data: bytes, content_type: str) -> str:
        """Upload a file to Supabase Storage and return the storage path."""
        url = f"{self._base}/object/{self._bucket}/{path.lstrip('/')}"
        try:
            response = httpx.post(
                url,
                headers=self._headers(
                    {
                        "Content-Type": content_type,
                        "x-upsert": "true",
                    }
                ),
                content=data,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Storage is unavailable.",
            ) from exc

        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to store file in storage.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload document to Supabase Storage: {response.text}",
            )
        return path

    def download_file(self, path: str) -> bytes:
        """Download file bytes from Supabase Storage (with fallback for legacy local paths)."""
        # 1. Check if path is a legacy local file path on disk
        local_path = Path(path)
        if local_path.is_file():
            return local_path.read_bytes()

        # 2. Fetch from Supabase Storage
        # Try authenticated endpoint first, fall back to standard object endpoint
        clean_path = path.lstrip("/")
        url = f"{self._base}/object/authenticated/{self._bucket}/{clean_path}"
        try:
            response = httpx.get(
                url,
                headers=self._headers(),
                timeout=30.0,
            )
            if response.status_code == 404:
                # Fallback to standard object endpoint if authenticated endpoint returned 404
                fallback_url = f"{self._base}/object/{self._bucket}/{clean_path}"
                response = httpx.get(
                    fallback_url,
                    headers=self._headers(),
                    timeout=30.0,
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Storage is unavailable.",
            ) from exc

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original document file not found in storage.",
            )
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to access this storage object.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve file from Supabase Storage.",
            )
        return response.content

    def delete_file(self, path: str) -> None:
        """Delete file from Supabase Storage (and unlink legacy local file if exists)."""
        if not path:
            return

        local_path = Path(path)
        if local_path.is_file():
            try:
                local_path.unlink(missing_ok=True)
            except Exception:
                pass

        clean_path = path.lstrip("/")
        url = f"{self._base}/object/{self._bucket}/{clean_path}"
        try:
            httpx.delete(
                url,
                headers=self._headers(),
                timeout=30.0,
            )
        except Exception:
            # Also try batch prefixes delete if single object delete is not supported
            try:
                batch_url = f"{self._base}/object/{self._bucket}"
                httpx.request(
                    "DELETE",
                    batch_url,
                    headers=self._headers({"Content-Type": "application/json"}),
                    json={"prefixes": [clean_path]},
                    timeout=30.0,
                )
            except Exception:
                pass


def storage_for(user: CurrentUser) -> SupabaseStorageService:
    return SupabaseStorageService(user.token)
