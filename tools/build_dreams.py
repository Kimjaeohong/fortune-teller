"""
꿈해몽 사전 페이지 생성기

    python3 tools/build_dreams.py

읽는 것: tools/dreams/catalog.json, tools/dreams/data/*.json
만드는 것:
    dream/index.html          꿈해몽 메인 (검색 + 분류별 전체 목록)
    dream/<slug>.html         꿈 하나당 한 페이지 (검색엔진이 읽을 수 있게 본문을 HTML에 그대로 넣음)
    sitemap.xml               <!-- dream:start --> ~ <!-- dream:end --> 구간을 새로 씀

글을 고치려면 data/*.json 을 고치고 다시 돌리면 됩니다.
"""
import argparse
import hashlib
import html
import json
import random
import re
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'dreams'
OUT = ROOT / 'dream'
SITE = 'https://fortune.hongspot.com'

VERDICT = {
    'good':    {'label': '길몽',          'short': '좋음', 'cls': 'good'},
    'mixed':   {'label': '풀이가 갈려요', 'short': '반반', 'cls': 'mixed'},
    'caution': {'label': '조심하라는 꿈', 'short': '주의', 'cls': 'caution'},
}

# 메인에 먼저 보여 줄 많이 찾는 꿈
POPULAR = ['pig', 'poop', 'teeth', 'snake', 'ex-lover', 'fire', 'ancestor', 'deceased-parent',
           'corpse', 'dragon', 'tiger', 'death-self', 'lottery', 'pick-money', 'army', 'baby',
           'chased', 'cat']

CATEGORY_ICON = {'animal': '🐾', 'people': '👥', 'body': '🫀', 'action': '🏃', 'nature': '🌿',
                 'place': '🏠', 'object': '💍', 'food': '🍑'}

e = html.escape


def load():
    catalog = json.loads((SRC / 'catalog.json').read_text(encoding='utf-8'))
    entries = {}
    for p in sorted((SRC / 'data').glob('*.json')):
        for item in json.loads(p.read_text(encoding='utf-8')):
            entries[item['slug']] = item
    order = [d['slug'] for d in catalog['dreams']]
    meta = {d['slug']: d for d in catalog['dreams']}
    missing = [s for s in order if s not in entries]
    if missing:
        raise SystemExit(f'본문이 없는 꿈: {missing}')
    return catalog['categories'], order, meta, entries


def lucky_numbers(slug):
    """꿈마다 고정된 행운 번호 6개 (1~45)"""
    seed = int(hashlib.sha256(f'hongspot-dream:{slug}'.encode()).hexdigest(), 16)
    return sorted(random.Random(seed).sample(range(1, 46), 6))


def ball_class(n):
    return 'b1' if n <= 10 else 'b2' if n <= 20 else 'b3' if n <= 30 else 'b4' if n <= 40 else 'b5'


def h1_text(title):
    return f'{title} 해몽'


def page_title(entry):
    return f"{entry['title']} 해몽 — 상황별 풀이 {len(entry['cases'])}가지 | 홍스팟 운세"


def verdict_badge(v, small=False):
    info = VERDICT[v]
    return f'<span class="verdict verdict--{info["cls"]}{" verdict--sm" if small else ""}">{info["short" if small else "label"]}</span>'


NAV_ITEMS = [('/', '띠별 운세'), ('/ilgan.html', '사주'), ('/invest.html', '투자운'), ('/star.html', '별자리'),
             ('/dream/', '꿈해몽'), ('/name.html', '궁합'), ('/tarot.html', '타로'), ('/lotto.html', '로또')]


def nav_html():
    lines = []
    for href, label in NAV_ITEMS:
        current = ' aria-current="page"' if href == '/dream/' else ''
        lines.append(f'                <a href="{href}"{current}>{label}</a>\n')
    return ''.join(lines)


def safe_json(obj):
    """<script> 안에 넣어도 안전한 JSON"""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def head(title, description, canonical, og_type='article', extra=''):
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}">
    <meta name="theme-color" content="#0c0f1d">
    <link rel="canonical" href="{canonical}">

    <meta property="og:type" content="{og_type}">
    <meta property="og:site_name" content="홍스팟 운세">
    <meta property="og:title" content="{e(title.split(' | ')[0])}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE}/fortune-image.png">
    <meta name="twitter:card" content="summary">

    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2248%22 fill=%22%230c0f1d%22/><text x=%2250%22 y=%2268%22 font-size=%2252%22 text-anchor=%22middle%22 fill=%22%23d9b673%22>福</text></svg>">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/styles.css">

    <!-- Google AdSense 자동 광고 -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2438640431184534" crossorigin="anonymous"></script>
    <!-- 카카오톡 공유 SDK -->
    <script defer src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js" crossorigin="anonymous"></script>
{extra}</head>
<body>
    <div class="page page--narrow">
        <header class="topbar">
            <a href="/" class="brand"><span class="brand-mark">福</span><span class="brand-text">홍스팟 운세</span></a>
            <nav class="nav" aria-label="주요 메뉴">
{nav_html()}            </nav>
        </header>
