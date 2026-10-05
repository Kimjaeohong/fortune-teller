# 🔮 홍스팟 운세 (fortune.hongspot.com)

매일 자정(한국시간) 바뀌는 12띠 운세 · 사주 일진 · 띠별 투자운 · 별자리 운세 + 꿈해몽 사전 · 이름 궁합 · 타로 · 행운의 로또 번호 사이트입니다.
GitHub Pages로 호스팅하고, 운세 데이터는 구글 스프레드시트에서 읽어옵니다.

## 구성

| 파일 | 역할 |
|------|------|
| `index.html` / `script.js` | 메인 — 12띠 카드, 내 띠 찾기 |
| `ilgan.html` / `ilgan.js` | 사주 일진 — 생년월일 → 일주 계산, 오늘 일진과의 십신·합충으로 하루 운세, 7일 흐름, 일간 10가지 오늘 순위 (데이터 파일 없이 날짜로 계산, 기한 없음) |
| `ilgan/<key>.html` · `ilgan-data.js` | 일간 10가지 소개 페이지와 문장 데이터 (생성기가 만듦, 직접 고치지 말 것) |
| `invest.html` / `invest.js` | 오늘의 투자운 — 12띠 카드, 순위, 띠별 상세(매매 분위기·행운의 섹터·시간대·팁·주의) |
| `star.html` / `star.js` | 별자리 목록 — 오늘의 순위, 생일로 내 별자리 찾기 |
| `detail.html` / `star-detail.html` / `detail.js` | 띠·별자리 상세 (공용 스크립트) — 5개 카테고리, 행운 아이템 |
| `dream/index.html` · `dream/<slug>.html` | 꿈해몽 사전 — 메인(검색·분류별 목록) + 꿈 하나당 정적 페이지 189개 (생성기가 만듦, 직접 고치지 말 것) |
| `dream/dream.js` | 꿈해몽 검색·공유 스크립트 |
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
| `data/invest/*.json` | 날짜별 투자운 데이터 (12띠 × 매매 분위기·문장·팁·주의·섹터·시간대·키워드, 휴장일 표시) |
| `tools/build_fortunes.py` | 문장 풀 조합으로 띠·별자리 데이터 생성 (API 비용 없음) |
| `tools/build_ilgan.py` · `tools/ilgan/*.json` | 사주 일진 문장 데이터·일간 페이지 생성기 |
| `tools/build_dreams.py` | 꿈해몽 페이지 생성기 — `tools/dreams/` 의 글로 `dream/*.html` 과 사이트맵 꿈 구간을 다시 만듦 |
| `tools/dreams/catalog.json` · `data/*.json` · `validate.py` | 꿈 목록(분류·작성 메모), 꿈별 본문, 형식 검사기 |
| `tools/build_invest.py` / `tools/invest_phrases.py` | 투자운 데이터 생성 (띠 데이터의 재물운 점수와 연동, 휴장일 달력 포함) |
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
python3 tools/build_fortunes.py --start 2026-01-01 --end 2029-12-31              # 띠
python3 tools/build_fortunes.py --kind star --start 2026-01-01 --end 2029-12-31  # 별자리 (띠 먼저)
```

별자리는 같은 날 띠 운세에 쓰인 문장을 피해서 고르므로, 띠 데이터를 먼저 만든 뒤 돌리세요.

기간을 늘릴 때는 **항상 2026-01-01부터** 새 종료일까지 한 번에 돌리세요.
시드가 고정이라 앞쪽 날짜는 그대로 유지되고 뒤에 새 날짜만 붙습니다.
(새 해만 따로 돌리면 "400일 안에 반복 금지" 규칙이 연도 경계에서 끊깁니다.)

투자운은 같은 날 띠 운세의 **재물운 별점**을 읽어 매매 분위기를 정하므로, 역시 띠 데이터 다음에 돌리세요.

```bash
python3 tools/build_invest.py --start 2026-01-01 --end 2028-12-31
```

휴장일(주말·공휴일·대체공휴일·설/추석 연휴·근로자의 날·선거일·연말 휴장)은 `tools/build_invest.py` 안의 달력으로 판단합니다.
새 해를 추가할 때는 그 해의 음력 공휴일(설·추석·부처님오신날)과 선거일을 `LUNAR_HOLIDAYS`, `ELECTION_DAYS`에 넣어 주세요.

문장을 추가·수정한 뒤 다시 돌리면 됩니다. 문장 하나를 자리에서 고치기만 하면 그 문장만 바뀝니다.

### 사주 일진 고치기

- 일간 성격 소개: `tools/ilgan/profiles.json`, 십신별 하루 문장·합충 문장: `tools/ilgan/sipsin.json`
- 고친 뒤 `python3 tools/build_ilgan.py` → `ilgan-data.js`, `ilgan/*.html`, 사이트맵 일간 구간이 다시 만들어져요
- 일주 계산은 율리우스 적일 기준 (JDN + 49) mod 60 (0 = 갑자). 1949-10-01 갑자일, 2026-05-01 을해일로 검증했어요
- 점수·카테고리 기울기는 `ilgan.js` 의 `ILGAN_SCORE` 에서 조정

### 꿈해몽 고치기·추가하기

1. 글 고치기: `tools/dreams/data/*.json` 에서 해당 꿈을 고친다
2. 꿈 추가: `tools/dreams/catalog.json` 에 slug·제목·분류를 넣고, `data/` 아래 아무 파일에 같은 형식으로 본문을 넣는다 (형식은 `validate.py` 맨 위 설명 참고)
3. 검사 후 페이지 다시 만들기:

```bash
python3 tools/dreams/validate.py
python3 tools/build_dreams.py
```

`dream/*.html` 과 `sitemap.xml` 의 꿈 구간(`<!-- dream:start -->` ~ `<!-- dream:end -->`)은 생성기가 덮어쓰니 직접 고치지 마세요.
꿈마다 나오는 행운 번호는 slug로 정해지는 고정값이고, '로또 번호 뽑기' 버튼은 `lotto.html#inc=…&from=…` 로 앞 3개 번호를 포함 번호로 넘깁니다.

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
