# Implementation Plan

## Phase 1: Core Infrastructure & Basic Analysis

- [x] 1. 프로젝트 구조 및 환경 설정





  - 백엔드 디렉토리 구조 생성 (app/, models/, services/, api/)
  - requirements.txt 작성 (FastAPI, SQLAlchemy, Pydantic, requests, APScheduler)
  - .env.example 파일 생성
  - 기본 설정 파일 (config.py) 작성
  - _Requirements: 6.1, 6.2_

- [x] 2. 데이터베이스 설정 및 모델 정의






- [x] 2.1 데이터베이스 연결 설정

  - SQLAlchemy 엔진 및 세션 설정
  - PostgreSQL/SQLite 연결 구성
  - _Requirements: 8.1, 8.2_


- [x] 2.2 기본 테이블 모델 구현

  - NewsArticle, SentimentAnalysis, AnalysisCache 모델 작성
  - Pydantic 스키마 정의
  - Alembic 마이그레이션 초기화
  - _Requirements: 8.3, 8.4_

- [x] 3. llama.cpp 클라이언트 구현






- [x] 3.1 LlamaCppClient 클래스 작성

  - HTTP 클라이언트 설정 (requests 라이브러리)
  - /completion 엔드포인트 연동
  - 에러 처리 및 재시도 로직
  - _Requirements: 5.1, 5.2, 5.3, 5.4_


- [x] 3.2 프롬프트 템플릿 정의

  - 1단계: 개별 기사 분석 프롬프트
  - 2단계: 주간 동향 종합 프롬프트
  - 3단계: 보수적 추천 프롬프트
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 3.3 llama.cpp 통합 테스트






  - Mock 응답으로 단위 테스트
  - 실제 서버 연동 테스트
  - _Requirements: 5.5_

- [x] 4. 뉴스 수집 모듈 구현






- [x] 4.1 NewsAPIClient 클래스 작성

  - News API 연동 (예: NewsAPI.org)
  - 금융 뉴스 필터링 로직
  - 날짜 범위 쿼리 구현
  - _Requirements: 1.2, 1.3_

- [x] 4.2 NewsScheduler 구현


  - APScheduler 설정
  - 매일 자정 뉴스 수집 작업 스케줄링
  - 7일 이상 된 뉴스 자동 삭제
  - _Requirements: 1.1, 1.4, 1.5_

- [x] 4.3 뉴스 수집 테스트






  - Mock API 응답으로 테스트
  - 데이터베이스 저장 검증
  - _Requirements: 1.3_

- [x] 5. 감성 분석 모듈 구현






- [x] 5.1 SentimentAnalyzer 클래스 작성

  - 개별 기사 분석 메서드
  - JSON 응답 파싱
  - 감성 점수 정량화 (Positive: +1.0, Negative: -1.5, Neutral: 0.0)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_


- [x] 5.2 배치 분석 기능 구현

  - 여러 기사 동시 분석
  - 데이터베이스 저장 로직
  - _Requirements: 2.5_

- [x] 5.3 감성 분석 단위 테스트






  - 프롬프트 생성 테스트
  - 점수 계산 검증
  - _Requirements: 2.2, 2.3_


- [x] 6. 신호 생성 모듈 구현





- [x] 6.1 SentimentQuantifier 클래스 작성


  - 감성 정량화 로직
  - 일일 감성 점수 계산
  - 보수적 가중치 적용
  - _Requirements: 2.3, 2.4_


- [x] 6.2 VIXFetcher 클래스 작성


  - VIX API 연동 (예: Alpha Vantage, Yahoo Finance)
  - VIX 정규화 (0-1 범위)
  - _Requirements: 4.2_


- [x] 6.3 SignalCalculator 클래스 작성


  - 주간 신호 점수 계산 공식 구현
  - 시그모이드 정규화 함수
  - 0-100 범위 매수/매도 비율 변환
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 6.4 신호 계산 테스트






  - 알려진 입력값으로 출력 검증
  - 보수적 가중치 효과 확인
  - _Requirements: 4.6, 4.7_

- [x] 7. 동향 종합 분석 모듈 구현




