# 주식 디스코드 봇

PyCord를 사용한 커스텀 주식 거래 디스코드 봇입니다. 사용자들이 가상 주식을 매수/매수하고 시세 변동을 통해 수익을 낼 수 있습니다.

## 기능

### 유저 명령어
- **주식매수**: 주식을 구매합니다
- **주식매도**: 보유한 주식을 판매합니다
- **시세**: 모든 주식의 현재 가격 및 상세 변동률 정보를 확인합니다 (초기가 대비, 이전가 대비, 최고가/최저가, 거래량)
- **내프로필**: 보유 현금과 주식, 총 자산을 확인합니다
- **주식그래프**: 주식 가격 그래프를 확인합니다
- **거래내역**: 내 거래 내역을 확인합니다
- **상세변동률**: 주식의 상세 변동률을 시간대별로 확인합니다 (1분, 5분, 10분, 30분, 1시간, 6시간, 12시간, 1일, 1주)

### 관리자 명령어
- **주식제작**: 새로운 주식을 생성합니다 (관리자 전용)
- **주식삭제**: 주식을 삭제합니다 (관리자 전용)
- **주식변동**: 주식 가격을 즉시 변경합니다 (관리자 전용)

### 웹 대시보드
- **Discord OAuth2 로그인**: Discord 계정으로 안전하게 로그인
- **실시간 자산 확인**: 보유 현금, 주식 가치, 총 자산 실시간 확인
- **주식 가격 그래프**: Plotly를 사용한 인터랙티브 가격 차트
- **상세 변동률 분석**: 초기가 대비, 이전가 대비 변동률
- **전체 시장 현황**: 모든 주식의 실시간 가격 및 변동률
- **거래 내역**: 최근 거래 내역 확인
- **30초 자동 새로고침**: 실시간 데이터 업데이트

## 주요 특징

- ✅ 슬래시 명령어 지원
- ✅ 자동 주식 가격 변동 시스템
- ✅ 입력 검증 (음수, 소수점 방지)
- ✅ 잔액 및 보유 주식 확인
- ✅ 관리자 권한 확인
- ✅ SQLite 데이터베이스 사용
- ✅ 가격 히스토리 저장 및 분석
- ✅ 거래량 추적
- ✅ 최고가/최저가 기록
- ✅ matplotlib 기반 디스코드 그래프
- ✅ Flask 기반 웹 대시보드
- ✅ Discord OAuth2 인증
- ✅ Plotly 인터랙티브 차트

## 로컬 설치 및 실행

### 1. 필수 요구사항
- Python 3.11 이상
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications)에서 발급)

### 2. 설치 단계

```bash
# 프로젝트 디렉토리로 이동
cd stock-discord-bot

# 가상 환경 생성 (선택사항)
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (Mac/Linux)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 봇 토큰 설정

`bot.py` 파일에서 `TOKEN` 변수에 봇 토큰을 입력하세요:

```python
TOKEN = "YOUR_BOT_TOKEN_HERE"  # 여기에 봇 토큰을 입력
```

또는 환경 변수로 설정:

```bash
# Windows (PowerShell)
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"

# Windows (CMD)
set DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE

# Mac/Linux
export DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
```

### 4. 관리자 ID 설정 (선택사항)

특정 유저만 관리자 명령어를 사용하도록 하려면 `bot.py`에서 `ADMIN_IDS`를 설정하세요:

```python
ADMIN_IDS = [123456789012345678, 987654321098765432]  # 관리자 Discord ID 목록
```

또는 환경 변수로 설정:

```bash
export ADMIN_IDS="123456789012345678,987654321098765432"
```

설정하지 않을 경우 서버 관리자 권한이 있는 모든 유저가 관리자 명령어를 사용할 수 있습니다.

### 5. 봇 실행

```bash
python bot.py
```

### 6. Discord 봇 초대

봇을 서버에 초대하려면 Discord Developer Portal에서 OAuth2 URL Generator를 사용하거나 다음 권한으로 초대 링크를 생성하세요:
- bot
- applications.commands

## Discloud 배포

### 1. Discloud 계정 및 프로젝트 생성

1. [Discloud](https://discloud.app)에 로그인
2. 대시보드에서 새 프로젝트 생성
3. 프로젝트 유형: "Bot" 선택

### 2. 환경 변수 설정

Discloud 프로젝트 설정에서 다음 환경 변수를 추가하세요:

- `DISCORD_TOKEN`: 봇 토큰
- `ADMIN_IDS`: (선택사항) 관리자 ID 목록 (쉼표로 구분)

### 3. 파일 업로드

Discloud CLI를 사용하여 업로드:

```bash
# Discloud CLI 설치
npm install -g discloud

