# Daily Security Newsletter

매일 아침 7시(KST)에 자동으로 보안 뉴스를 수집하여 이메일로 발송하는 시스템입니다.

## 구성

- **Claude API** (web search) — 뉴스 수집 및 요약
- **GitHub Actions** — 매일 자동 실행 (cron)
- **Gmail API** (`users.messages.send`) — OAuth 2.0 오프라인 권한으로 이메일 발송

## 카테고리

| 구분 | 내용 |
|------|------|
| 🔴 주요 보안 뉴스 | 침해사고, 취약점, 해킹 |
| 🟠 정책·규제 동향 | 각국 보안 정책, 법규 |
| 🔵 보안 기술 동향 | 신기술, 위협 연구, AI 보안 |
| 🟢 솔루션·제품 동향 | 제품 출시, M&A, 시장 |

## 설정 방법

### 1. Anthropic API 키 발급

- https://console.anthropic.com 에서 API 키 생성

### 2. Gmail API OAuth 설정

1. Google Cloud 프로젝트에서 Gmail API를 활성화합니다.
2. OAuth 동의 화면을 구성하고 `joonmi.family@gmail.com`을 테스트 사용자로 추가합니다.
3. 데스크톱 앱 OAuth 클라이언트를 생성합니다.
4. `https://www.googleapis.com/auth/gmail.send` 범위로 오프라인 동의를 받아 refresh token을 생성합니다.
5. client id, client secret, refresh token은 GitHub Actions Secrets에만 저장합니다.

### 3. GitHub Secrets 등록

저장소 → Settings → Secrets and variables → Actions → New repository secret:

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `GMAIL_USER` | Gmail 주소 (예: user@gmail.com) |
| `GMAIL_CLIENT_ID` | Google OAuth 클라이언트 ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth 클라이언트 보안 비밀 |
| `GMAIL_REFRESH_TOKEN` | `gmail.send` 범위의 오프라인 refresh token |
| `TO_EMAILS` | 수신자 이메일 (쉼표로 구분, 예: `a@x.com,b@y.com`) |

### 4. 저장소 Push

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

공개 저장소로 설정하면 GitHub Actions 무료입니다.

## 수동 실행

GitHub → Actions → "Daily Security Newsletter" → Run workflow

## 로컬 테스트

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-..."
export GMAIL_USER="your@gmail.com"
export GMAIL_CLIENT_ID="...apps.googleusercontent.com"
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."
export TO_EMAILS="recipient@example.com"

python send_newsletter.py
```

## 비용

- **GitHub Actions**: 공개 저장소 무료
- **Claude API**: 하루 1회 실행 기준 월 $1~3 수준
