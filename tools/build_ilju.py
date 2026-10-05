"""
일주 60가지 페이지 생성기

    python3 tools/build_ilju.py

읽는 것: tools/ilju/catalog.json (60갑자 순서·별칭·합충 짝), tools/ilju/data/*.json (일주별 본문)
만드는 것:
    ilju/index.html        60갑자 전체 목록
    ilju/<slug>.html       일주 하나당 한 페이지 (예: byeong-o.html = 병오일주) + 오늘의 운세(ilgan.js 로 계산)
    sitemap.xml            <!-- ilju:start --> ~ <!-- ilju:end --> 구간
"""
import argparse
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'ilju'
OUT = ROOT / 'ilju'
SITE = 'https://fortune.hongspot.com'

STEMS = '갑을병정무기경신임계'
BRANCHES = '자축인묘진사오미신유술해'
STEM_KEY = ['gap', 'eul', 'byeong', 'jeong', 'mu', 'gi', 'gyeong', 'sin', 'im', 'gye']
STEM_NAME = ['갑목', '을목', '병화', '정화', '무토', '기토', '경금', '신금', '임수', '계수']
ELEM_HANJA = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}

NAV_ITEMS = [('/', '띠별 운세'), ('/ilgan.html', '사주'), ('/invest.html', '투자운'), ('/star.html', '별자리'),
             ('/dream/', '꿈해몽'), ('/name.html', '궁합'), ('/tarot.html', '타로'), ('/lotto.html', '로또')]

e = html.escape


def safe_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def nav_html():
    out = []
    for href, label in NAV_ITEMS:
        cur = ' aria-current="page"' if href == '/ilgan.html' else ''
        out.append(f'                <a href="{href}"{cur}>{label}</a>\n')
    return ''.join(out)


def load():
    cat = json.loads((SRC / 'catalog.json').read_text(encoding='utf-8'))['ilju']
    data = {}
    for p in sorted((SRC / 'data').glob('*.json')):
        for item in json.loads(p.read_text(encoding='utf-8')):
            data[item['name']] = item
    missing = [c['name'] for c in cat if c['name'] not in data]
    if missing:
        raise SystemExit(f'본문이 없는 일주: {missing}')
    return cat, data


def head(title, desc, url, keywords, og_type='article', ld=''):
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(title)}</title>
    <meta name="description" content="{e(desc)}">
    <meta name="keywords" content="{e(keywords)}">
    <meta name="theme-color" content="#0c0f1d">
    <link rel="canonical" href="{url}">

    <meta property="og:type" content="{og_type}">
    <meta property="og:site_name" content="홍스팟 운세">
    <meta property="og:title" content="{e(title.split(' | ')[0])}">
    <meta property="og:description" content="{e(desc)}">
    <meta property="og:url" content="{url}">
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
    <script type="application/ld+json">{ld}</script>
</head>
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
        <p>일주 풀이는 전해 내려오는 해석을 재미로 정리한 거예요</p>
        <p>매일 자정(한국시간) 오늘의 운세가 바뀝니다</p>
        <p><a href="/privacy.html">개인정보처리방침</a></p>
    </footer>

    <script src="/config.js"></script>
    <script src="/common.js"></script>
    <script src="/ilgan-data.js"></script>
    <script src="/ilgan.js"></script>
