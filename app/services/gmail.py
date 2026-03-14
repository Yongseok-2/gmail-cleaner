import asyncio
from typing import Any

import httpx
from fastapi import HTTPException, status

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


class GmailService:
    async def fetch_unread_emails(
        self,
        access_token: str,
        user_id: str = "me",
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"q": "is:unread", "maxResults": max_results}
        list_url = f"{GMAIL_API_BASE}/users/{user_id}/messages"

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                list_response = await client.get(list_url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to connect Gmail API: {exc}",
                ) from exc

            if list_response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Failed to fetch unread Gmail list",
                        "google_response": list_response.text,
                    },
                )

            message_refs = list_response.json().get("messages", [])
            if not message_refs:
                return []

            detail_tasks = [
                self._fetch_message_detail(
                    client=client,
                    access_token=access_token,
                    user_id=user_id,
                    message_id=item["id"],
                )
                for item in message_refs
            ]
            results = await asyncio.gather(*detail_tasks, return_exceptions=True)

        emails: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            emails.append(result)
        return emails

    async def _fetch_message_detail(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        user_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        url = f"{GMAIL_API_BASE}/users/{user_id}/messages/{message_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        params: list[tuple[str, str]] = [
            ("format", "metadata"),
            ("metadataHeaders", "Subject"),
            ("metadataHeaders", "From"),
            ("metadataHeaders", "To"),
            ("metadataHeaders", "Date"),
        ]
        response = await client.get(url, headers=headers, params=params)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"Failed to fetch message detail: {message_id}",
                    "google_response": response.text,
                },
            )

        data = response.json()
        headers_map = self._extract_headers(data.get("payload", {}).get("headers", []))
        return {
            "gmail_message_id": data.get("id"),
            "gmail_thread_id": data.get("threadId"),
            "subject": headers_map.get("Subject", ""),
            "from_email": headers_map.get("From", ""),
            "to_email": headers_map.get("To", ""),
            "date_header": headers_map.get("Date", ""),
            "snippet": data.get("snippet", ""),
            "internal_date": data.get("internalDate"),
            "label_ids": data.get("labelIds", []),
            "raw": data,
        }

    @staticmethod
    def _extract_headers(headers: list[dict[str, str]]) -> dict[str, str]:
        return {item.get("name", ""): item.get("value", "") for item in headers}


gmail_service = GmailService()
