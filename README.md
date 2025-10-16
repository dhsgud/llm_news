# 📈 Market Analyzer

뉴스 기반 시장 감성 분석 및 자동 매매 시스템입니다. LLM을 활용해 뉴스 데이터를 분석하고, 실시간 시장 동향을 파악하여 투자 인사이트를 제공합니다.

## 주요 기능

- **뉴스 수집 및 감성 분석**: 실시간 뉴스를 수집하고 LLM으로 시장 감성 분석
- **주식 데이터 추적**: 실시간 주가 데이터 수집 및 저장
- **자동 매매**: 설정한 전략에 따른 자동 매매 실행
- **백테스팅**: 과거 데이터로 매매 전략 검증
- **대시보드**: React 기반 실시간 모니터링 UI

## 기술 스택

### Backend
- FastAPI - 고성능 비동기 API 서버
- SQLAlchemy - ORM 및 데이터베이스 관리
- Redis - 캐싱 및 세션 관리
- APScheduler - 주기적 데이터 수집

### Frontend
- React 19 - UI 프레임워크
- Vite - 빌드 도구
- TailwindCSS - 스타일링
- Chart.js - 데이터 시각화

## 시작하기

### 필수 요구사항

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Docker로 실행 (권장)

```bash
# 저장소 클론
git clone https://github.com/dhsgud/llm_news.git
cd llm_news

# 환경 변수 설정
cp backend/.env.kiwoom.example backend/.env

# Docker Compose로 실행
docker-compose up -d
```

서비스 접속:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 로컬 개발 환경

#### Backend

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

## 환경 변수 설정

`backend/.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# Database
DATABASE_URL=sqlite:///./market_analyzer.db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# API Keys (선택사항)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Kiwoom API (Windows 전용)
KIWOOM_ACCOUNT=your_account_number
```

## 뉴스 수집

뉴스 데이터를 수집하려면:

```bash
# Windows
collect_news.bat

# Linux/Mac
./collect_news.sh
```

또는 Python 스크립트 직접 실행:

```bash
cd backend
python collect_news.py
```

## API 엔드포인트

주요 API 엔드포인트:

- `GET /api/market/sentiment` - 시장 감성 분석 결과
- `GET /api/stock/prices/{symbol}` - 특정 종목 가격 데이터
- `POST /api/trading/start` - 자동 매매 시작
- `GET /api/trading/status` - 매매 상태 조회
- `GET /api/news/latest` - 최신 뉴스 목록

자세한 API 문서는 http://localhost:8000/docs 에서 확인하세요.

## 프로젝트 구조

```
.
├── backend/              # FastAPI 백엔드
│   ├── api/             # API 라우터
│   ├── models/          # 데이터베이스 모델
│   ├── services/        # 비즈니스 로직
│   └── tests/           # 테스트 코드
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # UI 컴포넌트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   └── services/    # API 클라이언트
│   └── public/
└── docker-compose.yml   # Docker 설정
```

## 테스트

```bash
# Backend 테스트
cd backend
pytest

# Frontend 테스트
cd frontend
npm test
```

## 주의사항

- 키움증권 API는 Windows 환경에서만 동작합니다
- 실제 매매 전에 반드시 백테스팅으로 전략을 검증하세요
- API 키는 절대 공개 저장소에 커밋하지 마세요

## 라이선스

MIT License

## 기여

이슈나 PR은 언제든 환영합니다!
