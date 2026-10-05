"""
오늘의 투자운 데이터 생성기 (API 호출 없음, 문장 풀 조합 방식)

    python3 tools/build_invest.py --start 2026-01-01 --end 2028-12-31

결과: data/invest/YYYY-MM-DD.json
    {
      "date": "2026-10-05",
      "market": {"open": true}            # 휴장일이면 {"open": false, "reason": "주말"}
      "fortunes": {
        "rat": {"stance": "watch", "score": 3, "text": "1문장 2문장",
                "tip": "...", "caution": "...", "sector": "반도체",
                "time": "오전 장", "keyword": "관망"},
        ...
      }
    }

규칙
- 매매 분위기(stance)는 같은 날 띠별 운세의 재물운 별점과 결이 맞게 뽑는다 (data/*.json 먼저 필요)
- 장이 쉬는 날(주말·공휴일·연말 휴장·선거일)은 'closed' 분위기와 휴장일 전용 문장만 쓴다
- 같은 날 띠끼리 같은 문장·같은 섹터를 쓰지 않는다
- 같은 띠는 최근 며칠 안에 쓴 문장을 다시 쓰지 않고, 1·2문장 조합은 400일 안에 반복하지 않는다
- 시드가 고정이라 다시 돌려도 같은 결과가 나온다 (기간을 늘릴 땐 항상 2026-01-01부터)
"""

import argparse
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import invest_phrases as P

ZODIACS = ['rat', 'ox', 'tiger', 'rabbit', 'dragon', 'snake',
           'horse', 'sheep', 'monkey', 'rooster', 'dog', 'pig']

SEED = 20261005
HEADLINE_RECENCY = 10
DETAIL_RECENCY = 7
TIP_RECENCY = 12
CAUTION_RECENCY = 12
SECTOR_RECENCY = 4
COMBO_RECENCY = 400


# ─────────────────────────────────────────────
#  휴장일 (한국 주식시장)
# ─────────────────────────────────────────────

# 고정 공휴일: (월, 일, 이름, 대체공휴일 적용 여부)
FIXED_HOLIDAYS = [
    (1, 1, '신정', False),
    (3, 1, '삼일절', True),
    (5, 1, '근로자의 날', False),
    (5, 5, '어린이날', True),
    (6, 6, '현충일', False),
    (8, 15, '광복절', True),
    (10, 3, '개천절', True),
    (10, 9, '한글날', True),
    (12, 25, '성탄절', True),
]

# 음력 공휴일 (연도별 양력 날짜) — 설·추석은 당일 기준 앞뒤 하루씩
LUNAR_HOLIDAYS = {
    2026: {'설날': date(2026, 2, 17), '부처님오신날': date(2026, 5, 24), '추석': date(2026, 9, 25)},
    2027: {'설날': date(2027, 2, 6),  '부처님오신날': date(2027, 5, 13), '추석': date(2027, 9, 15)},
    2028: {'설날': date(2028, 1, 26), '부처님오신날': date(2028, 5, 2),  '추석': date(2028, 10, 3)},
}

# 선거일 (휴장)
ELECTION_DAYS = {
    date(2026, 6, 3): '지방선거',
    date(2028, 4, 12): '국회의원 선거',
}


def build_holidays(year):
    """해당 연도의 휴장일 {date: 이름} (주말 제외, 대체공휴일 포함)"""
    days = {}

    def add(d, name):
        if d.year == year and d not in days:
            days[d] = name

    for m, dd, name, _ in FIXED_HOLIDAYS:
        add(date(year, m, dd), name)

    lunar = LUNAR_HOLIDAYS.get(year, {})
    for name, d in lunar.items():
        if name in ('설날', '추석'):
            for off in (-1, 0, 1):
                add(d + timedelta(days=off), f'{name} 연휴')
        else:
            add(d, name)

    for d, name in ELECTION_DAYS.items():
        add(d, name)

    # 대체공휴일: 토·일 또는 다른 공휴일과 겹치면 다음 평일
    def next_free(d):
        d += timedelta(days=1)
        while d.weekday() >= 5 or d in days:
            d += timedelta(days=1)
        return d

    subs = {}
    for m, dd, name, sub in FIXED_HOLIDAYS:
        d = date(year, m, dd)
        if sub and d.weekday() >= 5:
            subs[next_free(d)] = f'{name} 대체공휴일'
    for name, d in lunar.items():
        if name == '부처님오신날' and d.weekday() >= 5:
            subs[next_free(d)] = f'{name} 대체공휴일'
        if name in ('설날', '추석'):
            span = [d + timedelta(days=off) for off in (-1, 0, 1)]
            # 일요일 또는 다른 공휴일과 겹친 날 수만큼 대체 (토요일은 제외)
            overlap = sum(1 for x in span if x.weekday() == 6 or
                          any(x == date(year, m, dd) for m, dd, _, _ in FIXED_HOLIDAYS))
            cur = span[-1]
            for _ in range(overlap):
                cur = next_free(cur)
                subs[cur] = f'{name} 대체공휴일'
    for d, name in subs.items():
        add(d, name)

    # 연말 휴장일: 12월 31일, 주말·공휴일이면 그 직전 거래일
    d = date(year, 12, 31)
    while d.weekday() >= 5 or d in days:
        d -= timedelta(days=1)
    add(d, '연말 휴장')
    return days


_HOLIDAY_CACHE = {}


def market_status(d):
    """(열림 여부, 사유)"""
    if d.weekday() >= 5:
        return False, '주말'
    if d.year not in _HOLIDAY_CACHE:
        _HOLIDAY_CACHE[d.year] = build_holidays(d.year)
    name = _HOLIDAY_CACHE[d.year].get(d)
    return (False, name) if name else (True, None)


