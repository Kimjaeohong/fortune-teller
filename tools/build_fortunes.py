"""
운세 데이터 생성기 (API 호출 없음, 문장 풀 조합 방식)

    python tools/build_fortunes.py                 # 띠별 운세 → data/
    python tools/build_fortunes.py --kind star     # 별자리 운세 → data/star/ (띠 데이터를 먼저 만든 뒤)

결과: YYYY-MM-DD.json (날짜별 12개 × 5카테고리 + 문장 톤 기반 별점)

규칙
- 같은 날, 같은 카테고리에서 띠끼리 같은 문장을 쓰지 않는다
- 같은 띠는 최근 며칠 안에 쓴 문장을 다시 쓰지 않는다
- 같은 띠에서 두 문장 조합 전체는 1년 넘게 반복하지 않는다
- 별자리는 같은 날 띠별 운세에 쓰인 문장과 겹치지 않게 고른다
- 시드가 고정이라 다시 돌려도 같은 결과가 나온다
"""

import argparse
import json
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import fortune_phrases as P

ZODIACS = ['rat', 'ox', 'tiger', 'rabbit', 'dragon', 'snake',
           'horse', 'sheep', 'monkey', 'rooster', 'dog', 'pig']
CATEGORIES = ['overall', 'money', 'work', 'health', 'relationship']

TONE_WEIGHTS = {
    'overall': {'g': 0.38, 'n': 0.42, 'c': 0.20},
    'other':   {'g': 0.35, 'n': 0.45, 'c': 0.20},
}

S1_RECENCY_DAYS = 10
S2_RECENCY_DAYS = 7
COMBO_RECENCY_DAYS = 400

S1_POOLS = {'overall': P.OVERALL_S1, 'money': P.MONEY_S1, 'work': P.WORK_S1,
            'health': P.HEALTH_S1, 'relationship': P.REL_S1}
S2_POOLS = {'overall': P.OVERALL_S2, 'money': P.MONEY_S2, 'work': P.WORK_S2,
            'health': P.HEALTH_S2, 'relationship': P.REL_S2}


KINDS = {
    'zodiac': dict(keys=ZODIACS, overall_s1=P.OVERALL_S1, traits=P.ZODIAC_TRAITS, seasonal_p=0.22,
                   out='data', seed=20260926, rules=[], upbeat=[]),
    'star':   dict(keys=P.STAR_ORDER, overall_s1=P.STAR_OVERALL_S1, traits=P.STAR_TRAITS, seasonal_p=0.15,
                   out='data/star', seed=20260927,
                   rules=P.STAR_CONFLICT_RULES, upbeat=P.STAR_UPBEAT_MARKERS),
}

# 문장 → 톤(g/n/c) 조회표
TONE_OF = {t: tone for pool in S1_POOLS.values() for tone, lines in pool.items() for t in lines}
TONE_OF.update({t: tone for lines in P.SEASONAL_S1.values() for tone, t in lines})
TONE_OF.update({t: tone for tone, lines in P.STAR_OVERALL_S1.items() for t in lines})
ALL_S1 = sorted(TONE_OF, key=len, reverse=True)


def split_text(text):
    """저장된 운세 문장을 (1문장, 2문장)으로 나눈다"""
    for s1 in ALL_S1:
        if text.startswith(s1 + ' '):
            return s1, text[len(s1) + 1:]
    return None, None


def conflicts(s1, s2, extra_rules=(), extra_upbeat=()):
    """두 문장을 이어 붙였을 때 앞뒤가 안 맞으면 True"""
    for a_words, b_words in list(P.CONFLICT_RULES) + list(extra_rules):
        if any(a in s1 for a in a_words) and any(b in s2 for b in b_words):
            return True
    if TONE_OF.get(s1) == 'c' and any(m in s2 for m in list(P.UPBEAT_MARKERS) + list(extra_upbeat)):
        return True
    return False


