"""Minimal Gmail API sender using OAuth 2.0 offline credentials."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TOKEN_URL = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class GmailApiError(RuntimeError):
    """Raised when token exchange or message sending fails."""


@dataclass(frozen=True)
class GmailOAuthCredentials:
    client_id: str
    client_secret: str
    refresh_token: str


class GmailApiClient:
    def __init__(
        self,
        credentials: GmailOAuthCredentials,
        *,
        timeout: int = 30,
    ) -> None:
        self.credentials = credentials
        self.timeout = timeout

    def _request_json(
        self,
        url: str,
        *,
        body: bytes,
        headers: dict[str, str],
    ) -> tuple[int, dict]:
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            return error.code, {}

    def _access_token(self) -> str:
        status, payload = self._request_json(
            TOKEN_URL,
            body=urlencode(
                {
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                    "refresh_token": self.credentials.refresh_token,
                    "grant_type": "refresh_token",
                }
            ).encode("ascii"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not 200 <= status < 300:
            raise GmailApiError(f"OAuth token refresh failed: HTTP {status}")

        token = payload.get("access_token")
        if not token:
            raise GmailApiError("OAuth token response did not include access_token")
        return token

    def send_html(
        self,
        *,
        sender: str,
        recipients: Iterable[str],
        subject: str,
        html_content: str,
        plain_content: str,
    ) -> str:
        recipient_list = [address.strip() for address in recipients if address.strip()]
        if not recipient_list:
            raise ValueError("At least one recipient is required")

        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipient_list)
        message["Subject"] = subject
        message.set_content(plain_content)
        message.add_alternative(html_content, subtype="html")

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        status, payload = self._request_json(
            SEND_URL,
            body=json.dumps({"raw": raw}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
        )
        if not 200 <= status < 300:
            raise GmailApiError(f"Gmail messages.send failed: HTTP {status}")

        message_id = payload.get("id")
        if not message_id:
            raise GmailApiError("Gmail messages.send response did not include message id")
        return message_id
