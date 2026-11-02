"""
오늘의 운세를 검색엔진이 읽을 수 있는 정적 HTML로 만드는 생성기 (매일 자동 실행)

    python3 tools/build_daily.py                 # 한국시간 오늘 기준
    python3 tools/build_daily.py --date 2026-11-03

읽는 것: data/<날짜>.json, data/star/<날짜>.json, data/invest/<날짜>.json
         tools/tpl_detail.html, tools/tpl_star_detail.html, invest.html (틀)
만드는 것:
    zodiac/<띠>.html       띠별 오늘의 운세 12개 (예전 detail.html?zodiac=…)
    star/<별자리>.html     별자리 오늘의 운세 12개 (예전 star-detail.html?sign=…)
    invest/<띠>.html       띠별 오늘의 투자운 12개 (예전 invest.html?zodiac=…)
    daily/<날짜>.html      그날의 12띠 운세·띠별 로또 번호 (오늘 ~ 모레까지 미리 만듦, 30일 지나면 지움)
    daily/index.html       날짜별 운세 목록
    index.html, star.html, invest.html 의 카드 (<!--pre:start--> ~ <!--pre:end--> 구간)
    sitemap.xml            <!-- daily:start --> ~ <!-- daily:end --> 구간

운세 문장은 data/*.json 이 원본이고, 이 생성기가 비용 없이 HTML로 옮겨 적기만 합니다.
화면에서는 detail.js · invest.js · script.js · star.js 가 접속 시점의 오늘 데이터로 다시 채우므로,
자동 실행이 하루 밀려도 방문자에게는 맞는 날짜가 보입니다.
"""
import argparse
import json
import re
from datetime import date, timedelta

from site_common import (CATEGORIES, CATEGORY_COLORS, ROOT, SITE, STAR, STAR_ORDER, ZODIAC, ZODIAC_ORDER, article_ld,
                         balls_html, e, first_sentence, hash_string, korean_date, lotto_numbers, lucky_items, next_draw,
                         page_foot, page_head, safe_json, stars_html, today_kst, update_block, url_line, years_for)

KEEP_DAYS = 30        # 날짜 페이지 보관 기간
SITEMAP_DAYS = 13     # 사이트맵에 넣는 지난 날짜 수
AHEAD_DAYS = 2        # 미리 만들어 두는 날짜 수 (검색엔진이 수집할 시간을 벌어 줌)

STEMS = '갑을병정무기경신임계'
BRANCHES = '자축인묘진사오미신유술해'
STANCE = {
    'flow': ('흐름 타기', '매수 분위기', '#86c2a8'), 'split': ('나눠 담기', '분할 매수', '#8fa8e0'),
    'harvest': ('챙기기', '수익 실현', '#e3c26b'), 'watch': ('지켜보기', '관망', '#b9a9e6'),
    'rest': ('쉬어가기', '매매 휴식', '#e08a7a'), 'closed': ('충전하기', '휴장일', '#9aa0b4'),
}