- [x] 7.1 TrendAggregator 클래스 작성


  - 7일간 감성 데이터 집계
  - 2단계 프롬프트 실행
  - 동향 요약 텍스트 생성
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 7.2 RecommendationEngine 클래스 작성


  - 3단계 프롬프트 실행
  - VIX와 동향 요약 통합
  - 최종 추천 생성
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 7.3 캐싱 로직 구현


  - 분석 결과 캐시 저장
  - 1시간 만료 로직
  - _Requirements: 3.4, 8.5, 8.6_

- [x] 8. FastAPI 백엔드 서버 구축




- [x] 8.1 기본 FastAPI 앱 설정


  - 앱 초기화 및 CORS 설정
  - 라우터 구조 설정
  - 미들웨어 설정
  - _Requirements: 6.1, 6.6_

- [x] 8.2 시장 분석 API 엔드포인트 구현

  - POST /api/analyze 구현
  - GET /api/news 구현
  - GET /api/sentiment/daily 구현
  - _Requirements: 6.2, 6.3_

- [x] 8.3 에러 핸들링 및 로깅

  - 커스텀 예외 클래스 정의
  - 전역 예외 핸들러 설정
  - 로깅 설정 (파일 + 콘솔)
  - _Requirements: 6.5, 10.1, 10.2, 10.3_
-

- [x] 8.4 API 엔드포인트 통합 테스트





  - 각 엔드포인트 요청/응답 테스트
  - 에러 케이스 검증
  - _Requirements: 6.2, 6.3_

## Phase 2: Frontend & User Interface

- [x] 9. React 프론트엔드 프로젝트 설정











  - Vite + React 프로젝트 초기화
  - Tailwind CSS 설정
  - Chart.js 설치
  - 기본 라우팅 설정
  - _Requirements: 7.1_

- [x] 10. 시장 분석 대시보드 UI 구현




- [x] 10.1 메인 레이아웃 컴포넌트


  - 헤더 (앱 이름, 마지막 업데이트 시간)
  - 메인 컨테이너
  - 반응형 디자인 적용
  - _Requirements: 7.7, 7.8_

- [x] 10.2 분석 버튼 및 로딩 상태


  - "Analyze Market" 버튼 컴포넌트
  - 로딩 인디케이터
  - API 호출 로직
  - _Requirements: 7.1, 7.2_

- [x] 10.3 결과 표시 컴포넌트


  - 매수/매도 비율 숫자 표시
  - 원형 게이지 차트 (Chart.js)
  - 동적 색상 변경 (0-30: 빨강, 31-70: 노랑, 71-100: 초록)
  - 동향 요약 텍스트 표시
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 10.4 추가 정보 패널


  - 접이식 패널 구현
  - 7일간 일일 감성 점수 막대 차트
  - _Requirements: 7.6_

- [x] 10.5 프론트엔드 컴포넌트 테스트






  - 주요 컴포넌트 렌더링 테스트
  - 사용자 인터랙션 테스트
  - _Requirements: 7.2, 7.3_

- [x] 11. 백엔드-프론트엔드 통합





  - API 클라이언트 함수 작성 (axios)
  - 에러 처리 및 사용자 피드백
  - 환경 변수 설정 (.env)
  - _Requirements: 6.2, 10.5_

## Phase 3: Stock Integration & Real-time Data

- [x] 12. 주식 데이터 테이블 추가







- [x] 12.1 데이터베이스 스키마 확장
  - StockPrice, StockNewsRelation, AccountHolding 테이블 생성
  - 마이그레이션 실행
  - _Requirements: 11.3_


- [x] 12.2 Pydantic 모델 추가

  - StockPrice, Order, TradeResult 스키마 정의
  - _Requirements: 11.3_

- [x] 13. 증권사 API 연동 구현





- [x] 13.1 BrokerageAPIBase 추상 클래스


  - 인증, 가격 조회, 주문 실행 메서드 정의
  - _Requirements: 11.1_

- [x] 13.2 한국투자증권 API 구현


  - KoreaInvestmentAPI 클래스 작성
  - OAuth 인증 구현
  - 실시간 시세 조회
  - 계좌 잔고 조회
  - _Requirements: 11.1, 11.2, 11.6_

- [x] 13.3 키움증권 API 구현 (선택사항)


  - KiwoomAPI 클래스 작성
  - API 연동 로직
  - _Requirements: 11.1_