'''


FOOT = '''
    <footer class="footer">
        <p>꿈 해몽은 전해 내려오는 풀이를 재미로 정리한 거예요</p>
        <p>건강·돈·관계의 중요한 결정은 꿈보다 현실의 정보로 내려 주세요</p>
        <p><a href="/privacy.html">개인정보처리방침</a></p>
    </footer>

    <script src="/config.js"></script>
    <script src="/common.js"></script>
    <script src="/dream/dream.js"></script>
</body>
</html>
'''


def jsonld(obj):
    return '    <script type="application/ld+json">' + safe_json(obj) + '</script>\n'


def search_form(value=''):
    return f'''
        <form class="dream-search" action="/dream/" method="get" role="search" autocomplete="off">
            <label for="dream-q" class="sr-only">꿈 검색</label>
            <input id="dream-q" name="q" type="search" placeholder="어떤 꿈을 꿨나요?" value="{e(value)}" enterkeyhint="search">
            <button type="submit" class="btn btn-gold">찾기</button>
        </form>'''


# ─────────────────────────────────────────────
#  개별 꿈 페이지
# ─────────────────────────────────────────────

def related_for(slug, entries, meta, order):
    picked = [r for r in entries[slug]['related'] if r in entries and r != slug]
    same = [s for s in order if meta[s]['category'] == meta[slug]['category'] and s != slug and s not in picked]
    # 같은 분류에서 몇 개 더 — 꿈마다 다르게 섞이도록 slug로 고정 셔플
    random.Random(slug).shuffle(same)
    return picked, same[:8]


def dream_page(slug, categories, order, meta, entries, today):
    d = entries[slug]
    cat = meta[slug]['category']
    cat_name = categories[cat]
    url = f'{SITE}/dream/{slug}.html'
    nums = lucky_numbers(slug)
    picked, same = related_for(slug, entries, meta, order)

    ld = jsonld({
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Article',
                'headline': h1_text(d['title']),
                'description': d['summary'],
                'inLanguage': 'ko-KR',
                'mainEntityOfPage': url,
                'image': f'{SITE}/fortune-image.png',
                'datePublished': today,
                'dateModified': today,
                'author': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'},
                'publisher': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'},
            },
            {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': '홍스팟 운세', 'item': SITE + '/'},
                    {'@type': 'ListItem', 'position': 2, 'name': '꿈해몽', 'item': SITE + '/dream/'},
                    {'@type': 'ListItem', 'position': 3, 'name': cat_name, 'item': f'{SITE}/dream/#cat-{cat}'},
                    {'@type': 'ListItem', 'position': 4, 'name': d['title'], 'item': url},
                ],
            },
        ],
    })

    toc = [('meaning', '전통 해몽'), ('psychology', '심리로 보면'), ('cases', '상황별 해몽')]
    if d.get('taemong'):
        toc.append(('taemong', '태몽으로 보면'))
    toc.append(('lucky', '행운 번호'))

    cases_html = ''.join(f'''
                <article class="dream-case" id="case-{i + 1}">
                    <header>
                        <h3>{e(c['title'])}</h3>
                        {verdict_badge(c['verdict'], small=True)}
                    </header>
                    <p>{e(c['text'])}</p>
                </article>''' for i, c in enumerate(d['cases']))

    taemong_html = f'''
        <section class="dream-section" id="taemong" aria-labelledby="h-taemong">
            <h2 id="h-taemong">태몽으로 보면</h2>
            <p>{e(d['taemong'])}</p>
        </section>''' if d.get('taemong') else ''

    def chip(s):
        return f'<a class="chip dream-chip" href="/dream/{s}.html"><i class="vdot vdot--{entries[s]["verdict"]}" aria-hidden="true"></i>{e(entries[s]["title"])}</a>'

    lotto_href = f'/lotto.html#inc={",".join(map(str, nums[:3]))}&from={quote(d["title"])}'

    body = f'''
        <nav class="crumbs dream-crumbs" aria-label="현재 위치">
            <a href="/dream/">← 꿈해몽</a>
            <span class="dream-path"><a href="/dream/#cat-{cat}">{e(cat_name)}</a></span>
        </nav>

        <main class="dream-main">
            <header class="dream-hero">
                <div class="eyebrow">{e(cat_name)} 꿈</div>
                <h1>{e(h1_text(d['title']))}</h1>
                <div class="dream-verdict-row">{verdict_badge(d['verdict'])}<span class="dream-count">상황별 풀이 {len(d['cases'])}가지</span></div>
                <p class="dream-summary">{e(d['summary'])}</p>
            </header>

            <nav class="dream-toc" aria-label="목차">
                {''.join(f'<a href="#{a}">{t}</a>' for a, t in toc)}
            </nav>

            <section class="dream-section" id="meaning" aria-labelledby="h-meaning">
                <h2 id="h-meaning">전통 해몽</h2>
                <p>{e(d['traditional'])}</p>
            </section>

            <section class="dream-section" id="psychology" aria-labelledby="h-psychology">
                <h2 id="h-psychology">심리로 보면</h2>
                <p>{e(d['psychology'])}</p>
            </section>

            <section class="dream-section dream-cases" id="cases" aria-labelledby="h-cases">
                <h2 id="h-cases">상황별 {e(d['title'])} 해몽</h2>{cases_html}
            </section>
{taemong_html}
            <aside class="summary dream-advice" aria-label="이 꿈을 꿨다면">
                <div class="label">이 꿈을 꿨다면</div>
                <p>{e(d['advice'])}</p>
            </aside>

            <section class="dream-lucky" id="lucky" aria-labelledby="h-lucky">
                <div class="dream-lucky-head">
                    <h2 id="h-lucky">{e(d['title'])} 행운 번호</h2>
                    <span>꿈마다 정해진 재미용 번호</span>
                </div>
                <div class="balls">{''.join(f'<span class="ball {ball_class(n)}{" is-fixed" if i < 3 else ""}">{n}</span>' for i, n in enumerate(nums))}</div>
                <a class="btn btn-ghost btn-sm" href="{lotto_href}">테두리 친 3개를 넣고 로또 번호 뽑기 →</a>
            </section>

            <div class="share-row" data-share-title="{e(h1_text(d['title']))}" data-share-text="{e(d['summary'])}" data-share-url="{url}">
                <button type="button" class="btn btn-kakao" data-share="kakao">카카오톡 공유</button>
                <button type="button" class="btn btn-ghost" data-share="link">링크 복사</button>
            </div>
        </main>

        <section class="dream-related" aria-labelledby="h-related">
            <div class="section-head"><h2 id="h-related">함께 많이 찾는 꿈</h2></div>
            <div class="dream-chips">{''.join(chip(s) for s in picked)}</div>
            <div class="section-head dream-subhead"><h2>다른 {e(cat_name)} 꿈</h2><a href="/dream/#cat-{cat}">전체 보기</a></div>
            <div class="dream-chips">{''.join(chip(s) for s in same)}</div>
        </section>
{search_form()}

        <a class="promo" href="/">
            <div>
                <h3>오늘의 띠별 운세도 확인해 보세요</h3>
                <p>꿈이 마음에 걸린다면, 오늘 하루 흐름도 함께 살펴보세요.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>