</body>
</html>
'''


def page(c, d, cat, by_name, today):
    url = f"{SITE}/ilju/{c['slug']}.html"
    si, bi = STEMS.index(c['stem']), BRANCHES.index(c['branch'])
    i = c['order'] - 1
    prev, nxt = cat[(i - 1) % 60], cat[(i + 1) % 60]
    hap, chung = by_name[c['hap_partner']], by_name[c['chung_partner']]
    stem_name = STEM_NAME[si]
    title = f"{c['name']}일주 특징 — {c['alias']}의 성격·연애·궁합 | 홍스팟 운세"
    ld = safe_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': f"{c['name']}일주 특징", 'description': d['summary'], 'inLanguage': 'ko-KR',
         'mainEntityOfPage': url, 'image': f'{SITE}/fortune-image.png', 'datePublished': today, 'dateModified': today,
         'author': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'},
         'publisher': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': '홍스팟 운세', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': '사주 일진', 'item': SITE + '/ilgan.html'},
            {'@type': 'ListItem', 'position': 3, 'name': '일주 60가지', 'item': SITE + '/ilju/'},
            {'@type': 'ListItem', 'position': 4, 'name': f"{c['name']}일주", 'item': url}]}]})
    keywords = f"{c['name']}일주, {c['name']}일주 특징, {c['name']}일주 성격, {c['name']}일주 궁합, {c['name']}일주 연애, {c['hanja']}일주, {c['alias']}, {stem_name} 일간"

    siblings = [x for x in cat if x['stem'] == c['stem'] and x['name'] != c['name']]
    lis = lambda items: ''.join(f'<li>{e(t)}</li>' for t in items)

    def link(x):
        return f'<a href="/ilju/{x["slug"]}.html">{x["name"]}일주</a>'

    body = f'''
        <nav class="crumbs" aria-label="현재 위치">
            <a href="/ilju/">← 일주 60가지</a>
            <span class="dream-path"><a href="/ilju/{prev['slug']}.html">‹ {prev['name']}</a> <a href="/ilju/{nxt['slug']}.html">{nxt['name']} ›</a></span>
        </nav>

        <main>
            <header class="dream-hero stem-hero">
                <div class="ilju-glyph ilju-glyph--lg" aria-hidden="true"><span>{c['hanja'][0]}</span><span>{c['hanja'][1]}</span></div>
                <div class="eyebrow">60갑자 {c['order']}번째 · {e(c['alias'])}</div>
                <h1>{c['name']}일주 특징</h1>
                <p class="stem-image">{e(d['image'])}</p>
                <p class="dream-summary">{e(d['summary'])}</p>
                <div class="ilju-keywords">{''.join(f'<span>#{e(k)}</span>' for k in d['keywords'])}</div>
                <p class="ilju-meta">일간 <a href="/ilgan/{STEM_KEY[si]}.html">{stem_name}({c['hanja'][0]}{ELEM_HANJA[c['stem_element']]})</a> · 일지 {c['branch']}({c['hanja'][1]}{ELEM_HANJA[c['branch_element']]}) · {c['yinyang']}</p>
            </header>

            <section class="ilgan-today stem-today" id="ilju-today" data-stem="{si}" data-branch="{bi}" data-name="{c['name']}" aria-live="polite">
                <span class="skeleton skeleton-line" style="width:60%"></span>
                <span class="skeleton skeleton-line"></span>
                <span class="skeleton skeleton-line short"></span>
            </section>

            <section class="dream-section" aria-labelledby="h-pers">
                <h2 id="h-pers">{c['name']}일주의 성격</h2>
                <p>{e(d['personality'])}</p>
            </section>

            <div class="stem-lists">
                <section class="stem-list stem-list--good" aria-labelledby="h-str">
                    <h2 id="h-str">빛나는 점</h2>
                    <ul>{lis(d['strengths'])}</ul>
                </section>
                <section class="stem-list stem-list--care" aria-labelledby="h-cau">
                    <h2 id="h-cau">챙기면 좋은 점</h2>
                    <ul>{lis(d['cautions'])}</ul>
                </section>
            </div>

            <section class="dream-section" aria-labelledby="h-love">
                <h2 id="h-love">{c['name']}일주의 연애·관계</h2>
                <p>{e(d['love'])}</p>
            </section>
            <section class="dream-section" aria-labelledby="h-work">
                <h2 id="h-work">일·적성</h2>
                <p>{e(d['work'])}</p>
            </section>
            <section class="dream-section" aria-labelledby="h-money">
                <h2 id="h-money">재물을 대하는 방식</h2>
                <p>{e(d['money'])}</p>
            </section>

            <div class="stem-lists">
                <section class="stem-list stem-list--good" aria-labelledby="h-match">
                    <h2 id="h-match">잘 맞는 일주 · {link(hap)}</h2>
                    <p>{e(d['match'])}</p>
                </section>
                <section class="stem-list stem-list--care" aria-labelledby="h-fric">
                    <h2 id="h-fric">부딪히기 쉬운 일주 · {link(chung)}</h2>
                    <p>{e(d['friction'])}</p>
                </section>
            </div>

            <aside class="summary dream-advice" aria-label="{c['name']}일주에게 건네는 한마디">
                <div class="label">{c['name']}일주에게 건네는 한마디</div>
                <p>{e(d['advice'])}</p>
            </aside>

            <div class="share-row" data-share-title="{c['name']}일주 특징 — {e(c['alias'])}" data-share-text="{e(d['summary'])}" data-share-url="{url}">
                <button type="button" class="btn btn-kakao" data-share="kakao">카카오톡 공유</button>
                <button type="button" class="btn btn-ghost" data-share="link">링크 복사</button>
            </div>
        </main>

        <section class="dream-related" aria-labelledby="h-sib">
            <div class="section-head"><h2 id="h-sib">{stem_name} 일간의 다른 일주</h2><a class="dream-subhead-link" href="/ilgan/{STEM_KEY[si]}.html">{stem_name} 일간 보기</a></div>
            <div class="dream-chips">{''.join(f'<a class="chip" href="/ilju/{x["slug"]}.html"><span class="hanja" aria-hidden="true">{x["hanja"]}</span>{x["name"]}일주</a>' for x in siblings)}</div>
        </section>

        <a class="promo" href="/ilgan.html">
            <div>
                <h3>내 일주가 궁금하다면</h3>
                <p>생년월일만 넣으면 일주를 계산하고 오늘의 운세와 7일 흐름까지 보여드려요.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>
