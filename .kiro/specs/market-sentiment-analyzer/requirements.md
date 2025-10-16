# Requirements Document

## Introduction

이 프로젝트는 Apriel-1.5-15b-Thinker-Q8_0.gguf 모델을 활용하여 금융, 시장, 주식, 코인 관련 뉴스를 분석하고 감성(긍정/부정)을 판단하는 웹 애플리케이션입니다. 최근 일주일간의 뉴스를 자동으로 수집하고 분석하여, 사용자가 버튼 한 번으로 당일 투자 결정을 위한 보수적인 매수/매도 비율 추천을 받을 수 있습니다.

핵심 목표는 복잡한 시장 분석 과정을 자동화하고, 사용자에게 직관적이고 실행 가능한 투자 신호를 제공하는 것입니다. 향후 증권사 API 연동을 통한 실시간 거래 정보 수집과 자동 매매 시스템으로 확장 가능하도록 설계됩니다.

## Requirements

### Requirement 1: 뉴스 데이터 수집 및 관리

**User Story:** 시스템 관리자로서, 최근 7일간의 금융 뉴스를 자동으로 수집하고 저장하여 분석에 활용할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 시스템이 실행되면 THEN 시스템은 매일 자정에 자동으로 뉴스 수집 작업을 실행해야 합니다
2. WHEN 뉴스 수집이 실행되면 THEN 시스템은 최근 7일간의 금융, 주식, 코인 관련 뉴스를 뉴스 API로부터 가져와야 합니다
3. WHEN 뉴스가 수집되면 THEN 시스템은 각 뉴스 기사의 제목, 본문, 발행일, 출처를 데이터베이스에 저장해야 합니다
4. IF 뉴스 API 호출이 실패하면 THEN 시스템은 오류를 로깅하고 다음 스케줄된 시간에 재시도해야 합니다
5. WHEN 8일 이상 된 뉴스가 있으면 THEN 시스템은 자동으로 해당 데이터를 삭제하여 7일 윈도우를 유지해야 합니다

### Requirement 2: LLM 기반 개별 뉴스 감성 분석

**User Story:** 분석 시스템으로서, 각 뉴스 기사를 Apriel-1.5-15b-Thinker 모델로 분석하여 긍정/부정/중립 감성을 판단하고 근거를 추출할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 개별 뉴스 기사가 분석 요청되면 THEN 시스템은 Ollama 서버의 Apriel-1.5-15b-Thinker-Q8_0.gguf 모델에 1단계 프롬프트를 전송해야 합니다
2. WHEN 1단계 프롬프트가 실행되면 THEN 모델은 "Positive", "Negative", "Neutral" 중 하나의 감성과 판단 근거를 JSON 형식으로 반환해야 합니다
3. WHEN 감성 분석 결과가 반환되면 THEN 시스템은 감성을 정량화된 점수(Positive: +1.0, Neutral: 0.0, Negative: -1.0)로 변환해야 합니다
4. IF 부정적 감성이 판단되면 THEN 시스템은 보수적 가중치(1.5배)를 적용하여 점수를 -1.5로 조정해야 합니다
5. WHEN 분석이 완료되면 THEN 시스템은 감성 점수와 근거를 데이터베이스에 저장해야 합니다
6. WHEN 1단계 분석이 실행되면 THEN 시스템은 Reasoning: medium 레벨로 모델을 호출하여 효율성을 최적화해야 합니다

### Requirement 3: 주간 시장 동향 종합 분석

**User Story:** 분석 시스템으로서, 일주일간의 개별 뉴스 감성 데이터를 종합하여 전반적인 시장 동향과 핵심 동인을 파악할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 사용자가 분석을 요청하면 THEN 시스템은 최근 7일간의 모든 감성 분석 결과를 데이터베이스에서 조회해야 합니다
2. WHEN 감성 데이터가 조회되면 THEN 시스템은 2단계 프롬프트를 사용하여 주간 동향 요약을 생성해야 합니다
3. WHEN 2단계 프롬프트가 실행되면 THEN 모델은 전반적인 시장 감성, 핵심 동인, 주요 패턴을 텍스트로 요약해야 합니다
4. WHEN 동향 요약이 생성되면 THEN 시스템은 결과를 캐시에 저장하여 중복 분석을 방지해야 합니다

