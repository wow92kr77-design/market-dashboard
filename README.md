# 국내증시 AI 터미널

오늘 한국증시에서 돈이 어디로 흐르는지 30초 만에 보기 위한 Bloomberg Lite 스타일 Streamlit 대시보드입니다.

## 주요 기능

- KOSPI, KOSDAQ, USD/KRW, Nasdaq, S&P500, Nikkei, Shanghai, Bitcoin, WTI, VIX 지표 카드
- OpenAI API 키가 있으면 GPT 시장요약, 없으면 룰 기반 요약
- 테마별 대표 종목 평균 수익률 기반 히트맵과 TOP10 점수
- 외국인/기관 순매수 TOP20, 프로그램 매매 연결 준비 UI
- 뉴스 RSS, 중요도 별점, 테마 태그, 예상 수혜주 엔진
- DART API 연동 구조와 공시 호재/악재/중립 분류
- 경제일정, 위험도 게이지, 시장 자금 흐름 Sankey
- 관심종목 영향 분석, CSV/HTML 리포트 다운로드

## 설치

```bash
cd market_dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux는 가상환경 활성화 명령만 다릅니다.

```bash
source .venv/bin/activate
```

## 실행

```bash
streamlit run app.py
```

브라우저가 열리면 첫 화면에서 바로 대시보드가 표시됩니다. 외부 데이터 연결이 실패해도 샘플 데이터로 화면이 정상 작동합니다.

## API 키 설정

`.env.example`을 복사해서 `.env`를 만듭니다.

```bash
copy .env.example .env
```

설정 가능한 값:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
DART_API_KEY=your_dart_api_key
USE_LIVE_DATA=false
```

- `OPENAI_API_KEY`가 없으면 룰 기반 시장요약을 사용합니다.
- `DART_API_KEY`가 없으면 공시 영역에 샘플 데이터와 안내 문구가 표시됩니다.
- `USE_LIVE_DATA=true`로 두면 yfinance/pykrx 실시간 데이터 호출을 우선 시도합니다.
- `USE_LIVE_DATA=false`로 두면 네트워크가 없어도 샘플 데이터로 빠르게 표시됩니다.

## 데이터 수정

- `data/themes.csv`: 테마, 관련 종목, 키워드를 관리합니다.
- `data/watchlist.csv`: 관심종목/보유종목을 관리합니다.

종목은 `|`로 구분합니다.

```csv
theme,stocks,keywords
전력기기,"HD현대일렉트릭|LS ELECTRIC|효성중공업","전력기기|변압기|전선"
```

## Streamlit Cloud 배포

1. 이 폴더를 GitHub 저장소에 업로드합니다.
2. Streamlit Cloud에서 New app을 누릅니다.
3. Repository와 branch를 선택합니다.
4. Main file path에 `app.py`를 입력합니다.
5. Advanced settings의 Secrets에 API 키를 넣습니다.

Streamlit Cloud Secrets 예시:

```toml
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_MODEL = "gpt-4o-mini"
DART_API_KEY = "your_dart_api_key"
USE_LIVE_DATA = "true"
```

## 연결 TODO

- pykrx 종목명-티커 매핑을 확장해 국내 개별 종목 실시간 수익률 정확도 개선
- KRX 프로그램 매매 데이터 연결
- 경제일정 API 연결
- PDF 직접 생성 기능 추가

## 주의

이 앱은 시장 흐름 파악을 위한 보조 도구입니다. 투자 판단의 최종 책임은 사용자에게 있습니다.
