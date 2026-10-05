"""
꿈 해몽 데이터 검사기

    python3 tools/dreams/validate.py                     # data/*.json 전부
    python3 tools/dreams/validate.py tools/dreams/data/g3.json

항목 형식 (data/<group>.json = 항목 배열)
{
  "slug": "pig",                       # catalog.json 의 slug 그대로
  "title": "돼지꿈",                    # catalog.json 의 title 그대로
  "aliases": ["돼지 꿈", ...],          # 검색어 3~8개 (title과 다른 표현)
  "verdict": "good" | "mixed" | "caution",
  "summary": "...",                    # 60~130자, 검색 결과 설명문
  "traditional": "...",                # 전통 해몽 200~420자
  "psychology": "...",                 # 심리로 보면 150~330자
  "taemong": "..." | null,             # 태몽 해석 60~200자 (태몽으로 흔한 꿈만, 아니면 null)
  "cases": [                           # 상황별 해몽 5~7개
    {"title": "돼지가 집에 들어오는 꿈", "verdict": "good", "text": "60~180자"}
  ],
  "advice": "...",                     # 이 꿈을 꿨다면 50~150자
  "related": ["gold", "money"]         # 다른 꿈 slug 3~6개 (catalog에 있는 것만, 자기 자신 제외)
}
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / 'catalog.json').read_text(encoding='utf-8'))
BY_SLUG = {d['slug']: d for d in CATALOG['dreams']}
VERDICTS = {'good', 'mixed', 'caution'}

BANNED = ['반드시', '틀림없이', '100%', '무조건', '자살', '자해', '죽고 싶', '살인 방법',
          '진단', '처방', '복용', '확실히 당첨', '꼭 사세요', '대출']


def n(s):
    return len(re.sub(r'\s+', ' ', s or '').strip())


def check_entry(e, errors, warns):
    slug = e.get('slug')
    where = f'[{slug}]'
    if slug not in BY_SLUG:
        errors.append(f'{where} catalog에 없는 slug')
        return
    cat = BY_SLUG[slug]
    if e.get('title') != cat['title']:
        errors.append(f"{where} title이 catalog와 다름: {e.get('title')!r} != {cat['title']!r}")

    al = e.get('aliases') or []
    if not (3 <= len(al) <= 8):
        errors.append(f'{where} aliases 3~8개 (현재 {len(al)})')
    if len(set(al)) != len(al):
        errors.append(f'{where} aliases 중복')

    if e.get('verdict') not in VERDICTS:
        errors.append(f"{where} verdict 값 오류: {e.get('verdict')!r}")

    for field, lo, hi in (('summary', 60, 130), ('traditional', 200, 420),
                          ('psychology', 150, 330), ('advice', 50, 150)):
        L = n(e.get(field))
        if not (lo <= L <= hi):
            errors.append(f'{where} {field} 길이 {L}자 (허용 {lo}~{hi})')

    tm = e.get('taemong')
    if tm is not None and not (60 <= n(tm) <= 200):
        errors.append(f'{where} taemong 길이 {n(tm)}자 (60~200 또는 null)')

    cases = e.get('cases') or []
    if not (5 <= len(cases) <= 7):
        errors.append(f'{where} cases 5~7개 (현재 {len(cases)})')
    titles = set()
    for i, c in enumerate(cases):
        t = c.get('title', '')
        if not t.endswith('꿈'):
            errors.append(f'{where} cases[{i}] title은 "꿈"으로 끝나야 함: {t!r}')
        if t in titles:
            errors.append(f'{where} cases[{i}] title 중복: {t!r}')
        titles.add(t)
        if c.get('verdict') not in VERDICTS:
            errors.append(f'{where} cases[{i}] verdict 오류')
        L = n(c.get('text'))
        if not (60 <= L <= 180):
            errors.append(f'{where} cases[{i}] text 길이 {L}자 (60~180)')

    rel = e.get('related') or []
    if not (3 <= len(rel) <= 6):
        errors.append(f'{where} related 3~6개 (현재 {len(rel)})')
    for r in rel:
        if r not in BY_SLUG:
            errors.append(f'{where} related에 없는 slug: {r!r}')
        if r == slug:
            errors.append(f'{where} related에 자기 자신')

    texts = [e.get(f) or '' for f in ('summary', 'traditional', 'psychology', 'advice', 'taemong')]
    texts += [c.get('text', '') + ' ' + c.get('title', '') for c in cases]
    blob = ' '.join(texts) + ' ' + ' '.join(al)
    for w in BANNED:
        if w in blob:
            errors.append(f'{where} 금지 표현 포함: {w!r}')
    if re.search(r'[A-Za-z]{3,}', blob):
        warns.append(f'{where} 본문에 영문 단어가 있음')

    for field in ('summary', 'traditional', 'psychology', 'advice'):
        txt = (e.get(field) or '').strip()
        if txt and not txt.endswith(('요.', '요!', '요?')):
            warns.append(f'{where} {field} 끝이 해요체(…요.)가 아님')


def main(paths):
    if not paths:
        paths = sorted((HERE / 'data').glob('*.json'))
    errors, warns = [], []
    seen = {}
    total = 0
    for p in map(Path, paths):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception as ex:
            errors.append(f'{p.name}: JSON 오류 — {ex}')
            continue
        if not isinstance(data, list):
            errors.append(f'{p.name}: 최상위는 배열이어야 함')
            continue
        for e in data:
            total += 1
            s = e.get('slug')
            if s in seen:
                errors.append(f'[{s}] 중복 항목 ({seen[s]}, {p.name})')
            seen[s] = p.name
            check_entry(e, errors, warns)
    print(f'항목 {total}개 검사')
    for w in warns:
        print('경고:', w)
    for e in errors:
        print('오류:', e)
    print('통과' if not errors else f'오류 {len(errors)}건')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
