import anthropic
import os
import json
import re
import html as html_mod
from datetime import datetime, timezone, timedelta
from pathlib import Path

from gmail_api import GmailApiClient, GmailOAuthCredentials

# --- Configuration ---
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST)
DATE_STR = TODAY.strftime("%Y-%m-%d")
DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
DAY_KR = DAY_NAMES[TODAY.weekday()]

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]
TO_EMAILS = [e.strip() for e in os.environ["TO_EMAILS"].split(",")]

SECTIONS = [
    {"id": "breaking", "icon": "🔴", "title": "주요 보안 뉴스", "color": "#e74c3c"},
    {"id": "policy", "icon": "🟠", "title": "정책·규제 동향", "color": "#e67e22"},
    {"id": "technology", "icon": "🔵", "title": "보안 기술 동향", "color": "#3498db"},
    {"id": "solutions", "icon": "🟢", "title": "솔루션·제품 동향", "color": "#27ae60"},
]


def collect_news():
    """Claude API + web search로 보안 뉴스 수집"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""오늘은 {DATE_STR} ({DAY_KR}요일)입니다.

당신은 사이버보안 전문 컨설턴트입니다. 웹 검색을 활용하여 오늘 또는 최근 1~2일 이내의 사이버보안 관련 뉴스를 수집해 주세요.

아래 4개 카테고리별로 각 3~5개의 기사를 찾아주세요:

1. breaking — 주요 보안 뉴스: 국내외 보안 이슈, 침해사고, 취약점 공개, 해킹 사건
2. policy — 정책·규제 동향: 각국 사이버보안 정책, 법규 제·개정, 규제 변화, 정부 발표
3. technology — 보안 기술 동향: 새로운 보안 기술, 위협 연구, 공격/방어 기법, AI 보안
4. solutions — 솔루션·제품 동향: 보안 솔루션/제품 출시·업데이트, 기업 인수합병, 시장 동향

검색 시 다양한 키워드를 활용하세요:
- 한국어: "사이버보안 뉴스", "정보보호", "해킹", "취약점", "개인정보보호", "보안 정책"
- 영어: "cybersecurity news today", "data breach", "vulnerability disclosure", "security policy"

반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 절대 포함하지 마세요:
{{
  "sections": [
    {{
      "category": "breaking",
      "articles": [
        {{
          "title": "기사 제목 (한국어)",
          "summary": "2~3문장 핵심 요약 (한국어)",
          "source": "출처명",
          "url": "기사 원문 URL"
        }}
      ]
    }},
    {{
      "category": "policy",
      "articles": [...]
    }},
    {{
      "category": "technology",
      "articles": [...]
    }},
    {{
      "category": "solutions",
      "articles": [...]
    }}
  ]
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        tools=[{"type": "web_search_20250305", "max_uses": 10}],
        messages=[{"role": "user", "content": prompt}],
    )

    # 응답에서 텍스트 추출
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    # JSON 파싱 (여러 방법 시도)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    json_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_block:
        return json.loads(json_block.group(1).strip())

    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        return json.loads(json_match.group())

    raise ValueError(f"JSON 파싱 실패. 응답 앞부분: {text[:500]}")


def esc(s):
    """HTML 이스케이프"""
    return html_mod.escape(str(s))


def build_html(data):
    """수집된 뉴스 데이터로 카드뉴스 스타일 HTML 이메일 생성"""
    section_map = {s["id"]: s for s in SECTIONS}

    cards_html = ""
    for section_data in data["sections"]:
        cat_id = section_data["category"]
        section = section_map.get(cat_id)
        if not section:
            continue

        articles_html = ""
        articles = section_data.get("articles", [])
        for i, article in enumerate(articles):
            border = (
                "border-bottom: 1px solid #eef0f2;"
                if i < len(articles) - 1
                else ""
            )
            title = esc(article["title"])
            summary = esc(article["summary"])
            source = esc(article["source"])
            url = esc(article["url"])

            articles_html += f"""
              <tr>
                <td style="padding: 14px 18px; {border}">
                  <a href="{url}" target="_blank"
                     style="color: #1a1a2e; text-decoration: none; font-weight: 600; font-size: 15px; line-height: 1.5; display: block;">
                    {title}
                  </a>
                  <p style="margin: 6px 0 0; color: #5a6377; font-size: 13px; line-height: 1.6;">
                    {summary}
                  </p>
                  <p style="margin: 8px 0 0;">
                    <span style="color: #9ca3af; font-size: 11px;">📰 {source}</span>
                    <a href="{url}" target="_blank"
                       style="color: {section['color']}; font-size: 11px; text-decoration: none; margin-left: 12px; font-weight: 600;">
                      원문 보기 →
                    </a>
                  </p>
                </td>
              </tr>"""

        cards_html += f"""
          <tr>
            <td style="padding: 0 24px 16px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border: 1px solid #e8eaed; border-radius: 10px; overflow: hidden;">
                <tr>
                  <td style="background-color: {section['color']}; padding: 14px 18px;">
                    <span style="color: #ffffff; font-size: 17px; font-weight: 700;">
                      {section['icon']} {section['title']}
                    </span>
                  </td>
                </tr>
                {articles_html}
              </table>
            </td>
          </tr>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f0f2f5;
             font-family: -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td align="center" style="padding: 24px 16px;">
        <table width="640" cellpadding="0" cellspacing="0"
               style="background-color: #ffffff; border-radius: 14px;
                      overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background-color: #1a1a2e; padding: 36px 24px; text-align: center;">
              <p style="margin: 0 0 8px; font-size: 36px;">🛡️</p>
              <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 800;">
                Daily Security Briefing
              </h1>
              <p style="margin: 8px 0 0; color: #8892b0; font-size: 14px;">
                {DATE_STR} ({DAY_KR}요일)
              </p>
            </td>
          </tr>
          <!-- Spacer -->
          <tr><td style="height: 20px;"></td></tr>
          <!-- Cards -->
          {cards_html}
          <!-- Footer -->
          <tr>
            <td style="background-color: #f8f9fb; padding: 20px 24px;
                        text-align: center; border-top: 1px solid #eef0f2;">
              <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                이 뉴스레터는 Claude API 웹 검색을 활용하여 자동 생성되었습니다.
              </p>
              <p style="margin: 4px 0 0; color: #d1d5db; font-size: 10px;">
                Powered by Anthropic Claude · GitHub Actions
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_email(html_content):
    """Gmail API messages.send로 뉴스레터 발송"""
    client = GmailApiClient(
        GmailOAuthCredentials(
            client_id=GMAIL_CLIENT_ID,
            client_secret=GMAIL_CLIENT_SECRET,
            refresh_token=GMAIL_REFRESH_TOKEN,
        )
    )
    subject = f"[데일리 보안 브리핑] {DATE_STR}"
    message_id = client.send_html(
        sender=GMAIL_USER,
        recipients=TO_EMAILS,
        subject=subject,
        html_content=html_content,
        plain_content=(
            f"{subject}\n\n"
            "HTML을 지원하는 메일 클라이언트에서 카드형 뉴스레터를 확인해 주세요."
        ),
    )

    print(
        f"Gmail API send confirmed: message_id={message_id}, "
        f"recipients={len(TO_EMAILS)}"
    )
    return message_id


def main():
    print(f"Collecting security news for {DATE_STR}...")
    data = collect_news()

    total = sum(len(s.get("articles", [])) for s in data["sections"])
    print(f"Collected {total} articles across {len(data['sections'])} categories")

    print("Building HTML email...")
    html_content = build_html(data)

    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(exist_ok=True)
    artifact_path = artifact_dir / f"security_newsletter_{DATE_STR}.html"
    artifact_path.write_text(html_content, encoding="utf-8")
    print(f"HTML artifact written: {artifact_path}")

    print("Sending email...")
    message_id = send_email(html_content)

    print(f"Done: Gmail message id {message_id}")


if __name__ == "__main__":
    main()
