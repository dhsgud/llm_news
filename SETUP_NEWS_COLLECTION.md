# 뉴스 수집 기능 설정 가이드

## 빠른 시작

### 1. 백엔드 설정

#### 1.1 News API 키 발급
1. https://newsapi.org/ 방문
2. 무료 계정 생성
3. API 키 복사

#### 1.2 환경 변수 설정
`backend/.env` 파일에 다음 추가:
```bash
NEWS_API_KEY=your_api_key_here
```

#### 1.3 데이터베이스 마이그레이션
```bash
cd backend
python run_news_migration.py
```

#### 1.4 백엔드 서버 시작
```bash
cd backend
python main.py
```

### 2. 프론트엔드 설정

#### 2.1 의존성 설치 (이미 완료된 경우 생략)
```bash
cd frontend
npm install
```

#### 2.2 프론트엔드 서버 시작
```bash
cd frontend
npm run dev
```

### 3. 사용하기

1. 브라우저에서 `http://localhost:5173/news` 접속
2. 수집 설정 조정 (기간, 검색어, 언어)
3. "뉴스 수집 시작" 버튼 클릭
4. 실시간 로그에서 진행 상황 확인
5. 수집된 뉴스 기사 확인

## 주요 기능

### 1. 뉴스 수집
- News API를 통해 최신 금융 뉴스 자동 수집
- 중복 체크로 효율적인 데이터 관리
- 커스터마이징 가능한 검색 쿼리

### 2. 실시간 로그
- 수집 진행 상황 실시간 모니터링
- 에러 및 경고 메시지 표시
- 터미널 스타일의 로그 뷰어

### 3. 감성 분석
- LLM을 사용한 자동 감성 분석
- Positive/Neutral/Negative 분류
- 분석 근거 제공

### 4. 통계 대시보드
- 총 뉴스 기사 수
- 감성 분석 완료 현황
- 감성 분포 시각화

## API 엔드포인트

### 뉴스 수집
```
POST /api/news/collect?days=7&query=finance&language=en
```

### 로그 조회
```
GET /api/news/logs?limit=100
```

### 뉴스 기사 조회
```
GET /api/news/articles?limit=50&days=7
```

### 통계 조회
```
GET /api/news/stats?days=7
```

## 트러블슈팅

### "No articles fetched" 오류
- News API 키가 올바른지 확인
- 일일 요청 제한 (무료: 100개) 확인

### 감성 분석 실패
- LLM 서버 실행 확인: `http://localhost:8080`
- `backend/config.py`의 `LLAMA_CPP_URL` 설정 확인

### 데이터베이스 오류
- 마이그레이션 실행 확인
- 데이터베이스 파일 권한 확인

## 기존 방식과의 차이

### 기존 (collect_news.bat)
```bash
# 커맨드 라인에서 실행
cd backend
python collect_news.py --days 7
```

### 새로운 방식 (프론트엔드 버튼)
1. 브라우저에서 버튼 클릭
2. 실시간 로그 확인
3. 수집된 뉴스 즉시 확인

## 장점

✅ **사용 편의성**: 커맨드 라인 없이 버튼 클릭만으로 실행
✅ **실시간 모니터링**: 수집 진행 상황을 실시간으로 확인
✅ **시각화**: 수집된 뉴스와 통계를 한눈에 확인
✅ **접근성**: 웹 브라우저만 있으면 어디서든 사용 가능

## 다음 단계

- 자동 스케줄링 설정 (매일 자동 수집)
- 알림 기능 추가
- 더 많은 뉴스 소스 통합
- 감성 분석 결과 시각화 개선
