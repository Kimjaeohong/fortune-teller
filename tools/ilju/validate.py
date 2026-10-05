"""
일주 60가지 본문 검사기

    python3 tools/ilju/validate.py                     # data/*.json 전부
    python3 tools/ilju/validate.py tools/ilju/data/g2.json

항목 형식 (data/<group>.json = 항목 배열)
{
  "name": "병오",                  # catalog.json 의 name 그대로
  "image": "...",                 # 자연 이미지 8~24자 (예: 한낮 하늘 꼭대기의 태양)
  "keywords": ["...", ...],       # 성격 키워드 5개, 각 2~6자
  "summary": "...",               # 70~130자, 검색 결과 설명문
  "personality": "...",           # 300~480자
  "strengths": ["...", ...],      # 4개, 각 25~60자
  "cautions": ["...", ...],       # 3개, 각 25~60자
  "love": "...",                  # 160~300자
  "work": "...",                  # 160~300자
  "money": "...",                 # 120~250자
  "match": "...",                 # 100~220자 — catalog 의 hap_partner 일주 이름을 꼭 넣을 것
  "friction": "...",              # 100~220자 — catalog 의 chung_partner 일주 이름을 꼭 넣을 것
  "advice": "..."                 # 60~150자, 이 일주에게 건네는 한마디
}
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = {x['name']: x for x in json.loads((HERE / 'catalog.json').read_text(encoding='utf-8'))['ilju']}
BANNED = ['반드시', '틀림없이', '무조건', '100%', '운명적으로 정해', '이혼', '사별', '단명', '자살', '질병에 걸',
          '여자는', '남자는', '여자라면', '남자라면']
FIELDS = [('image', 8, 24), ('summary', 70, 130), ('personality', 300, 480), ('love', 160, 300),
          ('work', 160, 300), ('money', 120, 250), ('match', 100, 220), ('friction', 100, 220), ('advice', 60, 150)]


def n(s):
    return len(re.sub(r'\s+', ' ', s or '').strip())


def check(e, errors, warns):
    name = e.get('name')
    w = f'[{name}]'
    if name not in CATALOG:
        errors.append(f'{w} catalog에 없는 일주')
        return
    c = CATALOG[name]
    for f, lo, hi in FIELDS:
        L = n(e.get(f))
        if not lo <= L <= hi:
            errors.append(f'{w} {f} 길이 {L}자 (허용 {lo}~{hi})')
    kw = e.get('keywords') or []
    if len(kw) != 5 or any(not 2 <= len(k) <= 6 for k in kw):
        errors.append(f'{w} keywords 5개, 각 2~6자')
    for f, cnt in (('strengths', 4), ('cautions', 3)):
        items = e.get(f) or []
        if len(items) != cnt:
            errors.append(f'{w} {f} {cnt}개여야 함 (현재 {len(items)})')
        for t in items:
            if not 25 <= n(t) <= 60:
                errors.append(f'{w} {f} 항목 길이 {n(t)}자 (25~60)')
            if not t.strip().endswith('요.'):
                errors.append(f'{w} {f} 항목이 "요."로 끝나지 않음')
    if c['hap_partner'] not in (e.get('match') or ''):
        errors.append(f"{w} match 에 {c['hap_partner']} 이 없음")
    if c['chung_partner'] not in (e.get('friction') or ''):
        errors.append(f"{w} friction 에 {c['chung_partner']} 이 없음")
    blob = ' '.join(str(e.get(f, '')) for f, _, _ in FIELDS) + ' '.join(e.get('strengths', []) + e.get('cautions', []))
    for b in BANNED:
        if b in blob:
            errors.append(f'{w} 금지 표현: {b!r}')
    if re.search(r'[A-Za-z]{3,}', blob):
        errors.append(f'{w} 영문 단어 포함')
    for f in ('summary', 'personality', 'love', 'work', 'money', 'match', 'friction', 'advice'):
        if not (e.get(f) or '').strip().endswith(('요.', '요!')):
            warns.append(f'{w} {f} 끝이 해요체가 아님')


def main(paths):
    paths = paths or sorted((HERE / 'data').glob('*.json'))
    errors, warns, seen = [], [], set()
    for p in map(Path, paths):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception as ex:
            errors.append(f'{p.name}: JSON 오류 {ex}')
            continue
        for e in data:
            if e.get('name') in seen:
                errors.append(f"[{e.get('name')}] 중복")
            seen.add(e.get('name'))
            check(e, errors, warns)
    print(f'항목 {len(seen)}개 검사')
    for x in warns:
        print('경고:', x)
    for x in errors:
        print('오류:', x)
    print('통과' if not errors else f'오류 {len(errors)}건')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