def load(kind, day):
    sub = {'zodiac': '', 'star': 'star/', 'invest': 'invest/'}[kind]
    path = ROOT / 'data' / f'{sub}{day}.json'
    if not path.exists():
        raise SystemExit(f'데이터가 없습니다: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def short_years(key, year):
    return ' · '.join(str(y)[2:] for y in years_for(key, year)[-6:])


def day_pillar(day):
    """그날의 일진. README 의 일주 계산과 같은 식: (JDN + 49) mod 60 (0 = 갑자)"""
    jdn = date.fromisoformat(day).toordinal() + 1721425
    n = (jdn + 49) % 60
    return n, STEMS[n % 10] + BRANCHES[n % 12]


def ilju_slugs():
    cat = json.loads((ROOT / 'tools' / 'ilju' / 'catalog.json').read_text(encoding='utf-8'))['ilju']
    return [c['slug'] for c in cat]


def rank_star(d, day):
    def key(k):
        s = d['scores'][k]
        return (-s['overall'], -sum(s.values()), hash_string(day + k))
    return sorted(STAR_ORDER, key=key)


def rank_invest(d, day):
    return sorted(ZODIAC_ORDER, key=lambda k: (-d['fortunes'][k]['score'], hash_string(f'{day}:invest:{k}')))


# ── 틀 바꾸기 ─────────────────────────────────

def retitle(s, title, desc, url, ld):
    s = re.sub(r'<title>.*?</title>', lambda m: f'<title>{e(title)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content=".*?">', lambda m: f'<meta name="description" content="{e(desc)}">', s, count=1)
    s = re.sub(r'<link rel="canonical"[^>]*>\n\s*', '', s)
    s = s.replace('<meta name="theme-color" content="#0c0f1d">',
                  f'<meta name="theme-color" content="#0c0f1d">\n    <link rel="canonical" href="{url}">', 1)
    og = title.split(' | ')[0]
    s = re.sub(r'<meta property="og:type" content=".*?">', '<meta property="og:type" content="article">', s, count=1)
    s = re.sub(r'<meta property="og:title" content=".*?">', lambda m: f'<meta property="og:title" content="{e(og)}">', s, count=1)
    s = re.sub(r'<meta property="og:description" content=".*?">', lambda m: f'<meta property="og:description" content="{e(desc)}">', s, count=1)
    s = re.sub(r'\s*<meta property="og:url" content=".*?">', '', s)
    s = s.replace('<meta property="og:image"', f'<meta property="og:url" content="{url}">\n    <meta property="og:image"', 1)
    s = s.replace('</head>', f'    <script type="application/ld+json">{safe_json(ld)}</script>\n</head>', 1)
    return s


def inject_pre(s, element_id, content):
    """id 가 element_id 인 요소 안의 미리 넣은 구간을 바꾼다"""
    pat = rf'(id="{element_id}"[^>]*>)(?:<!--pre:start-->.*?<!--pre:end-->)?'
    return re.sub(pat, lambda m: f'{m.group(1)}<!--pre:start-->{content}<!--pre:end-->', s, count=1, flags=re.S)


def set_date_label(s, text):
    return re.sub(r'(id="today-date">).*?(</div>)', lambda m: m.group(1) + text + m.group(2), s, count=1)



# ── 상세 본문 (detail.js 와 같은 모양) ──────────────

def fortune_body(kind, key, d, day, extra=''):
    m = d['fortunes'][key]
    scores = d['scores'][key]
    items = ''
    for cat, title in CATEGORIES[1:]:
        color = CATEGORY_COLORS[cat]
        items += f'''
                <article class="fortune-item">
                    <header>
                        <h2><span class="cat-dot" style="color:{color};background:{color}"></span>{title}</h2>
                        {stars_html(scores[cat], label=False)}
                    </header>
                    <p>{e(m[cat])}</p>
                </article>'''
    lucky = lucky_items(day, key if kind == 'zodiac' else f'{kind}:{key}')
    return f'''
        <div class="summary">
            <div class="label">오늘의 한마디 · 종합운</div>
            <p>{e(m['overall'])}</p>
        </div>
        <div class="fortune-list">{items}</div>
        <div class="lucky" aria-label="오늘의 행운 아이템">
            <div class="lucky-item"><div class="k">행운의 색</div><div class="v"><span class="swatch" style="background:{lucky['color'][1]}"></span>{lucky['color'][0]}</div></div>
            <div class="lucky-item"><div class="k">행운의 숫자</div><div class="v">{lucky['number']}</div></div>
            <div class="lucky-item"><div class="k">행운의 방향</div><div class="v">{lucky['direction']}</div></div>
            <div class="lucky-item"><div class="k">좋은 시간대</div><div class="v">{lucky['time']}</div></div>
        </div>{extra}'''


def promo(href, title, text):
    return f'''
        <a class="promo" href="{href}">
            <div>
                <h3>{title}</h3>
                <p>{text}</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
'''


def zodiac_page(tpl, key, d, day):
    name, hanja, _ = ZODIAC[key]
    info = korean_date(day)
    years = years_for(key, info['year'])
    url = f'{SITE}/zodiac/{key}.html'
    short = '·'.join(str(y)[2:] for y in years[-5:-1])
    title = f'{name} 오늘의 운세 ({info["short"]}) — {short}년생 | 홍스팟 운세'
    desc = f'{info["full"]} {name} 운세. {first_sentence(d["fortunes"][key]["overall"])} 종합운·재물운·일·건강·인연운과 행운 아이템을 확인해 보세요.'
    ld = article_ld(url, f'{name} 오늘의 운세', desc, '2026-11-02', day,
                    [('홍스팟 운세', SITE + '/'), ('띠별 운세', SITE + '/'), (name, url)])
    s = retitle(tpl, title, desc, url, ld)
    hero = f'''<div class="hanja-lg" aria-hidden="true">{hanja}</div>
        <h1>{name} 오늘의 운세</h1>
        <p class="meta">{info['full']}</p>
        <p class="years">{' · '.join(map(str, years))}년생</p>
        <div class="score" id="hero-score">{stars_html(d['scores'][key]['overall'])}</div>'''
    invest_link = f'''
        <a class="promo promo--tight" href="/invest/{key}.html">
                <div>
                    <h3>{name} 오늘의 투자운 <span class="new-tag">NEW</span></h3>
                    <p>매매 분위기 · 행운의 섹터 · 좋은 시간대 · 오늘의 팁과 주의 포인트</p>
                </div>
                <span class="arrow" aria-hidden="true">→</span>
            </a>'''
    i = ZODIAC_ORDER.index(key)
    prev, nxt = ZODIAC_ORDER[(i + 11) % 12], ZODIAC_ORDER[(i + 1) % 12]
    s = s.replace('<section class="detail-hero" id="detail-hero"></section>', f'<section class="detail-hero" id="detail-hero">{hero}</section>')
    s = s.replace('<div id="fortune-content"></div>', f'<div id="fortune-content">{fortune_body("zodiac", key, d, day, invest_link)}</div>')
    s = s.replace('<div class="sibs" id="sibs"></div>', f'<div class="sibs" id="sibs"><a href="/zodiac/{prev}.html">‹ {ZODIAC[prev][0]}</a><a href="/zodiac/{nxt}.html">{ZODIAC[nxt][0]} ›</a></div>')
    chips = ''.join(f'<a class="chip" href="/zodiac/{k}.html"{" aria-current=\"page\"" if k == key else ""}><span class="hanja" aria-hidden="true">{ZODIAC[k][1]}</span>{ZODIAC[k][0]}</a>' for k in ZODIAC_ORDER)
    s = s.replace('id="other-keys" aria-label="다른 띠"></nav>', f'id="other-keys" aria-label="다른 띠">{chips}</nav>')
    promos = promo(f'/2027/{key}.html', f'2027년 {name} 운세', '정미년 총운·재물·직장·연애와 출생연도별 흐름까지.') + \
        promo(f'/daily/{day}.html', '오늘 12띠 운세와 로또 번호 한눈에', f'{info["short"]} 띠별 운세와 재미로 뽑은 행운 번호.')
    s = s.replace('<a class="promo" href="/tarot.html">', promos.strip() + '\n\n        <a class="promo" href="/tarot.html">', 1)
    s = s.replace("<script>window.FORTUNE_KIND = 'zodiac';</script>", f"<script>window.FORTUNE_KIND = 'zodiac'; window.FORTUNE_KEY = '{key}';</script>")
    return s


def star_page(tpl, key, d, day):
    name, symbol, period, element, planet = STAR[key]
    info = korean_date(day)
    rank = rank_star(d, day).index(key) + 1
    url = f'{SITE}/star/{key}.html'
    title = f'{name} 오늘의 운세 ({info["short"]}) — {period.replace(" ", "")} | 홍스팟 운세'
    desc = f'{info["full"]} {name} 운세, 오늘 12별자리 중 {rank}위. {first_sentence(d["fortunes"][key]["overall"])} 재물·일·건강·인연운까지 확인해 보세요.'
    ld = article_ld(url, f'{name} 오늘의 운세', desc, '2026-11-02', day,
                    [('홍스팟 운세', SITE + '/'), ('별자리 운세', SITE + '/star.html'), (name, url)])
    s = retitle(tpl, title, desc, url, ld)
    hero = f'''<div class="hanja-lg glyph-star" aria-hidden="true">{symbol}</div>
        <h1>{name} 오늘의 운세</h1>
        <p class="meta">{info['full']}</p>
        <p class="years">{period} · {element}의 별자리 · 수호성 {planet}</p>
        <div class="score" id="hero-score">{stars_html(d['scores'][key]['overall'])}<span class="rank-pill">오늘 {rank}위</span></div>'''
    i = STAR_ORDER.index(key)
    prev, nxt = STAR_ORDER[(i + 11) % 12], STAR_ORDER[(i + 1) % 12]
    s = s.replace('<section class="detail-hero" id="detail-hero"></section>', f'<section class="detail-hero" id="detail-hero">{hero}</section>')
    s = s.replace('<div id="fortune-content"></div>', f'<div id="fortune-content">{fortune_body("star", key, d, day)}</div>')
    s = s.replace('<div class="sibs" id="sibs"></div>', f'<div class="sibs" id="sibs"><a href="/star/{prev}.html">‹ {STAR[prev][0]}</a><a href="/star/{nxt}.html">{STAR[nxt][0]} ›</a></div>')
    chips = ''.join(f'<a class="chip" href="/star/{k}.html"{" aria-current=\"page\"" if k == key else ""}><span class="hanja glyph-star" aria-hidden="true">{STAR[k][1]}</span>{STAR[k][0]}</a>' for k in STAR_ORDER)
    s = s.replace('id="other-keys" aria-label="다른 별자리"></nav>', f'id="other-keys" aria-label="다른 별자리">{chips}</nav>')
    s = s.replace("<script>window.FORTUNE_KIND = 'star';</script>", f"<script>window.FORTUNE_KIND = 'star'; window.FORTUNE_KEY = '{key}';</script>")
    return s


# ── 카드 (script.js / star.js / invest.js 와 같은 모양) ─────

def zodiac_cards(d, year):
    out = ''
    for i, k in enumerate(ZODIAC_ORDER):
        name, hanja, emoji = ZODIAC[k]
        line = re.sub(r'^오늘은\s*\S+띠(?:에게|는|의)\s*', '', first_sentence(d['fortunes'][k]['overall']))
        out += f'''
            <a class="zodiac-card" href="/zodiac/{k}.html" data-zodiac="{k}" style="animation-delay:{i * 35}ms">
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">{hanja}</span>
                    <div class="zc-name">{name}<span class="zc-emoji" aria-hidden="true">{emoji}</span></div>
                </div>
                <div class="zc-years">{short_years(k, year)}년생</div>
                <p class="zc-line">{e(line)}</p>
                <div class="zc-foot">{stars_html(d['scores'][k]['overall'])}</div>
            </a>'''
    return out


def star_cards(d, day):
    ranking = rank_star(d, day)
    out = ''
    for i, k in enumerate(STAR_ORDER):
        name, symbol, period, element, _ = STAR[k]
        rank = ranking.index(k) + 1
        badge = f'<span class="rank-badge{" top" if rank <= 3 else ""}">{rank}위</span>'
        out += f'''
            <a class="zodiac-card" href="/star/{k}.html" data-key="{k}" style="animation-delay:{i * 35}ms">
                <div class="zc-top">
                    <span class="hanja glyph-star" aria-hidden="true">{symbol}</span>
                    <div class="zc-name">{name}</div>
                </div>
                <div class="zc-years">{period} · {element}</div>
                <p class="zc-line">{e(first_sentence(d['fortunes'][k]['overall']))}</p>
                <div class="zc-foot">{stars_html(d['scores'][k]['overall'], label=False)}{badge}</div>
            </a>'''
    top = ''.join(f'''
        <li class="top3-item rank-{i + 1}">
            <a href="/star/{k}.html">
                <span class="top3-rank">{i + 1}</span>
                <span class="hanja glyph-star" aria-hidden="true">{STAR[k][1]}</span>
                <span class="top3-body">
                    <strong>{STAR[k][0]}</strong>
                    <small>{e(first_sentence(d['fortunes'][k]['overall']))}</small>
                </span>
            </a>
        </li>''' for i, k in enumerate(ranking[:3]))
    return out, top


def stance_pill(stance, with_short=True):
    label, short, color = STANCE.get(stance, STANCE['watch'])
    sm = f'<small>{short}</small>' if with_short else ''
    return f'<span class="stance stance--{stance}" style="--stance:{color}">{label}{sm}</span>'


def invest_cards(d, day):
    ranking = rank_invest(d, day)
    out = ''
    for i, k in enumerate(ZODIAC_ORDER):
        name, hanja, emoji = ZODIAC[k]
        f = d['fortunes'][k]
        rank = ranking.index(k) + 1
        badge = f'<span class="rank-badge{" top" if rank <= 3 else ""}">{rank}위</span>'
        out += f'''
            <a class="zodiac-card" href="/invest/{k}.html" data-zodiac="{k}" style="animation-delay:{i * 35}ms">
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">{hanja}</span>
                    <div class="zc-name">{name}<span class="zc-emoji" aria-hidden="true">{emoji}</span></div>
                </div>
                <div class="zc-stance">{stance_pill(f['stance'], False)}</div>
                <p class="zc-line">{e(first_sentence(f['text']))}</p>
                <div class="zc-foot">{stars_html(f['score'], label=False)}{badge}</div>
            </a>'''
    top = ''.join(f'''
        <li class="top3-item rank-{i + 1}">
            <a href="/invest/{k}.html">
                <span class="top3-rank">{i + 1}</span>
                <span class="hanja" aria-hidden="true">{ZODIAC[k][1]}</span>
                <span class="top3-body">
                    <strong>{ZODIAC[k][0]} <span class="top3-stance">{STANCE[d['fortunes'][k]['stance']][0]}</span></strong>
                    <small>{e(first_sentence(d['fortunes'][k]['text']))}</small>
                </span>
            </a>
        </li>''' for i, k in enumerate(ranking[:3]))
    return out, top


def invest_focus(key, d, day):
    f = d['fortunes'][key]
    name, hanja, emoji = ZODIAC[key]
    info = korean_date(day)
    color = STANCE.get(f['stance'], STANCE['watch'])[2]
    rank = rank_invest(d, day).index(key) + 1
    years = ' · '.join(map(str, years_for(key, info['year'])[-6:]))
    is_open = d.get('market', {}).get('open', True)
    digit = hash_string(f'invest:{day}:{key}') % 10
    return f'''
        <div class="invest-focus-head">
            <span class="hanja" aria-hidden="true">{hanja}</span>
            <div class="invest-focus-title">
                <h2>{name} 오늘의 투자운 <span class="zc-emoji" aria-hidden="true">{emoji}</span></h2>
                <p class="years">{years}년생 · {info['short']}</p>
            </div>
            <div class="invest-focus-score">
                {stars_html(f['score'])}
                <span class="rank-pill">오늘 {rank}위</span>
            </div>
        </div>
        <div class="invest-stance-row">{stance_pill(f['stance'])}</div>
        <div class="summary">
            <div class="label">오늘의 투자 한마디</div>
            <p>{e(f['text'])}</p>
        </div>
        <div class="lucky invest-lucky" aria-label="오늘의 투자 포인트">
            <div class="lucky-item"><div class="k">{'행운의 섹터' if is_open else '다음 장 관심 섹터'}</div><div class="v">{e(f['sector'])}</div></div>
            <div class="lucky-item"><div class="k">좋은 시간대</div><div class="v">{e(f['time'])}</div></div>
            <div class="lucky-item"><div class="k">오늘의 키워드</div><div class="v">#{e(f['keyword'])}</div></div>
            <div class="lucky-item"><div class="k">행운의 끝자리</div><div class="v">{digit}<small class="v-sub">종목코드 끝자리</small></div></div>
        </div>
        <div class="invest-notes">
            <article class="fortune-item">
                <header><h3><span class="cat-dot" style="color:{color};background:{color}"></span>오늘의 팁</h3></header>
                <p>{e(f['tip'])}</p>
            </article>
            <article class="fortune-item">
                <header><h3><span class="cat-dot" style="color:var(--rose);background:var(--rose)"></span>주의 포인트</h3></header>
                <p>{e(f['caution'])}</p>
            </article>
        </div>
        <div class="share-row"><a class="btn btn-ghost" href="/zodiac/{key}.html">{name} 종합 운세 →</a></div>'''


def invest_page(tpl, key, d, day):
    name = ZODIAC[key][0]
    info = korean_date(day)
    f = d['fortunes'][key]
    url = f'{SITE}/invest/{key}.html'
    title = f'{name} 오늘의 투자운 ({info["short"]}) — 띠별 주식 운세 | 홍스팟 운세'
    desc = f'{info["full"]} {name} 투자운. {first_sentence(f["text"])} 매매 분위기와 행운의 섹터, 좋은 시간대를 재미로 확인해 보세요.'
    ld = article_ld(url, f'{name} 오늘의 투자운', desc, '2026-11-02', day,
                    [('홍스팟 운세', SITE + '/'), ('오늘의 투자운', SITE + '/invest.html'), (name, url)])
    s = retitle(tpl, title, desc, url, ld)
    s = re.sub(r'<h1>.*?</h1>', lambda m: f'<h1>{name} <em>오늘의 투자운</em></h1>', s, count=1, flags=re.S)
    s = re.sub(r'<form class="finder".*?</form>\s*<p class="finder-hint">.*?</p>', '', s, count=1, flags=re.S)
    s = s.replace('<section class="invest-focus" id="focus" hidden aria-live="polite"></section>',
                  f'<section class="invest-focus" id="focus" aria-live="polite">{invest_focus(key, d, day)}\n        </section>')
    s = s.replace('<script src="/invest.js"></script>', f"<script>window.INVEST_KEY = '{key}';</script>\n    <script src=\"/invest.js\"></script>")
    return s


# ── 날짜별 페이지 ──────────────────────────────

def daily_page(day, today, published):
    z = load('zodiac', day)
    st = load('star', day)
    inv = load('invest', day)
    info = korean_date(day)
    n, pillar = day_pillar(day)
    slug = ilju_slugs()[n]
    round_no, draw = next_draw(day)
    draw_label = korean_date(draw.isoformat())
    url = f'{SITE}/daily/{day}.html'
    head_title = f'{info["full"]} 오늘의 운세 — 띠별 운세·로또 번호'
    desc = f'{info["full"]}({pillar}일) 12띠 운세와 띠별 행운의 로또 번호, 별자리 순위, 투자운까지 한 번에 확인해 보세요. 재미로 보는 하루 운세예요.'
    keywords = f'{info["full"]} 운세, {info["short"]} 띠별 운세, {info["short"]} 로또 띠별 번호, 오늘의 운세, 띠별 운세'
    ld = article_ld(url, head_title, desc, published, published,
                    [('홍스팟 운세', SITE + '/'), ('날짜별 운세', SITE + '/daily/'), (info['short'], url)])

    items = ''
    for k in ZODIAC_ORDER:
        name, hanja, emoji = ZODIAC[k]
        m = z['fortunes'][k]
        lucky = lucky_items(day, k)
        nums, lucky_no = lotto_numbers(day, k)
        items += f'''
            <article class="fortune-item daily-item" id="z-{k}">
                <header>
                    <h2><a href="/zodiac/{k}.html">{name}</a><small>{short_years(k, info['year'])}년생</small></h2>
                    {stars_html(z['scores'][k]['overall'], label=False)}
                </header>
                <p>{e(m['overall'])}</p>
                <p class="daily-sub"><b>재물운</b> {e(first_sentence(m['money']))}</p>
                <p class="daily-sub"><b>인연운</b> {e(first_sentence(m['relationship']))}</p>
                <p class="daily-lucky">행운의 색 {lucky['color'][0]} · 방향 {lucky['direction']} · 시간대 {lucky['time']}</p>
                <div class="daily-balls"><span>{name} 로또 번호</span>{balls_html(nums, lucky_no)}</div>
            </article>'''

    stars = ''.join(f'<li><a href="/star/{k}.html">{i + 1}위 {STAR[k][0]}</a><small>{e(first_sentence(st["fortunes"][k]["overall"]))}</small></li>'
                    for i, k in enumerate(rank_star(st, day)[:3]))
    invs = ''.join(f'<li><a href="/invest/{k}.html">{i + 1}위 {ZODIAC[k][0]}</a><small>{STANCE[inv["fortunes"][k]["stance"]][0]} · {e(first_sentence(inv["fortunes"][k]["text"]))}</small></li>'
                   for i, k in enumerate(rank_invest(inv, day)[:3]))
    d0 = date.fromisoformat(day)
    prev_day, next_day = (d0 - timedelta(days=1)).isoformat(), (d0 + timedelta(days=1)).isoformat()
    prev_link = f'<a href="/daily/{prev_day}.html">‹ {korean_date(prev_day)["short"]}</a>' if (ROOT / 'daily' / f'{prev_day}.html').exists() else ''
    next_link = f'<a href="/daily/{next_day}.html">{korean_date(next_day)["short"]} ›</a>' if next_day <= (date.fromisoformat(today) + timedelta(days=AHEAD_DAYS)).isoformat() else ''

    body = f'''
        <nav class="crumbs" aria-label="현재 위치">
            <a href="/daily/">← 날짜별 운세</a>
            <span class="dream-path">{prev_link} {next_link}</span>
        </nav>

        <main>
            <header class="dream-hero">
                <div class="eyebrow">{pillar}일 · 제{round_no}회 로또 {draw_label['short']} 추첨</div>
                <h1>{info['full']}<br>오늘의 운세</h1>
                <p class="dream-summary">오늘의 일진은 <a href="/ilju/{slug}.html">{pillar}</a>이에요. 12띠 운세와 띠별 행운의 로또 번호, 별자리·투자운 순위를 모았어요.</p>
            </header>

            <nav class="dream-cat-tabs" aria-label="띠 바로가기">{''.join(f'<a class="chip" href="#z-{k}">{ZODIAC[k][0]}</a>' for k in ZODIAC_ORDER)}</nav>

            <div class="fortune-list daily-list">{items}
            </div>

            <div class="stem-lists">
                <section class="stem-list stem-list--good" aria-labelledby="h-star">
                    <h2 id="h-star">오늘의 별자리 순위</h2>
                    <ol class="daily-rank">{stars}</ol>
                </section>
                <section class="stem-list stem-list--good" aria-labelledby="h-inv">
                    <h2 id="h-inv">오늘의 투자운 순위</h2>
                    <ol class="daily-rank">{invs}</ol>
                </section>
            </div>

            <aside class="caution" aria-label="이용 안내">
                <h2>꼭 알아 두세요</h2>
                <ul>
                    <li>로또 번호는 날짜와 띠로 정해지는 재미용 조합이에요. <b>어떤 방법으로 뽑아도 당첨 확률은 같아요.</b></li>
                    <li>로또 복권은 만 19세 이상만 살 수 있어요. 도박 문제로 고민된다면 한국도박문제예방치유원 <a href="tel:1336">1336</a>에 연락해 보세요.</li>
                    <li>운세는 재미로만 봐 주세요. 투자 판단과 결과는 언제나 본인의 몫이에요.</li>
                </ul>
            </aside>

            <div class="share-row" data-share-title="{e(head_title)}" data-share-text="{e(desc)}" data-share-url="{url}">
                <button type="button" class="btn btn-kakao" data-share="kakao">카카오톡 공유</button>
                <button type="button" class="btn btn-ghost" data-share="link">링크 복사</button>
            </div>
        </main>
{promo('/lotto.html', '내 번호로 다시 뽑아 보기', '포함·제외할 번호를 고르고 5게임을 뽑을 수 있어요.')}
    </div>
'''
    return page_head(f'{head_title} | 홍스팟 운세', desc, url, keywords, ld=ld) + body + page_foot('운세와 번호는 재미로만 봐 주세요')


def daily_index(days, today):
    url = f'{SITE}/daily/'
    title = '날짜별 운세 — 띠별 운세·로또 번호 모아보기 | 홍스팟 운세'
    desc = '날짜별 12띠 운세와 띠별 행운의 로또 번호를 모았어요. 오늘과 지난 2주, 앞으로 이틀의 운세를 날짜를 눌러 확인해 보세요.'
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '날짜별 운세', 'description': desc, 'url': url,
          'inLanguage': 'ko-KR', 'isPartOf': {'@type': 'WebSite', 'name': '홍스팟 운세', 'url': SITE + '/'}}
    rows = ''
    for d in sorted(days, reverse=True):
        info = korean_date(d)
        tag = ' <span class="new-tag">오늘</span>' if d == today else ''
        rows += f'''
                <li><a class="dream-card" href="/daily/{d}.html">
                    <span class="dream-card-top"><strong>{info['full']}{tag}</strong></span>
                    <small>{day_pillar(d)[1]}일 · 12띠 운세와 띠별 로또 번호</small>
                </a></li>'''
    body = f'''
        <section class="hero">
            <div class="eyebrow">날짜별 운세</div>
            <h1>날짜를 골라<br><em>그날의 운세</em>를 봐요</h1>
            <p class="lead">12띠 운세 · 띠별 로또 번호 · 별자리 순위 · 투자운</p>
        </section>

        <ul class="dream-grid">{rows}
        </ul>
{promo('/2027/', '2027년 정미년 띠별 운세', '12띠 총운과 삼재, 출생연도별 흐름까지 미리 살펴보세요.')}
    </div>
'''
    return page_head(title, desc, url, '날짜별 운세, 오늘의 운세, 띠별 운세, 띠별 로또 번호', og_type='website', ld=ld) + body + page_foot()


