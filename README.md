# CHZZK 스트리밍 매니저 (Chzzk Streaming Manager)

치지직(CHZZK) 스트리밍 플랫폼의 채팅을 AI 에이전트를 통해 관리하고 분석하는 프로젝트입니다.

## 기술 스택
- Python 3.11
- LangChain & LangGraph: AI 에이전트 구현
- PostgreSQL: 데이터베이스
- Redis: 캐싱 및 메시지 브로커
- Selenium: 웹 크롤링
- PyTorch: 머신러닝 기능

## 프로젝트 구조
```
.
├── Agent/              # 핵심 기능 구현
│   ├── app.py         # 메인 애플리케이션 로직
│   ├── crawler.py     # 채팅 크롤링 구현
│   ├── broker.py      # 데이터 중개
│   ├── db_helper.py   # 데이터베이스 연동
│   └── ...
├── Utils/             # 유틸리티 기능
│   ├── logger.py      # 로깅 기능
│   └── graph_viewer.py # 그래프 시각화
└── main.py            # 프로그램 진입점
```

## 주요 기능

### 1. 채팅 관리 시스템
- 실시간 채팅 크롤링
  - 웹 소켓 분석 (향후 구현 예정)
- 후원 기능 모니터링
- 유저별 데이터 DB 적재
- 크롤러 -> Broker -> AI Agent 파이프라인

### 2. AI 에이전트 기능
- LangGraph 기반 에이전트 구현
- 유저 정보 분석
  - 최근 채팅 내역 조회
  - 유저 채팅 성향 분석
  - 채팅 내역 요약 (최근 N일)
  - 후원 내역 분석

### 3. 컨텍스트 제공
- 나무위키 검색 및 정보 제공
  - 본문 추출 및 가공
  - LLM 기반 답변 생성

### 4. 유저 관리 시스템 (개발 예정)
- 채팅 규칙 위반 모니터링
- 자동 경고 시스템
- 치지직 API 연동 (킥/밴 기능 - API 제공 시)

### 5. 품질 관리
- 질문-답변 적절성 평가 시스템
- 에이전트 응답 품질 모니터링

## 설치 및 실행
```bash
# Poetry를 사용한 의존성 설치
poetry install

# 프로그램 실행
poetry run python main.py
```

## 환경 설정
프로젝트 실행을 위해 다음 환경 변수가 필요합니다:
- DB 접속 정보
- Redis 설정
- API 키 (필요한 경우)

## 개발자
- kr-MATAGI (dev_matagi@kakao.com)