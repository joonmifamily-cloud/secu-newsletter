# Daily Security Newsletter

매일 아침 7시(KST)에 자동으로 보안 뉴스를 수집하여 이메일로 발송하는 시스템입니다.

## 구성

- **Claude API** (web search) — 뉴스 수집 및 요약
- **GitHub Actions** — 매일 자동 실행 (cron)
- **Gmail SMTP** — 이메일 발송

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

### 2. Gmail 앱 비밀번호 발급

1. Google 계정 → 보안 → 2단계 인증 활성화
2. Google 계정 → 보안 → 앱 비밀번호 → "메일" 선택 → 생성
3. 16자리 비밀번호 복사

### 3. GitHub Secrets 등록

저장소 → Settings → Secrets and variables → Actions → New repository secret:

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `GMAIL_USER` | Gmail 주소 (예: user@gmail.com) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (16자리) |
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
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export TO_EMAILS="recipient@example.com"

python send_newsletter.py
```

## 비용

- **GitHub Actions**: 공개 저장소 무료
- **Claude API**: 하루 1회 실행 기준 월 $1~3 수준