# ── 실행 ───────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='기준 날짜 YYYY-MM-DD (기본: 한국시간 오늘)')
    args = ap.parse_args()
    day = args.date or today_kst()
    d0 = date.fromisoformat(day)
    info = korean_date(day)

    zd, sd, id_ = load('zodiac', day), load('star', day), load('invest', day)
    tpl_z = (ROOT / 'tools' / 'tpl_detail.html').read_text(encoding='utf-8')
    tpl_s = (ROOT / 'tools' / 'tpl_star_detail.html').read_text(encoding='utf-8')

    # 목록 페이지 카드
    p = ROOT / 'index.html'
    s = p.read_text(encoding='utf-8')
    s = set_date_label(inject_pre(s, 'zodiac-grid', zodiac_cards(zd, info['year'])), info['full'])
    p.write_text(s, encoding='utf-8')

    p = ROOT / 'star.html'
    s = p.read_text(encoding='utf-8')
    cards, top = star_cards(sd, day)
    s = set_date_label(inject_pre(inject_pre(s, 'star-grid', cards), 'top3', top), info['full'])
    p.write_text(s, encoding='utf-8')

    p = ROOT / 'invest.html'
    s = p.read_text(encoding='utf-8')
    cards, top = invest_cards(id_, day)
    s = set_date_label(inject_pre(inject_pre(s, 'invest-grid', cards), 'top3', top), info['full'])
    p.write_text(s, encoding='utf-8')
    tpl_i = s

    # 띠·별자리·투자운 상세
    for sub in ('zodiac', 'star', 'invest', 'daily'):
        (ROOT / sub).mkdir(exist_ok=True)
    for k in ZODIAC_ORDER:
        (ROOT / 'zodiac' / f'{k}.html').write_text(zodiac_page(tpl_z, k, zd, day), encoding='utf-8')
        (ROOT / 'invest' / f'{k}.html').write_text(invest_page(tpl_i, k, id_, day), encoding='utf-8')
    for k in STAR_ORDER:
        (ROOT / 'star' / f'{k}.html').write_text(star_page(tpl_s, k, sd, day), encoding='utf-8')

    # 날짜 페이지: 지난 것은 지우고, 오늘~모레는 새로 만든다
    out = ROOT / 'daily'
    cutoff = (d0 - timedelta(days=KEEP_DAYS)).isoformat()
    for f in out.glob('20*.html'):
        if f.stem < cutoff:
            f.unlink()
    window = [(d0 + timedelta(days=i)).isoformat() for i in range(0, AHEAD_DAYS + 1)]
    for d in window:
        f = out / f'{d}.html'
        published = day
        if f.exists():
            m = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', f.read_text(encoding='utf-8'))
            if m:
                published = m.group(1)
        f.write_text(daily_page(d, day, published), encoding='utf-8')
    # 어제 페이지의 '다음 날' 링크가 끊기지 않게 어제 것도 다시 쓴다
    y = (d0 - timedelta(days=1)).isoformat()
    if (out / f'{y}.html').exists():
        m = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', (out / f'{y}.html').read_text(encoding='utf-8'))
        (out / f'{y}.html').write_text(daily_page(y, day, m.group(1) if m else y), encoding='utf-8')

    listed = sorted(f.stem for f in out.glob('20*.html'))
    recent = [d for d in listed if d >= (d0 - timedelta(days=SITEMAP_DAYS)).isoformat()]
    (out / 'index.html').write_text(daily_index(recent, day), encoding='utf-8')

    block = url_line(f'{SITE}/daily/', day, 'daily', '0.8')
    block += ''.join(url_line(f'{SITE}/daily/{d}.html', day, 'never', '0.7') for d in reversed(recent))
    block += ''.join(url_line(f'{SITE}/zodiac/{k}.html', day, 'daily', '0.8') for k in ZODIAC_ORDER)
    block += ''.join(url_line(f'{SITE}/star/{k}.html', day, 'daily', '0.8') for k in STAR_ORDER)
    block += ''.join(url_line(f'{SITE}/invest/{k}.html', day, 'daily', '0.7') for k in ZODIAC_ORDER)
    update_block('daily', block)
    print(f'{day} 기준 정적 페이지 생성 완료 (날짜 페이지 {len(listed)}개)')


if __name__ == '__main__':
    main()