# ─────────────────────────────────────────────
#  생성기
# ─────────────────────────────────────────────

def conflicts(s1, s2):
    for a_words, b_words in P.CONFLICT_RULES:
        if any(a in s1 for a in a_words) and any(b in s2 for b in b_words):
            return True
    return False


def in_season(day, start, end):
    md = (day.month, day.day)
    return start <= md <= end


class Builder:
    def __init__(self):
        self.rng = random.Random(SEED)
        self.last_used = {}   # (zodiac, slot, text) -> date

    def _recent(self, key, today, days):
        d = self.last_used.get(key)
        return d is not None and (today - d).days < days

    def _pick(self, candidates, zodiac, slot, today, used_today, recency):
        fresh = [c for c in candidates if c not in used_today
                 and not self._recent((zodiac, slot, c), today, recency)]
        if not fresh:
            fresh = [c for c in candidates if c not in used_today]
        if not fresh:
            fresh = list(candidates)
        return self.rng.choice(fresh) if fresh else None

    def _stance(self, money, is_open):
        if not is_open:
            return 'closed'
        w = P.STANCE_BY_MONEY[max(1, min(5, money))]
        return self.rng.choices(list(w), weights=list(w.values()))[0]

    def _score(self, stance, money):
        r = self.rng.random()
        if stance == 'flow':
            return 5 if (money == 5 or r < 0.35) else 4
        if stance == 'split':
            return 4 if (money >= 4 or r < 0.3) else 3
        if stance == 'harvest':
            return 4 if money >= 4 else 3
        if stance == 'watch':
            return 2 if (money <= 2 and r < 0.5) else 3
        if stance == 'rest':
            return 1 if (money == 1 or r < 0.15) else 2
        # closed: 재물운 흐름을 그대로 반영
        return 4 if money >= 4 else (2 if money <= 2 else 3)

    def build_day(self, day, money_scores):
        is_open, reason = market_status(day)
        result = {}
        used = {'h': set(), 'd': set(), 't': set(), 'c': set(), 'sector': set()}
        order = ZODIACS[:]
        self.rng.shuffle(order)

        for z in order:
            money = money_scores.get(z, 3)
            stance = self._stance(money, is_open)

            for _attempt in range(80):
                s1 = self._pick(P.HEADLINE[stance], z, 'h', day, used['h'], HEADLINE_RECENCY)

                # 2문장: 요일·시즌·띠 성향 문장을 가끔 섞는다
                ok = lambda pool: [t for t in pool if not conflicts(s1, t)]
                s2 = None
                r = self.rng.random()
                if is_open and r < 0.10 and day.weekday() in P.WEEKDAY_DETAIL:
                    s2 = self._pick(ok(P.WEEKDAY_DETAIL[day.weekday()]), z, 'd', day, used['d'], 21)
                elif is_open and r < 0.20:
                    seasonal = [t for start, end, lines in P.SEASON_DETAIL if in_season(day, start, end) for t in lines]
                    if seasonal:
                        s2 = self._pick(ok(seasonal), z, 'd', day, used['d'], 21)
                elif r < 0.38:
                    s2 = self._pick(ok(P.ZODIAC_TRAITS[z]), z, 'd', day, used['d'], 14)
                if s2 is None:
                    s2 = self._pick(ok(P.DETAIL[stance]), z, 'd', day, used['d'], DETAIL_RECENCY)

                combo = (z, 'combo', s1 + '|' + s2)
                if not self._recent(combo, day, COMBO_RECENCY):
                    break

            tip = self._pick(P.TIPS if is_open else P.CLOSED_TIPS, z, 't', day, used['t'], TIP_RECENCY)
            caution = self._pick(P.CAUTIONS if is_open else P.CLOSED_CAUTIONS, z, 'c', day, used['c'], CAUTION_RECENCY)
            sector = self._pick(P.SECTORS, z, 'sector', day, used['sector'], SECTOR_RECENCY)
            time_ = self.rng.choice(P.TIMES if is_open else P.CLOSED_TIMES)
            keyword = self.rng.choice(P.KEYWORDS[stance])

            for slot, text in (('h', s1), ('d', s2), ('t', tip), ('c', caution), ('sector', sector)):
                used[slot].add(text)
                self.last_used[(z, slot, text)] = day
            self.last_used[combo] = day

            result[z] = {
                'stance': stance,
                'score': self._score(stance, money),
                'text': f'{s1} {s2}',
                'tip': tip,
                'caution': caution,
                'sector': sector,
                'time': time_,
                'keyword': keyword,
            }

        fortunes = {z: result[z] for z in ZODIACS}
        market = {'open': True} if is_open else {'open': False, 'reason': reason}
        return fortunes, market


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-01-01')
    ap.add_argument('--end', default='2028-12-31')
    ap.add_argument('--out', help='출력 폴더 (기본: data/invest)')
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent

    start = datetime.strptime(args.start, '%Y-%m-%d').date()
    end = datetime.strptime(args.end, '%Y-%m-%d').date()
    out = Path(args.out) if args.out else root / 'data' / 'invest'
    out.mkdir(parents=True, exist_ok=True)

    b = Builder()
    day = start
    n = 0
    while day <= end:
        zpath = root / 'data' / f'{day.isoformat()}.json'
        money = {}
        if zpath.exists():
            scores = json.loads(zpath.read_text(encoding='utf-8')).get('scores') or {}
            money = {z: (scores.get(z) or {}).get('money', 3) for z in ZODIACS}
        fortunes, market = b.build_day(day, money)
        payload = {'date': day.isoformat(), 'market': market, 'fortunes': fortunes}
        (out / f'{day.isoformat()}.json').write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        day += timedelta(days=1)
        n += 1
    print(f'{n}일치 생성 → {out}')


if __name__ == '__main__':
    main()
