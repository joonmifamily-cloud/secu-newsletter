"""Send a small Gmail API message without invoking the news collector."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from gmail_api import GmailApiClient, GmailOAuthCredentials


KST = timezone(timedelta(hours=9))


def main() -> None:
    now = datetime.now(KST)
    sender = os.environ["GMAIL_USER"]
    recipients = [item.strip() for item in os.environ["TO_EMAILS"].split(",")]
    client = GmailApiClient(
        GmailOAuthCredentials(
            client_id=os.environ["GMAIL_CLIENT_ID"],
            client_secret=os.environ["GMAIL_CLIENT_SECRET"],
            refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        )
    )

    subject = f"[TEST][Gmail API] 클라우드 발송 확인 {now:%Y-%m-%d %H:%M} KST"
    html_content = f"""\
<!doctype html>
<html lang="ko">
  <body style="margin:0;background:#f3f6fa;font-family:Arial,'Noto Sans KR',sans-serif;color:#172033">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6fa;padding:28px 12px">
      <tr><td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#ffffff;border:1px solid #dfe6ef;border-radius:14px">
          <tr><td style="padding:30px">
            <div style="font-size:12px;font-weight:700;letter-spacing:.08em;color:#2864dc">GMAIL API CLOUD TEST</div>
            <h1 style="margin:10px 0 14px;font-size:24px">PC 전원과 무관한 발송 경로가 연결되었습니다.</h1>
            <p style="margin:0 0 18px;line-height:1.7;color:#4a5568">이 메일은 GitHub Actions에서 Gmail API의 최소 권한(<code>gmail.send</code>)으로 발송한 연결 확인용 메일입니다.</p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f9fe;border-radius:10px">
              <tr><td style="padding:16px;line-height:1.8">
                <strong>발신/수신</strong>: {sender}<br>
                <strong>실행 시각</strong>: {now:%Y-%m-%d %H:%M:%S} KST<br>
                <strong>실행 환경</strong>: GitHub Actions (클라우드)
              </td></tr>
            </table>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
"""
    plain_content = (
        "Gmail API 클라우드 발송 경로가 연결되었습니다.\n"
        f"발신/수신: {sender}\n"
        f"실행 시각: {now:%Y-%m-%d %H:%M:%S} KST\n"
        "실행 환경: GitHub Actions (클라우드)"
    )
    message_id = client.send_html(
        sender=sender,
        recipients=recipients,
        subject=subject,
        html_content=html_content,
        plain_content=plain_content,
    )
    print(f"Gmail API smoke test sent successfully. message_id={message_id}")


if __name__ == "__main__":
    main()