'''
    return head(title, d['summary'], url, keywords, ld=ld) + body + FOOT.replace(
        '<script src="/ilgan.js"></script>', '<script src="/ilgan.js"></script>\n    <script src="/dream/dream.js"></script>')


def index(cat, data, today):
    url = f'{SITE}/ilju/'
    title = '일주 60가지 특징 — 60갑자 일주별 성격·연애·궁합 | 홍스팟 운세'
    desc = '갑자일주부터 계해일주까지 60갑자 일주 60가지의 성격, 연애, 일·재물, 잘 맞는 일주를 한곳에서 찾아보세요. 생년월일로 내 일주도 바로 계산할 수 있어요.'
    ld = safe_json({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '일주 60가지', 'description': desc,
                    'url': url, 'inLanguage': 'ko-KR', 'isPartOf': {'@type': 'WebSite', 'name': '홍스팟 운세', 'url': SITE + '/'}})
    rows = ''
    for si, sname in enumerate(STEM_NAME):
        items = [x for x in cat if STEMS.index(x['stem']) == si]
        cards = ''.join(f'''
                <li><a class="dream-card ilju-card-link" href="/ilju/{x['slug']}.html">
                    <span class="dream-card-top"><strong>{x['name']}일주</strong><span class="ilju-hanja">{x['hanja']}</span></span>
                    <small>{e(x['alias'])} · {e(data[x['name']]['image'])}</small>
                </a></li>''' for x in items)
        rows += f'''
        <section class="dream-cat" id="stem-{STEM_KEY[si]}" aria-labelledby="h-{STEM_KEY[si]}">
            <div class="section-head"><h2 id="h-{STEM_KEY[si]}">{sname} 일간의 일주</h2><a class="dream-subhead-link" href="/ilgan/{STEM_KEY[si]}.html">{sname} 일간 보기</a></div>
            <ul class="dream-grid ilju-grid">{cards}
            </ul>
        </section>
'''
    body = f'''
        <section class="hero">
            <div class="eyebrow">60갑자 일주</div>
            <h1>일주 60가지,<br><em>나의 날</em>은 어떤 모습일까</h1>
            <p class="lead">태어난 날의 두 글자로 읽는 성격·연애·궁합</p>
            <a class="btn btn-gold" href="/ilgan.html" style="margin-top:18px">생년월일로 내 일주 찾기 →</a>
        </section>

        <nav class="dream-cat-tabs" aria-label="일간별 바로가기">{''.join(f'<a class="chip" href="#stem-{STEM_KEY[i]}">{n}</a>' for i, n in enumerate(STEM_NAME))}</nav>
{rows}
        <a class="promo" href="/ilgan.html">
            <div>
                <h3>오늘 내 일주의 운세는?</h3>
                <p>오늘 일진과 내 일주의 관계로 하루 운세와 7일 흐름을 보여드려요.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>
'''
    return head(title, desc, url, '일주, 60갑자, 일주 특징, 일주별 성격, 일주 궁합, 사주 일주', og_type='website', ld=ld) + body + FOOT


def update_sitemap(cat, today):
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    block = '  <!-- ilju:start -->\n'
    block += f'  <url><loc>{SITE}/ilju/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
    block += ''.join(f"  <url><loc>{SITE}/ilju/{x['slug']}.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.6</priority></url>\n" for x in cat)
    block += '  <!-- ilju:end -->\n'
    if '<!-- ilju:start -->' in s:
        s = re.sub(r'  <!-- ilju:start -->\n.*?  <!-- ilju:end -->\n', lambda m: block, s, flags=re.S)
    else:
        s = s.replace('</urlset>', block + '</urlset>')
    path.write_text(s, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    args = ap.parse_args()
    today = args.date or datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d')
    cat, data = load()
    by_name = {c['name']: c for c in cat}
    OUT.mkdir(exist_ok=True)
    for c in cat:
        (OUT / f"{c['slug']}.html").write_text(page(c, data[c['name']], cat, by_name, today), encoding='utf-8')
    (OUT / 'index.html').write_text(index(cat, data, today), encoding='utf-8')
    update_sitemap(cat, today)
    print(f'일주 페이지 {len(cat)}개 + 목록 → {OUT}')


if __name__ == '__main__':
    main()