# 로그인
discloud login

# 프로젝트 업로드
discloud upload
```

또는 Discloud 웹 대시보드에서 파일을 직접 업로드할 수 있습니다.

### 4. 배포 시작

업로드가 완료되면 Discloud 대시보드에서 "Start" 버튼을 클릭하여 봇을 시작하세요.

### 5. 로그 확인

Discloud 대시보드의 "Logs" 탭에서 봇 실행 로그를 확인할 수 있습니다.

## 주식 생성 예시

관리자로 다음 명령어를 사용하여 주식을 생성하세요:

```
/주식제작 이름:삼성전자 주당가격:50000 최저상승률:-5 최대상승률:5 시세변화주기:300
```

이 명령어는 다음 설정으로 삼성전자 주식을 생성합니다:
- 초기 가격: 50,000원
- 가격 변동 범위: -5% ~ +5%
- 가격 변동 주기: 300초 (5분)

## 데이터베이스

봇은 SQLite 데이터베이스를 사용합니다:
- `stock_bot.db` 파일이 자동 생성됩니다
- 유저 정보, 주식 정보, 보유 주식, 가격 히스토리, 거래 내역이 저장됩니다
- Discloud 배포 시 데이터베이스는 서버에 저장됩니다

## 웹 대시보드 설치 및 실행

### 1. Discord OAuth2 애플리케이션 설정

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 애플리케이션 생성 또는 선택
2. OAuth2 탭에서 Redirect URI 추가:
   - 로컬: `http://localhost:5000/callback`
   - 배포: `https://your-domain.com/callback`
3. OAuth2 탭에서 Client ID와 Client Secret 복사

### 2. 웹 대시보드 설치

```bash
cd web

# 가상 환경 생성 (선택사항)
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (Mac/Linux)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# Windows (PowerShell)
$env:FLASK_SECRET_KEY="your-secret-key"
$env:DISCORD_CLIENT_ID="your-client-id"
$env:DISCORD_CLIENT_SECRET="your-client-secret"
$env:DISCORD_REDIRECT_URI="http://localhost:5000/callback"

# Windows (CMD)
set FLASK_SECRET_KEY=your-secret-key
set DISCORD_CLIENT_ID=your-client-id
set DISCORD_CLIENT_SECRET=your-client-secret
set DISCORD_REDIRECT_URI=http://localhost:5000/callback

# Mac/Linux
export FLASK_SECRET_KEY="your-secret-key"
export DISCORD_CLIENT_ID="your-client-id"
export DISCORD_CLIENT_SECRET="your-client-secret"
export DISCORD_REDIRECT_URI="http://localhost:5000/callback"
```

### 4. 웹 대시보드 실행

```bash
python app.py
```

웹 브라우저에서 `http://localhost:5000` 접속

### 5. 웹 대시보드 배포 (Railway/Render)

Railway 또는 Render에 배포할 때:
- Python 버전: 3.11
- Start Command: `cd web && python app.py`
- 환경 변수 설정 (위와 동일)
- 데이터베이스 파일이 공유되도록 설정

## 주의사항

- 주식 매수/매수 시 수량은 정수만 가능합니다 (소수점 불가)
- 음수 수량으로 거래할 수 없습니다
- 보유한 금액보다 많은 주식을 구매할 수 없습니다
- 보유한 주식보다 많은 주식을 판매할 수 없습니다
- 주식 가격은 최소 1원으로 유지됩니다

## 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.
