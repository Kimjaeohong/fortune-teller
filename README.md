# 🔮 홍스팟 운세 (fortune.hongspot.com)

매일 자정(한국시간) 바뀌는 12띠 운세 + 타로 사이트입니다.
GitHub Pages로 호스팅하고, 운세 데이터는 구글 스프레드시트에서 읽어옵니다.

## 구성

| 파일 | 역할 |
|------|------|
| `index.html` / `script.js` | 메인 — 12띠 카드, 내 띠 찾기 |
| `detail.html` / `detail.js` | 띠별 상세 — 5개 카테고리, 행운 아이템 |
| `tarot.html` / `tarot.js` / `tarot-data.js` | 타로 (78장, 8가지 스프레드) |
| `config.js` | 스프레드시트 ID, 카카오 키, 띠·카테고리 정의 |
| `common.js` | 공통 — 한국시간 날짜, 데이터 로딩, 별점, 공유 |
| `styles.css` | 전체 디자인 |
| `generate_fortune.py` | Claude API로 운세 생성 → 시트 기록 |
| `.github/workflows/daily-fortune.yml` | 운세 생성 (수동 실행, 예약 실행은 꺼져 있음) |

## 데이터 흐름

1. 시트 `fortune_data` 에 `date | zodiac | category | content` 형식으로 저장
2. 페이지는 **오늘 날짜 60행만** 구글 시각화 쿼리(gviz)로 조회 → 세션 동안 캐시
3. 오늘 데이터가 없으면 **같은 월·일의 가장 최근 데이터**로 대신 표시 (연말 공백 대비)

시트는 "링크가 있는 모든 사용자 · 뷰어"로 공유되어 있어야 합니다.
형식은 [SPREADSHEET_GUIDE.md](SPREADSHEET_GUIDE.md) 참고.

## 운세 생성 (선택)

API 비용 때문에 **매일 자동 실행은 꺼 두었습니다.** 시트에 미리 채워둔 데이터로 운영하고, 필요할 때만 수동으로 생성하세요.

GitHub 저장소 Settings → Secrets 에 아래 값이 필요합니다.

- `ANTHROPIC_API_KEY` — Claude API 키
- `SPREADSHEET_ID` — 시트 ID
- `GOOGLE_CREDENTIALS` — 서비스 계정 JSON 전체 (시트에 편집자로 공유)

모델은 기본 `claude-haiku-4-5-20251001`이며, Settings → Variables 에 `FORTUNE_MODEL`을 넣으면 바꿀 수 있습니다.

한꺼번에 채우고 싶을 때는 Actions → Daily Fortune Generator → Run workflow 에서
시작 날짜와 일수를 입력하세요. (예: `2027-01-01`, `31`)

로컬 실행:

```bash
pip install -r requirements.txt
python generate_fortune.py --date 2027-01-01 --days 7
```

## 로컬 미리보기

```bash
python3 -m http.server 8000
# http://localhost:8000
```
