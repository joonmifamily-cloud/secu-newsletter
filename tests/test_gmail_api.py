import base64
import unittest
from email import policy
from email.parser import BytesParser

from gmail_api import GmailApiClient, GmailOAuthCredentials


class FakeGmailApiClient(GmailApiClient):
    def __init__(self, credentials):
        super().__init__(credentials)
        self.calls = []

    def _request_json(self, url, *, body, headers):
        self.calls.append((url, body, headers))
        if url.endswith("/token"):
            return 200, {"access_token": "access-token"}
        return 200, {"id": "gmail-message-id", "threadId": "thread"}


class GmailApiClientTests(unittest.TestCase):
    def test_send_html_refreshes_token_and_sends_mime_message(self):
        client = FakeGmailApiClient(
            GmailOAuthCredentials("client", "secret", "refresh")
        )

        message_id = client.send_html(
            sender="joonmi.family@gmail.com",
            recipients=["joonmi.family@gmail.com"],
            subject="[데일리 보안 브리핑] 2026-08-13",
            html_content="<h1>브리핑</h1>",
            plain_content="브리핑",
        )

        self.assertEqual(message_id, "gmail-message-id")
        self.assertEqual(len(client.calls), 2)
        _, send_body, send_headers = client.calls[1]
        self.assertEqual(
            send_headers["Authorization"], "Bearer access-token"
        )

        import json

        mime_bytes = base64.urlsafe_b64decode(json.loads(send_body)["raw"])
        message = BytesParser(policy=policy.default).parsebytes(mime_bytes)
        self.assertEqual(message["From"], "joonmi.family@gmail.com")
        self.assertEqual(message["To"], "joonmi.family@gmail.com")
        self.assertEqual(message["Subject"], "[데일리 보안 브리핑] 2026-08-13")
        self.assertTrue(message.is_multipart())


if __name__ == "__main__":
    unittest.main()