'''
    return head(page_title(d), d['summary'], url, extra=ld) + body + FOOT


# ─────────────────────────────────────────────
#  꿈해몽 메인
# ─────────────────────────────────────────────

def index_page(categories, order, meta, entries, today):
    url = f'{SITE}/dream/'
    total = len(order)
    title = f'꿈해몽 사전 — {total}가지 꿈 풀이와 상황별 해몽 | 홍스팟 운세'
    desc = (f'돼지꿈, 똥꿈, 이빨 빠지는 꿈, 뱀꿈, 조상꿈까지 {total}가지 꿈의 전통 해몽과 심리 풀이, '
            '상황별 해몽을 한곳에서 찾아보세요. 꿈 이름이나 장면으로 바로 검색할 수 있어요.')

    index_data = [{
        's': s,
        't': entries[s]['title'],
        'a': entries[s]['aliases'],
        'c': [c['title'] for c in entries[s]['cases']],
        'v': entries[s]['verdict'],
        'g': meta[s]['category'],
        'm': entries[s]['summary'],
    } for s in order]

    ld = jsonld({
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        'name': '꿈해몽 사전',
        'description': desc,
        'url': url,
        'inLanguage': 'ko-KR',
        'isPartOf': {'@type': 'WebSite', 'name': '홍스팟 운세', 'url': SITE + '/'},
    })

    index_json = safe_json(index_data)

    popular = ''.join(
        f'<a class="chip dream-chip" href="/dream/{s}.html"><i class="vdot vdot--{entries[s]["verdict"]}" aria-hidden="true"></i>{e(entries[s]["title"])}</a>'
        for s in POPULAR if s in entries)

    cat_tabs = ''.join(
        f'<a class="chip" href="#cat-{c}">{CATEGORY_ICON.get(c, "")} {e(name)} <small>{sum(1 for s in order if meta[s]["category"] == c)}</small></a>'
        for c, name in categories.items())

    sections = ''
    for c, name in categories.items():
        items = [s for s in order if meta[s]['category'] == c]
        cards = ''.join(f'''
                <li><a class="dream-card" href="/dream/{s}.html">
                    <span class="dream-card-top"><strong>{e(entries[s]['title'])}</strong>{verdict_badge(entries[s]['verdict'], small=True)}</span>
                    <small>{e(entries[s]['summary'])}</small>
                </a></li>''' for s in items)
        sections += f'''
        <section class="dream-cat" id="cat-{c}" aria-labelledby="h-cat-{c}">
            <div class="section-head"><h2 id="h-cat-{c}">{CATEGORY_ICON.get(c, "")} {e(name)} 꿈</h2><span>{len(items)}가지</span></div>
            <ul class="dream-grid">{cards}
            </ul>
        </section>
