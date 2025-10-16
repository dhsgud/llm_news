# Docker로 Market Sentiment Analyzer 실행하기

## 🚀 빠른 시작

### 0. 사전 준비

AI 서버(Ollama 등)가 호스트 머신에서 실행 중이어야 합니다:

```bash
# Ollama가 11434 포트에서 실행 중인지 확인
curl http://localhost:11434/api/tags
```

### 1. Docker 컨테이너 실행

```bash
# 모든 서비스 빌드 및 시작
docker-compose up -d

# 또는 빌드 강제 재실행
docker-compose up -d --build
```

### 2. 접속

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Redis**: localhost:6379

### 3. 중지 및 제거

```bash
# 컨테이너 중지
docker-compose stop

# 컨테이너 중지 및 제거
docker-compose down

# 컨테이너, 볼륨, 이미지 모두 제거 (완전 초기화)
docker-compose down -v --rmi all
```

## 📋 주요 명령어

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis
```

### 서비스 재시작

```bash
# 모든 서비스 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend
docker-compose restart frontend
```

### 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 상세 정보
docker-compose ps -a
```

### 컨테이너 내부 접속

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# Frontend 컨테이너 접속
docker-compose exec frontend sh

# Redis CLI 접속
docker-compose exec redis redis-cli
```

## 🔧 환경 설정

### Backend 환경 변수

`docker-compose.yml`의 `backend.environment` 섹션에서 설정:

```yaml
environment:
  - DATABASE_URL=sqlite:///./market_analyzer.db
  - REDIS_URL=redis://redis:6379/0
  - REDIS_ENABLED=true
  - DEBUG=false
  - LLAMA_CPP_BASE_URL=http://host.docker.internal:11434  # AI 서버 주소
```

**중요**: `host.docker.internal`은 Docker 컨테이너에서 호스트 머신을 가리킵니다.
- Windows/Mac: 자동 지원
- Linux: `extra_hosts` 설정 필요 (이미 docker-compose.yml에 포함됨)

또는 `.env` 파일 사용:

```bash
# backend/.env 파일 생성
cp backend/.env.social.example backend/.env
# 필요한 값 수정
```

그리고 `docker-compose.yml`에서:

```yaml
backend:
  env_file:
    - ./backend/.env
```

### Frontend 환경 변수

`docker-compose.yml`의 `frontend.environment` 섹션에서 설정:

```yaml
environment:
  - VITE_API_URL=http://localhost:8000
```

## 🛠️ 개발 모드

개발 중에는 코드 변경 시 자동 재시작되도록 볼륨 마운트 사용:

```yaml
backend:
  volumes:
    - ./backend:/app
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 데이터 관리

### 데이터 백업

```bash
# 데이터베이스 백업
docker-compose exec backend cp /app/market_analyzer.db /app/data/backup.db

# 호스트로 복사
docker cp market-analyzer-backend:/app/data/backup.db ./backup.db
```

### 데이터 초기화

```bash
# 볼륨 삭제 (모든 데이터 삭제)
docker-compose down -v

# 다시 시작
docker-compose up -d
```

## 🐛 트러블슈팅

### 포트 충돌

다른 서비스가 포트를 사용 중이면 `docker-compose.yml`에서 포트 변경:

```yaml
backend:
  ports:
    - "8001:8000"  # 호스트:컨테이너

frontend:
  ports:
    - "3001:3000"
```

### 빌드 캐시 문제

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 재시작
docker-compose up -d
```

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 컨테이너 상태 확인
docker-compose ps
```

### 네트워크 문제

```bash
# 네트워크 재생성
docker-compose down
docker network prune
docker-compose up -d
```

## 🔒 프로덕션 배포

프로덕션 환경에서는:

1. `.env` 파일에 실제 API 키 설정
2. `DEBUG=false` 설정
3. PostgreSQL 사용 권장
4. HTTPS 설정 (Nginx 리버스 프록시)
5. 로그 모니터링 설정

```yaml
# docker-compose.prod.yml 예시
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/market_analyzer
      - DEBUG=false
      - LOG_LEVEL=WARNING
```

실행:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📈 성능 최적화

### 리소스 제한

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### 헬스체크

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## 🎯 유용한 팁

1. **빠른 재시작**: `docker-compose restart backend` (빌드 없이)
2. **로그 실시간 확인**: `docker-compose logs -f --tail=100`
3. **특정 서비스만 실행**: `docker-compose up -d backend redis`
4. **리소스 사용량 확인**: `docker stats`
5. **이미지 크기 확인**: `docker images | grep market-analyzer`

## 📞 문제 해결

문제가 발생하면:

1. 로그 확인: `docker-compose logs -f`
2. 컨테이너 상태: `docker-compose ps`
3. 네트워크 확인: `docker network ls`
4. 볼륨 확인: `docker volume ls`
5. 완전 초기화: `docker-compose down -v && docker-compose up -d --build`
