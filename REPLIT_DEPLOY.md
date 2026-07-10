# Replit 배포 가이드

가장 쉽고 빠른 배포 방법입니다.

## 1. Replit 가입 및 프로젝트 생성

1. [replit.com](https://replit.com)에 가입
2. "Create Repl" 클릭
3. "Python" 선택
4. 프로젝트 이름 입력 (예: stock-bot)
5. "Create Repl" 클릭

## 2. 파일 업로드

1. 왼쪽 파일 목록에서 기본 파일 삭제 (main.py 등)
2. 다음 파일들을 순서대로 생성/업로드:
   - `bot.py` (기존 코드 복사)
   - `database.py` (기존 코드 복사)
   - `requirements.txt` (기존 코드 복사)

## 3. 환경 변수 설정

1. 왼쪽에서 "Secrets" (🔒 아이콘) 클릭
2. 다음 시크릿 추가:
   - Key: `DISCORD_TOKEN`
   - Value: 봇 토큰
   - Key: `ADMIN_IDS`
   - Value: `1232824256` (당신의 ID)

## 4. 실행

1. 하단 "Shell" 탭에서 다음 실행:
```bash
pip install -r requirements.txt
python bot.py
```

## 5. 24/7 실행 (Keep Alive)

Replit은 무료 플랜에서 자동으로 꺼질 수 있습니다. 이를 방지하려면:

1. Uptime Robot (uptimerobot.com)에 가입
2. New Monitor 추가
3. Monitor Type: HTTPS
4. URL: Replit 프로젝트 URL (프로젝트 공유 후 URL 확인)
5. Interval: 5 minutes

또는 Replit 내에서 `.replit` 파일에 다음 추가:
```
[run]
run = "python bot.py"
```

## 완료!

이제 봇이 24/7 실행됩니다. 문제가 있으면 Shell 탭의 로그를 확인하세요.