- [x] 13.4 증권사 API 통합 테스트









  - Mock API로 테스트
  - 실제 API 연동 검증 (테스트 계정)
  - _Requirements: 11.1, 11.7_
-

- [x] 14. 실시간 주식 데이터 수집



- [-] 14.1 StockDataCollector 클래스 작성




  - 주기적 가격 수집 (1분마다)
  - 데이터베이스 저장
  - _Requirements: 11.2, 11.3_

- [x] 14.2 종목별 뉴스 필터링



  - 뉴스-종목 연관 로직
  - 종목별 감성 분석
  - _Requirements: 11.4, 11.5_

- [x] 14.3 계좌 정보 동기화



  - 보유 종목 자동 업데이트
  - 평균 매입가 계산
  - _Requirements: 11.6_

- [x] 15. 주식 관련 API 엔드포인트 추가

  - GET /api/stocks/{symbol} 구현
  - GET /api/stocks/{symbol}/sentiment 구현
  - GET /api/account/holdings 구현
  - POST /api/account/sync 구현 (placeholder)
  - _Requirements: 11.4, 11.5, 11.6_

- [x] 16. 주식 대시보드 UI 구현

- [x] 16.1 종목 검색 및 선택 컴포넌트

  - 종목 검색 입력
  - 종목 리스트 표시
  - _Requirements: 11.4_

- [x] 16.2 종목 상세 정보 표시

  - 현재가, 거래량 표시
  - 종목별 감성 분석 결과
  - 관련 뉴스 목록
  - _Requirements: 11.2, 11.4, 11.5_

- [x] 16.3 보유 종목 포트폴리오 뷰

  - 보유 종목 테이블
  - 수익률 계산 및 표시
  - _Requirements: 11.6_

## Phase 4: Auto Trading System

- [x] 17. 자동 매매 데이터 모델 추가

- [x] 17.1 데이터베이스 스키마 확장

  - TradeHistory, AutoTradeConfig 테이블 생성
  - 마이그레이션 실행
  - _Requirements: 12.5_

- [x] 17.2 Pydantic 모델 추가

  - TradingConfig, Portfolio, Holding 스키마 정의
  - _Requirements: 12.1_


- [x] 18. 리스크 관리 모듈 구현
- [x] 18.1 RiskManager 클래스 작성
  - 거래 검증 로직 (시장 시간, 잔고, 포지션 크기)
  - 포지션 크기 계산
  - 손절매 체크
  - _Requirements: 12.2, 12.7_

- [x] 18.2 안전 메커니즘 구현
  - 일일 손실 한도 체크
  - 비정상 시장 감지 (서킷 브레이커)
  - 긴급 중지 로직
  - _Requirements: 12.9_

- [x] 18.3 리스크 관리 테스트


  - 각 검증 로직 단위 테스트
  - 엣지 케이스 검증
  - _Requirements: 12.2, 12.7_

- [x] 19. 자동 매매 엔진 구현

- [x] 19.1 AutoTradingEngine 클래스 작성
  - 신호 기반 자동 실행 로직
  - 매수 임계값 (80 이상) 체크
  - 매도 임계값 (20 이하) 체크
  - _Requirements: 12.2, 12.3, 12.4_

- [x] 19.2 주문 실행 및 기록
  - 증권사 API를 통한 주문 실행
  - 거래 내역 데이터베이스 저장
  - _Requirements: 12.5_

- [x] 19.3 포지션 모니터링
  - 보유 종목 실시간 모니터링
  - 손절매 자동 실행
  - _Requirements: 12.7_

- [x] 19.4 알림 시스템 구현
  - 거래 완료 알림 (이메일/SMS)
  - 손절매 알림
  - _Requirements: 12.6_

- [x] 19.5 자동 매매 통합 테스트


  - Paper trading 모드로 테스트
  - 전체 플로우 검증
  - _Requirements: 12.2, 12.3, 12.4_

- [x] 20. 자동 매매 API 엔드포인트 구현

  - POST /api/auto-trade/config 구현
  - POST /api/auto-trade/start 구현
  - POST /api/auto-trade/stop 구현
  - GET /api/trades/history 구현
  - _Requirements: 12.1, 12.5, 12.8_