### Requirement 4: 보수적 투자 추천 생성

**User Story:** 투자자로서, 주간 뉴스 동향과 시장 변동성을 기반으로 보수적인 매수/매도 비율 추천을 받아 투자 결정에 참고할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 3단계 추천 생성이 실행되면 THEN 시스템은 2단계의 동향 요약과 현재 VIX 지수를 입력으로 사용해야 합니다
2. WHEN VIX 데이터가 필요하면 THEN 시스템은 외부 API에서 최신 VIX 값을 가져와 0-1 범위로 정규화해야 합니다
3. WHEN 주간 신호 점수를 계산하면 THEN 시스템은 각 일일 감성 점수에 (1 + VIX_Normalized) 가중치를 적용하여 합산해야 합니다
4. WHEN 원시 신호 점수가 계산되면 THEN 시스템은 시그모이드 함수 또는 이동 창 정규화를 사용하여 0-100 범위의 매수/매도 비율로 변환해야 합니다
5. WHEN 3단계 프롬프트가 실행되면 THEN 시스템은 Reasoning: high 레벨로 모델을 호출하여 깊은 추론을 수행해야 합니다
6. WHEN 최종 비율이 생성되면 THEN 시스템은 0-30은 "강력 매도", 31-70은 "중립", 71-100은 "강력 매수"로 해석 가능해야 합니다
7. IF 부정적 뉴스가 많거나 VIX가 높으면 THEN 시스템은 더 보수적인(낮은) 비율을 생성해야 합니다

### Requirement 5: llama.cpp 서버 통합

**User Story:** 개발자로서, Python 백엔드에서 로컬 llama.cpp 서버의 Apriel-1.5-15b-Thinker 모델과 안정적으로 통신할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 시스템이 시작되면 THEN llama.cpp 서버가 localhost:8080에서 실행 중이어야 합니다
2. WHEN LLM 추론이 필요하면 THEN 시스템은 HTTP POST 요청을 llama.cpp의 /completion 엔드포인트로 전송해야 합니다
3. WHEN API 요청을 보내면 THEN 요청 본문에 prompt, temperature, max_tokens 등의 파라미터를 JSON 형식으로 포함해야 합니다
4. IF llama.cpp 서버 응답이 실패하면 THEN 시스템은 오류를 처리하고 사용자에게 적절한 에러 메시지를 반환해야 합니다
5. WHEN 응답이 수신되면 THEN 시스템은 JSON 응답에서 'content' 키의 값을 추출하여 파싱해야 합니다
6. WHEN 서버가 시작되면 THEN Apriel-1.5-15b-Thinker-Q8_0.gguf 모델이 로드되어 있어야 합니다

### Requirement 6: Python 백엔드 API 서비스

**User Story:** 프론트엔드 개발자로서, RESTful API를 통해 분석 요청을 보내고 결과를 JSON 형식으로 받을 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 백엔드 서버가 시작되면 THEN FastAPI 또는 Flask 프레임워크가 실행되어야 합니다
2. WHEN 프론트엔드가 POST /analyze 엔드포인트를 호출하면 THEN 시스템은 최신 매수/매도 비율과 동향 요약을 반환해야 합니다
3. WHEN /analyze 요청이 처리되면 THEN 응답은 { "buy_sell_ratio": number, "trend_summary": string, "last_updated": timestamp } 형식이어야 합니다
4. WHEN 백그라운드 작업이 실행되면 THEN APScheduler가 뉴스 수집과 감성 분석을 주기적으로 실행해야 합니다
5. IF 분석 중 오류가 발생하면 THEN 시스템은 적절한 HTTP 상태 코드(500)와 에러 메시지를 반환해야 합니다
6. WHEN CORS 설정이 필요하면 THEN 백엔드는 프론트엔드 도메인의 요청을 허용해야 합니다

