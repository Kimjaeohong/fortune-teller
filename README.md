# 🔮 홍스팟 운세 (fortune.hongspot.com)

매일 자정(한국시간) 바뀌는 12띠 운세 · 별자리 운세 + 이름 궁합 · 타로 · 행운의 로또 번호 사이트입니다.
GitHub Pages로 호스팅하고, 운세 데이터는 구글 스프레드시트에서 읽어옵니다.

## 구성

| 파일 | 역할 |
|------|------|
| `index.html` / `script.js` | 메인 — 12띠 카드, 내 띠 찾기 |
| `star.html` / `star.js` | 별자리 목록 — 오늘의 순위, 생일로 내 별자리 찾기 |
| `detail.html` / `star-detail.html` / `detail.js` | 띠·별자리 상세 (공용 스크립트) — 5개 카테고리, 행운 아이템 |
| `tarot.html` / `tarot.js` / `tarot-data.js` | 타로 (78장, 8가지 스프레드) |
| `name.html` / `name.js` | 이름 궁합 — 번갈아 쓰기·획수·숫자 피라미드, 양방향 결과 |
| `lotto.html` / `lotto.js` | 행운의 로또 번호 — 운세 기준(하루 고정)·무작위, 포함·제외 번호, 기록 |
| `config.js` | 스프레드시트 ID, 카카오 키, 띠·카테고리 정의 |
| `common.js` | 공통 — 한국시간 날짜, 데이터 로딩, 별점, 공유 |
| `styles.css` | 전체 디자인 |
| `privacy.html` | 개인정보처리방침 (애드센스 안내 포함) |
| `404.html` | 없는 주소로 들어왔을 때 안내 페이지 |
| `robots.txt` / `sitemap.xml` | 검색엔진 등록용 |
| `data/*.json` | 날짜별 띠 운세 데이터 (12띠 × 5카테고리 + 별점) |
| `data/star/*.json` | 날짜별 별자리 운세 데이터 |
| `tools/build_fortunes.py` | 문장 풀 조합으로 데이터 생성 (API 비용 없음) |
| `generate_fortune.py` | (선택) Claude API로 특정 날짜를 AI 문장으로 생성 |
| `.github/workflows/daily-fortune.yml` | 운세 생성 (수동 실행, 예약 실행은 꺼져 있음) |

## 데이터 흐름

1. **1순위: `data/YYYY-MM-DD.json`** — 사이트와 함께 배포되는 날짜별 파일 (현재 2026-01-01 ~ 2028-12-31)
2. 오늘 파일이 없으면 최근 3년 안의 **같은 월·일** 파일로 대신 표시
3. 그래도 없으면 **구글 시트**(`fortune_data`)에서 해당 날짜 행만 조회 (예전 방식, 백업용)

한 번 받은 데이터는 세션 동안 캐시됩니다.

### 데이터 다시 만들기 (API 비용 없음)

`tools/fortune_phrases.py`의 문장 풀을 조합해 만듭니다.
같은 날 띠끼리 같은 문장을 쓰지 않고, 같은 띠는 400일 안에 같은 운세가 반복되지 않습니다.

```bash
python3 tools/build_fortunes.py --start 2028-01-01 --end 2028-12-31              # 띠
python3 tools/build_fortunes.py --kind star --start 2028-01-01 --end 2028-12-31  # 별자리 (띠 먼저)
```

별자리는 같은 날 띠 운세에 쓰인 문장을 피해서 고르므로, 띠 데이터를 먼저 만든 뒤 돌리세요.

문장을 추가·수정한 뒤 다시 돌리면 됩니다. 시드가 고정이라 결과는 항상 같습니다.

## AI로 생성하기 (선택)

API 비용 때문에 **매일 자동 실행은 꺼 두었습니다.** 기본은 위의 무료 생성기로 운영하고, 필요할 때만 수동으로 실행하세요.

GitHub 저장소 Settings → Secrets 에 `ANTHROPIC_API_KEY`가 필요합니다.
결과는 `data/` 폴더에 커밋됩니다. (시트에도 쓰려면 로컬에서 `--sheet` 옵션 + 서비스 계정 필요)

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
