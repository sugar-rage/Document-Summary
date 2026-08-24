from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.auth import CurrentUser
from app.core.config import settings


def db_for(user: CurrentUser) -> "SupabaseRest":
    return SupabaseRest(user.token)


class DatabaseError(Exception):
    pass


class SupabaseRest:
    def __init__(self, access_token: str):
        self._token = access_token
        self._base = settings.supabase_url.rstrip("/") + "/rest/v1"

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "apikey": settings.supabase_anon_key,
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to access this resource.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Database request failed.",
            )

    def get(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        try:
            response = httpx.get(
                f"{self._base}/{table}",
                headers=self._headers(),
                params=params,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        self._raise_for_status(response)
        data = response.json()
        if not isinstance(data, list):
            return []
        return data

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self._base}/{table}",
                headers=self._headers(prefer="return=representation"),
                json=row,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        self._raise_for_status(response)
        data = response.json()
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database returned an unexpected response.",
        )

    def update(
        self, table: str, match: dict[str, str], row: dict[str, Any]
    ) -> dict[str, Any] | None:
        try:
            response = httpx.patch(
                f"{self._base}/{table}",
                headers=self._headers(prefer="return=representation"),
                params=match,
                json=row,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        self._raise_for_status(response)
        data = response.json()
        if isinstance(data, list) and data:
            return data[0]
        return None

    def delete(self, table: str, match: dict[str, str]) -> None:
        try:
            response = httpx.delete(
                f"{self._base}/{table}",
                headers=self._headers(),
                params=match,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        self._raise_for_status(response)

    def upsert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self._base}/{table}",
                headers=self._headers(
                    prefer="return=representation,resolution=merge-duplicates"
                ),
                params={"on_conflict": "document_id,mode"},
                json=row,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        self._raise_for_status(response)
        data = response.json()
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database returned an unexpected response.",
        )