### Requirement 7: 웹 프론트엔드 UI

**User Story:** 투자자로서, 직관적인 웹 인터페이스에서 버튼 한 번으로 시장 분석 결과를 확인할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 사용자가 웹 페이지에 접속하면 THEN 중앙에 "Analyze Market" 버튼이 표시되어야 합니다
2. WHEN 사용자가 버튼을 클릭하면 THEN 시스템은 백엔드 /analyze API를 호출하고 로딩 인디케이터를 표시해야 합니다
3. WHEN 분석 결과가 반환되면 THEN 매수/매도 비율이 큰 숫자와 원형 게이지 차트로 표시되어야 합니다
4. WHEN 게이지가 표시되면 THEN 색상은 비율에 따라 동적으로 변해야 합니다 (0-30: 빨강, 31-70: 노랑, 71-100: 초록)
5. WHEN 결과가 표시되면 THEN 동향 요약 텍스트가 비율 아래에 간결하게 표시되어야 합니다
6. WHEN 사용자가 추가 정보를 원하면 THEN 접이식 패널을 열어 7일간의 일일 감성 점수 막대 차트를 볼 수 있어야 합니다
7. WHEN 페이지가 로드되면 THEN 마지막 분석 시간이 헤더에 표시되어야 합니다
8. WHEN 다양한 디바이스에서 접속하면 THEN UI는 반응형으로 작동하여 모바일, 태블릿, 데스크톱에서 모두 사용 가능해야 합니다

### Requirement 8: 데이터 저장 및 캐싱

**User Story:** 시스템 관리자로서, 뉴스 데이터와 분석 결과를 효율적으로 저장하고 조회할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 시스템이 초기화되면 THEN SQLite 또는 PostgreSQL 데이터베이스가 생성되어야 합니다
2. WHEN 데이터베이스가 생성되면 THEN news_articles, sentiment_analysis, analysis_cache 테이블이 존재해야 합니다
3. WHEN 뉴스가 저장되면 THEN news_articles 테이블에 id, title, content, published_date, source 컬럼이 포함되어야 합니다
4. WHEN 감성 분석이 저장되면 THEN sentiment_analysis 테이블에 article_id, sentiment, score, reasoning, analyzed_date가 포함되어야 합니다
5. WHEN 분석 결과가 캐시되면 THEN analysis_cache 테이블에 cache_key, result_json, created_at이 저장되어야 합니다
6. WHEN 캐시된 결과가 1시간 이상 지났으면 THEN 시스템은 캐시를 무효화하고 새로운 분석을 수행해야 합니다

### Requirement 9: 프롬프트 엔지니어링 구현

**User Story:** AI 엔지니어로서, 3단계 프롬프트 체인을 체계적으로 구현하여 정확한 감성 분석과 보수적 추천을 생성할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 1단계 프롬프트가 생성되면 THEN "당신은 금융 분석가입니다" 역할 정의와 JSON 출력 형식 지정이 포함되어야 합니다
2. WHEN 2단계 프롬프트가 생성되면 THEN "당신은 시장 전략가입니다" 역할과 패턴 식별 지시가 포함되어야 합니다
3. WHEN 3단계 프롬프트가 생성되면 THEN "보수적이고 리스크 회피적인 포트폴리오 매니저" 역할과 부정적 뉴스 가중 지시가 명시되어야 합니다
4. WHEN 각 프롬프트가 실행되면 THEN 시스템 메시지와 사용자 메시지가 명확히 구분되어 전송되어야 합니다
5. WHEN 프롬프트 템플릿이 저장되면 THEN 코드에서 쉽게 수정 가능한 형태로 관리되어야 합니다

### Requirement 10: 에러 처리 및 로깅