'''

    body = f'''
        <section class="hero dream-index-hero">
            <div class="eyebrow">꿈해몽 사전</div>
            <h1>어젯밤 그 꿈,<br><em>무슨 뜻</em>이었을까</h1>
            <p class="lead">{total}가지 꿈의 전통 해몽 · 심리 풀이 · 상황별 해몽</p>
{search_form()}
            <p class="finder-hint">꿈 이름이나 장면으로 찾아보세요 · 예: "이빨 빠지는", "뱀에 물리는", "돈 줍는"</p>
        </section>

        <section class="dream-results" id="dream-results" hidden aria-live="polite">
            <div class="section-head"><h2 id="results-title">검색 결과</h2><button type="button" class="link-btn" id="results-clear">지우기</button></div>
            <ul class="dream-grid" id="results-list"></ul>
        </section>

        <section class="dream-popular" aria-labelledby="h-popular">
            <div class="section-head"><h2 id="h-popular">많이 찾는 꿈</h2><span><i class="vdot vdot--good"></i>길몽 <i class="vdot vdot--mixed"></i>반반 <i class="vdot vdot--caution"></i>주의</span></div>
            <div class="dream-chips">{popular}</div>
        </section>

        <nav class="dream-cat-tabs" aria-label="꿈 분류">{cat_tabs}</nav>
{sections}
        <a class="promo" href="/">
            <div>
                <h3>오늘의 띠별 운세도 확인해 보세요</h3>
                <p>종합운·재물운·인연운과 오늘의 행운 아이템까지.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>

    <script type="application/json" id="dream-index">{index_json}</script>
'''
    return head(title, desc, url, og_type='website', extra=ld) + body + FOOT


# ─────────────────────────────────────────────
#  사이트맵
# ─────────────────────────────────────────────

def update_sitemap(order, today):
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    block = '  <!-- dream:start -->\n'
    block += f'  <url><loc>{SITE}/dream/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>\n'
    block += ''.join(f'  <url><loc>{SITE}/dream/{s_}.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>\n'
                     for s_ in order)
    block += '  <!-- dream:end -->\n'
    if '<!-- dream:start -->' in s:
        s = re.sub(r'  <!-- dream:start -->\n.*?  <!-- dream:end -->\n', lambda m: block, s, flags=re.S)
    else:
        s = s.replace('</urlset>', block + '</urlset>')
    path.write_text(s, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='lastmod·datePublished 날짜 (기본: 오늘, 한국시간)')
    args = ap.parse_args()
    today = args.date or datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d')

    categories, order, meta, entries = load()
    OUT.mkdir(exist_ok=True)
    keep = {f'{s}.html' for s in order} | {'index.html', 'dream.js'}
    for old in OUT.glob('*.html'):
        if old.name not in keep:
            old.unlink()
    for s in order:
        (OUT / f'{s}.html').write_text(dream_page(s, categories, order, meta, entries, today), encoding='utf-8')
    (OUT / 'index.html').write_text(index_page(categories, order, meta, entries, today), encoding='utf-8')
    update_sitemap(order, today)
    print(f'꿈 페이지 {len(order)}개 + 메인 생성 → {OUT}')


if __name__ == '__main__':
    main()