- [x] 21. 자동 매매 대시보드 UI 구현

- [x] 21.1 설정 패널 컴포넌트

  - 최대 투자 금액 입력
  - 리스크 레벨 선택
  - 거래 시간대 설정
  - 손절매 임계값 설정
  - _Requirements: 12.1_

- [x] 21.2 제어 패널 컴포넌트
  - 자동 매매 시작/중지 버튼
  - 현재 상태 표시
  - 긴급 중지 버튼
  - _Requirements: 12.1, 12.9_

- [x] 21.3 거래 내역 및 성과 표시
  - 거래 내역 테이블
  - 수익률 차트
  - 현재 포지션 요약
  - _Requirements: 12.8_

- [x] 21.4 알림 설정 UI
  - 알림 방법 선택 (이메일, SMS)
  - 알림 조건 설정
  - _Requirements: 12.6_

## Phase 5: Advanced Features & Optimization

- [x] 22. 성능 최적화



- [x] 22.1 캐싱 전략 구현


  - Redis 연동 (선택사항)
  - 분석 결과 캐싱 (1시간)
  - 주식 가격 캐싱 (1분)
  - _Requirements: 8.5, 8.6_

- [x] 22.2 데이터베이스 최적화





  - 인덱스 추가 및 최적화
  - 쿼리 성능 개선
  - 오래된 데이터 아카이빙
  - _Requirements: 8.3, 8.4_

- [x] 22.3 LLM 요청 최적화

  - 배치 처리 구현
  - 요청 큐잉
  - _Requirements: 2.1, 3.1_

- [x] 23. 보안 강화

- [x] 23.1 API 인증 구현
  - API 키 기반 인증
  - Rate limiting
  - _Requirements: 6.6_

- [x] 23.2 민감 정보 암호화
  - 증권사 API 자격증명 암호화
  - 환경 변수 관리
  - _Requirements: 11.1_

- [x] 23.3 거래 보안
  - 2FA 구현 (자동 매매 활성화 시)
  - 거래 감사 로그
  - _Requirements: 12.1_

- [x] 24. 모니터링 및 로깅

- [x] 24.1 상세 로깅 구현
  - 구조화된 로깅 (JSON)
  - 로그 레벨별 분리
  - 로그 로테이션
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 24.2 메트릭 수집
  - API 응답 시간
  - LLM 추론 시간
  - 거래 성공률
  - _Requirements: 10.3_

- [x] 24.3 알림 시스템 확장
  - 시스템 오류 알림
  - 성능 저하 알림
  - _Requirements: 10.5_

- [x] 25. 문서화 및 배포 준비

- [x] 25.1 README 작성
  - 프로젝트 개요
  - 설치 가이드
  - 사용 방법
  - API 문서

- [x] 25.2 Docker 설정
  - Dockerfile 작성 (백엔드)
  - docker-compose.yml 작성
  - 환경 변수 설정 가이드

- [x] 25.3 배포 스크립트
  - 데이터베이스 마이그레이션 스크립트
  - 서버 시작 스크립트
  - 헬스 체크 엔드포인트

- [x] 25.4 E2E 테스트


  - 전체 시스템 통합 테스트
  - 사용자 시나리오 테스트

## Phase 6: Machine Learning & Advanced Analytics (Future)


- [x] 26. 거래 데이터 학습 시스템
  - 과거 거래 패턴 분석
  - 성공적인 거래 특징 추출
  - 매매 전략 개선 알고리즘
  - _Requirements: 12.10_

- [x] 27. 백테스팅 프레임워크
  - 과거 데이터로 전략 검증
  - 성과 지표 계산
  - 전략 비교 도구
  - _Requirements: Task 27_


- [x] 28. 다중 자산 지원
  - 암호화폐 API 연동 (CoinGecko)
  - 외환 데이터 수집 (ExchangeRate API)
  - 통합 자산 관리 시스템
  - 포트폴리오 집계 기능
  - _Requirements: Task 28_

- [x] 29. 소셜 감성 분석
  - Twitter/Reddit API 연동
  - 소셜 미디어 감성 분석
  - 뉴스와 소셜 감성 통합
  - 통합 감성 분석 서비스
  - 트렌딩 종목 감지
  - 감성 분기 탐지