**User Story:** 시스템 관리자로서, 시스템 오류를 추적하고 디버깅할 수 있도록 상세한 로그를 확인할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 시스템이 시작되면 THEN Python logging 모듈이 설정되어 로그 파일에 기록해야 합니다
2. WHEN API 호출이 실패하면 THEN 오류 메시지, 스택 트레이스, 타임스탬프가 로그에 기록되어야 합니다
3. WHEN 중요한 작업이 실행되면 THEN INFO 레벨 로그가 기록되어야 합니다 (예: "뉴스 수집 시작", "분석 완료")
4. IF 데이터베이스 연결이 실패하면 THEN 시스템은 재시도 로직을 실행하고 실패 횟수를 로깅해야 합니다
5. WHEN 프론트엔드에서 오류가 발생하면 THEN 사용자에게 친화적인 에러 메시지가 표시되어야 합니다

### Requirement 11: 증권사 API 연동 및 실시간 거래 데이터 수집

**User Story:** 투자자로서, 증권사 API를 통해 실시간 주식 거래 정보와 종목 가격을 수집하여 로컬 데이터베이스에 저장하고 분석에 활용할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 시스템이 증권사 API와 연동되면 THEN 한국투자증권, 키움증권 등의 API 인증이 완료되어야 합니다
2. WHEN 실시간 데이터 수집이 시작되면 THEN 시스템은 주요 종목의 현재가, 거래량, 시가, 고가, 저가를 주기적으로 가져와야 합니다
3. WHEN 종목 데이터가 수집되면 THEN 로컬 데이터베이스의 stock_prices 테이블에 종목코드, 가격정보, 타임스탬프가 저장되어야 합니다
4. WHEN 특정 종목이 선택되면 THEN 시스템은 해당 종목과 연관된 뉴스를 필터링하여 표시해야 합니다
5. WHEN 종목별 뉴스가 분석되면 THEN 각 종목에 대한 개별 감성 점수와 매수/매도 추천이 생성되어야 합니다
6. WHEN 거래 정보가 수집되면 THEN 시스템은 내 계좌의 보유 종목, 수량, 평균 매입가를 데이터베이스에 동기화해야 합니다
7. IF API 호출 한도에 도달하면 THEN 시스템은 요청을 큐에 저장하고 다음 가능한 시간에 재시도해야 합니다

### Requirement 12: 자동 매매 시스템

**User Story:** 투자자로서, 축적된 데이터와 AI 분석을 기반으로 자동으로 주식을 매수/매도하여 수동 개입 없이 투자를 실행할 수 있기를 원합니다.

#### Acceptance Criteria

1. WHEN 자동 매매 기능이 활성화되면 THEN 사용자는 최대 투자 금액, 리스크 레벨, 거래 가능 시간대를 설정할 수 있어야 합니다
2. WHEN 매수 신호가 생성되면 THEN 시스템은 설정된 리스크 레벨과 매수/매도 비율을 기반으로 거래 여부를 자동 판단해야 합니다
3. IF 매수/매도 비율이 80 이상이고 리스크가 낮으면 THEN 시스템은 증권사 API를 통해 자동으로 매수 주문을 실행해야 합니다
4. IF 매수/매도 비율이 20 이하이고 보유 종목이 있으면 THEN 시스템은 자동으로 매도 주문을 실행해야 합니다
5. WHEN 자동 거래가 실행되면 THEN 거래 내역(종목, 수량, 가격, 시간, 사유)이 데이터베이스에 기록되어야 합니다
6. WHEN 거래가 완료되면 THEN 사용자에게 알림(이메일, 푸시 등)이 전송되어야 합니다
7. WHEN 손실이 설정된 임계값을 초과하면 THEN 시스템은 자동으로 손절매를 실행하고 자동 매매를 일시 중지해야 합니다
8. WHEN 사용자가 자동 매매 대시보드에 접속하면 THEN 실행된 거래 내역, 수익률, 현재 포지션을 시각화하여 표시해야 합니다
9. IF 시장이 비정상적으로 변동하면 THEN 시스템은 안전 모드로 전환하고 모든 자동 거래를 중단해야 합니다
10. WHEN 충분한 거래 데이터가 축적되면 THEN 시스템은 과거 거래 패턴을 학습하여 매매 전략을 개선해야 합니다