def season_of(month):
    return {12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer'}.get(month, 'autumn')


class Builder:
    def __init__(self, kind='zodiac'):
        self.kind = KINDS[kind]
        self.rng = random.Random(self.kind['seed'])
        # last_used[(zodiac, category, slot, text)] = date
        self.last_used = {}

    def _recent(self, key, today, days):
        d = self.last_used.get(key)
        return d is not None and (today - d).days < days

    def _pick(self, candidates, zodiac, cat, slot, today, used_today, recency):
        """오늘 다른 띠가 안 쓴 것 + 이 띠가 최근에 안 쓴 것 중에서 고른다."""
        fresh = [c for c in candidates if c not in used_today
                 and not self._recent((zodiac, cat, slot, c), today, recency)]
        if not fresh:
            fresh = [c for c in candidates if c not in used_today]
        if not fresh:
            return None
        return self.rng.choice(fresh)

    def _pick_any(self, candidates, *args):
        """오늘 이미 쓴 것까지 모두 소진됐을 때의 마지막 대안"""
        return self._pick(candidates, *args) or (self.rng.choice(candidates) if candidates else None)

    def _tone(self, cat):
        w = TONE_WEIGHTS['overall' if cat == 'overall' else 'other']
        return self.rng.choices(list(w), weights=list(w.values()))[0]

    def _score(self, s1):
        """1문장 톤으로 별점 결정: 좋음 4~5, 무난 3, 조심 2 (가끔 1)"""
        tone = TONE_OF.get(s1, 'n')
        if tone == 'g':
            return 5 if self.rng.random() < 0.3 else 4
        if tone == 'c':
            return 1 if self.rng.random() < 0.12 else 2
        return 3

    def build_day(self, day: date, taken=None):
        """taken: {category: (쓰인 1문장 set, 쓰인 2문장 set)} — 다른 운세와 겹치지 않게"""
        K = self.kind
        keys = K['keys']
        result = {z: {} for z in keys}
        scores = {z: {} for z in keys}
        weekday = day.weekday()
        season = season_of(day.month)
        overall_s1 = {**S1_POOLS, 'overall': K['overall_s1']}

        for cat in CATEGORIES:
            t1, t2 = (taken or {}).get(cat, (set(), set()))
            used_s1, used_s2 = set(t1), set(t2)
            order = keys[:]
            self.rng.shuffle(order)
            for z in order:
                for _attempt in range(20):
                    # ── 1문장 ──
                    s1 = None
                    if cat == 'overall' and self.rng.random() < K['seasonal_p']:
                        seasonal = [t for _, t in P.SEASONAL_S1[day.month]]
                        s1 = self._pick(seasonal, z, cat, 1, day, used_s1, 30)
                    if s1 is None:
                        tone = self._tone(cat)
                        s1 = self._pick(overall_s1[cat][tone], z, cat, 1, day, used_s1, S1_RECENCY_DAYS)
                    if s1 is None:  # 해당 톤이 소진되면 전체에서
                        allp = [t for pool in overall_s1[cat].values() for t in pool]
                        s1 = self._pick_any(allp, z, cat, 1, day, used_s1, S1_RECENCY_DAYS)

                    # ── 2문장 (1문장과 어울리는 것만) ──
                    ok = lambda pool: [t for t in pool if not conflicts(s1, t, K['rules'], K['upbeat'])]
                    s2 = None
                    r = self.rng.random()
                    if cat == 'overall':
                        if r < 0.15 and weekday in P.WEEKDAY_S2:
                            s2 = self._pick(ok(P.WEEKDAY_S2[weekday]), z, cat, 2, day, used_s2, 21)
                        elif r < 0.33:
                            s2 = self._pick(ok(K['traits'][z]), z, cat, 2, day, used_s2, 12)
                    elif cat == 'health' and r < 0.18:
                        s2 = self._pick(ok(P.SEASON_HEALTH_S2[season]), z, cat, 2, day, used_s2, 14)
                    if s2 is None:
                        s2 = self._pick_any(ok(S2_POOLS[cat]), z, cat, 2, day, used_s2, S2_RECENCY_DAYS)

                    combo = (z, cat, 'combo', s1 + '|' + s2)
                    if not self._recent(combo, day, COMBO_RECENCY_DAYS):
                        break

                used_s1.add(s1)
                used_s2.add(s2)
                self.last_used[(z, cat, 1, s1)] = day
                self.last_used[(z, cat, 2, s2)] = day
                self.last_used[combo] = day
                result[z][cat] = f'{s1} {s2}'
                scores[z][cat] = self._score(s1)
        return result, scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-01-01')
    ap.add_argument('--end', default='2027-12-31')
    ap.add_argument('--kind', choices=list(KINDS), default='zodiac')
    ap.add_argument('--out', help='출력 폴더 (기본: 종류별 폴더)')
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent

    start = datetime.strptime(args.start, '%Y-%m-%d').date()
    end = datetime.strptime(args.end, '%Y-%m-%d').date()
    out = Path(args.out) if args.out else root / KINDS[args.kind]['out']
    out.mkdir(parents=True, exist_ok=True)

    b = Builder(args.kind)
    day = start
    n = 0
    while day <= end:
        taken = None
        if args.kind != 'zodiac':
            # 같은 날 띠별 운세에 쓰인 문장은 피한다
            zpath = root / 'data' / f'{day.isoformat()}.json'
            if zpath.exists():
                zf = json.loads(zpath.read_text(encoding='utf-8'))['fortunes']
                taken = {}
                for cat in CATEGORIES:
                    parts = [split_text(zf[z][cat]) for z in zf]
                    taken[cat] = ({p[0] for p in parts if p[0]}, {p[1] for p in parts if p[1]})
        fortunes, scores = b.build_day(day, taken)
        payload = {'date': day.isoformat(), 'fortunes': fortunes, 'scores': scores}
        (out / f'{day.isoformat()}.json').write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        day += timedelta(days=1)
        n += 1
    print(f'{n}일치 생성 → {out}')


if __name__ == '__main__':
    main()
