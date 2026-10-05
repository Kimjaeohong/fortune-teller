"""
일간(日干) 운세 생성기

    python3 tools/build_ilgan.py

읽는 것: tools/ilgan/profiles.json (일간 10가지 성격 소개), tools/ilgan/sipsin.json (십신별 하루 운세 문장)
만드는 것:
    ilgan-data.js        ilgan.js 가 쓰는 문장 데이터
    ilgan/<key>.html     일간 소개 페이지 10개 (gap, eul, byeong, jeong, mu, gi, gyeong, sin, im, gye)
    sitemap.xml          <!-- ilgan:start --> ~ <!-- ilgan:end --> 구간

하루 운세 자체는 데이터 파일 없이 브라우저에서 날짜로 계산합니다 (기한 없음).
"""
import argparse
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'ilgan'
OUT = ROOT / 'ilgan'
SITE = 'https://fortune.hongspot.com'

ORDER = ['gap', 'eul', 'byeong', 'jeong', 'mu', 'gi', 'gyeong', 'sin', 'im', 'gye']
SIPSIN = ['bigyeon', 'geopjae', 'siksin', 'sanggwan', 'pyeonjae', 'jeongjae',
          'pyeongwan', 'jeonggwan', 'pyeonin', 'jeongin']
ELEM_HANJA = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}
BRANCH_HANJA = dict(zip('자축인묘진사오미신유술해', '子丑寅卯辰巳午未申酉戌亥'))
BRANCH_KEY = dict(zip('자축인묘진사오미신유술해', ['ja', 'chuk', 'in', 'myo', 'jin', 'sa', 'o', 'mi', 'sin', 'yu', 'sul', 'hae']))

NAV_ITEMS = [('/', '띠별 운세'), ('/ilgan.html', '사주'), ('/invest.html', '투자운'), ('/star.html', '별자리'),
             ('/dream/', '꿈해몽'), ('/name.html', '궁합'), ('/tarot.html', '타로'), ('/lotto.html', '로또')]

e = html.escape


def josa(word, with_final, without_final):
    code = ord(word[-1]) - 0xAC00
    return word + (with_final if 0 <= code <= 11171 and code % 28 else without_final)


def safe_json(obj, **kw):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), **kw).replace('</', '<\\/')


def load():
    profiles = json.loads((SRC / 'profiles.json').read_text(encoding='utf-8'))
    sipsin = json.loads((SRC / 'sipsin.json').read_text(encoding='utf-8'))
    assert [p['key'] for p in profiles] == ORDER, '일간 순서/키가 다름'
    assert sorted(sipsin['sipsin']) == sorted(SIPSIN), '십신 키가 다름'
    assert sorted(sipsin['branch']) == ['chung', 'hap', 'same', 'samhap'], '지지 관계 키가 다름'
    return profiles, sipsin


def write_data_js(profiles, sipsin):
    data = {
        'sipsin': sipsin['sipsin'],
        'branch': sipsin['branch'],
        'ilgan': [{'key': p['key'], 'name': p['name'], 'hanja': p['hanja'], 'image': p['image'],
                   'element': p['element']} for p in profiles],
    }
    (ROOT / 'ilgan-data.js').write_text(
        '// tools/build_ilgan.py 가 만든 파일 — 직접 고치지 말고 tools/ilgan/*.json 을 고친 뒤 다시 생성하세요\n'
        'const ILGAN_DATA = ' + safe_json(data) + ';\n', encoding='utf-8')


def nav_html(current):
    return ''.join(
        f'                <a href="{href}"{" aria-current=" + chr(34) + "page" + chr(34) if href == current else ""}>{label}</a>\n'
        for href, label in NAV_ITEMS)


def page(p, profiles, idx, today):
    key = p['key']
    url = f'{SITE}/ilgan/{key}.html'
    eh = ELEM_HANJA[p['element']]
    full = f"{p['name']}({p['hanja']}{eh})"
    title = f"{p['name']}({p['hanja']}{eh}) 일간 성격과 특징 · 오늘의 운세 | 홍스팟 운세"
    desc = p['summary']

    ld = safe_json({
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'Article', 'headline': f"{p['name']} 일간 성격과 특징", 'description': desc,
             'inLanguage': 'ko-KR', 'mainEntityOfPage': url, 'image': f'{SITE}/fortune-image.png',
             'datePublished': today, 'dateModified': today,
             'author': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'},
             'publisher': {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': '홍스팟 운세', 'item': SITE + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': '사주 일진', 'item': SITE + '/ilgan.html'},
                {'@type': 'ListItem', 'position': 3, 'name': f"{p['name']} 일간", 'item': url}]},
        ],
    })

    ilju = ''.join(f'''
                <article class="dream-case ilju-item" id="ilju-{name}">
                    <header><h3><a href="/ilju/{p['key']}-{BRANCH_KEY[name[1]]}.html">{name}일주</a> <small>{p['hanja']}{BRANCH_HANJA[name[1]]}</small></h3></header>
                    <p>{e(text)} <a class="ilju-more" href="/ilju/{p['key']}-{BRANCH_KEY[name[1]]}.html">자세히 →</a></p>
                </article>''' for name, text in p['ilju'].items())

    others = ''.join(
        f'<a class="chip" href="/ilgan/{q["key"]}.html"><span class="hanja" aria-hidden="true">{q["hanja"]}</span>{q["name"]}</a>'
        for q in profiles if q['key'] != key)

    lis = lambda items: ''.join(f'<li>{e(t)}</li>' for t in items)

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(title)}</title>
    <meta name="description" content="{e(desc)}">
    <meta name="keywords" content="{p['name']} 일간, {p['name']} 성격, {p['stem']}{p['element']} 일간 특징, {p['hanja']}{eh}, 일간 성격, {', '.join(n + '일주' for n in p['ilju'])}">
    <meta name="theme-color" content="#0c0f1d">
    <link rel="canonical" href="{url}">

    <meta property="og:type" content="article">
    <meta property="og:site_name" content="홍스팟 운세">
    <meta property="og:title" content="{e(p['name'])} 일간 성격과 특징 · 오늘의 운세">
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
{nav_html('/ilgan.html')}            </nav>
        </header>

        <nav class="crumbs" aria-label="현재 위치">
            <a href="/ilgan.html">← 사주 일진</a>
            <span class="dream-path">{'<a href="/ilgan/' + profiles[idx - 1]['key'] + '.html">‹ ' + profiles[idx - 1]['name'] + '</a>'} {'<a href="/ilgan/' + profiles[(idx + 1) % 10]['key'] + '.html">' + profiles[(idx + 1) % 10]['name'] + ' ›</a>'}</span>
        </nav>

        <main>
            <header class="dream-hero stem-hero">
                <div class="stem-glyph" aria-hidden="true">{p['hanja']}</div>
                <div class="eyebrow">일간 · 오행 {p['element']}({eh}) · {p['yinyang']}</div>
                <h1>{e(p['name'])} 일간 성격과 특징</h1>
                <p class="stem-image">{e(p['image'])}</p>
                <p class="dream-summary">{e(p['summary'])}</p>
            </header>

            <section class="ilgan-today stem-today" id="stem-today" data-stem="{idx}" aria-live="polite">
                <span class="skeleton skeleton-line" style="width:60%"></span>
                <span class="skeleton skeleton-line"></span>
                <span class="skeleton skeleton-line short"></span>
            </section>

            <section class="dream-section" aria-labelledby="h-pers">
                <h2 id="h-pers">{e(full)}{josa(p['name'], '은', '는')[len(p['name']):]} 어떤 사람일까</h2>
                <p>{e(p['personality'])}</p>
            </section>

            <div class="stem-lists">
                <section class="stem-list stem-list--good" aria-labelledby="h-str">
                    <h2 id="h-str">빛나는 점</h2>
                    <ul>{lis(p['strengths'])}</ul>
                </section>
                <section class="stem-list stem-list--care" aria-labelledby="h-cau">
                    <h2 id="h-cau">챙기면 좋은 점</h2>
                    <ul>{lis(p['cautions'])}</ul>
                </section>
            </div>

            <section class="dream-section" aria-labelledby="h-love">
                <h2 id="h-love">연애·관계</h2>
                <p>{e(p['love'])}</p>
            </section>
            <section class="dream-section" aria-labelledby="h-work">
                <h2 id="h-work">일·적성</h2>
                <p>{e(p['work'])}</p>
            </section>
            <section class="dream-section" aria-labelledby="h-money">
                <h2 id="h-money">돈을 대하는 방식</h2>
                <p>{e(p['money'])}</p>
            </section>
            <section class="dream-section" aria-labelledby="h-self">
                <h2 id="h-self">나를 돌보는 법</h2>
                <p>{e(p['selfcare'])}</p>
            </section>

            <div class="stem-lists">
                <section class="stem-list stem-list--good" aria-labelledby="h-match">
                    <h2 id="h-match">잘 어울리는 일간</h2>
                    <p>{e(p['good_match'])}</p>
                </section>
                <section class="stem-list stem-list--care" aria-labelledby="h-fric">
                    <h2 id="h-fric">부딪히기 쉬운 일간</h2>
                    <p>{e(p['friction'])}</p>
                </section>
            </div>

            <section class="dream-section dream-cases" aria-labelledby="h-ilju">
                <h2 id="h-ilju">{e(josa(p['stem'], '으로', '로'))} 시작하는 일주 6가지</h2>{ilju}
            </section>
        </main>

        <section class="dream-related" aria-labelledby="h-others">
            <div class="section-head"><h2 id="h-others">다른 일간 보기</h2></div>
            <div class="dream-chips">{others}</div>
        </section>

        <a class="promo" href="/ilgan.html">
            <div>
                <h3>내 일주가 궁금하다면</h3>
                <p>생년월일만 넣으면 일주를 계산하고 오늘의 운세와 7일 흐름까지 보여드려요.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>

    <footer class="footer">
        <p>일간 풀이는 전해 내려오는 해석을 재미로 정리한 거예요</p>
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


def update_sitemap(today):
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    block = '  <!-- ilgan:start -->\n'
    block += f'  <url><loc>{SITE}/ilgan.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n'
    block += ''.join(f'  <url><loc>{SITE}/ilgan/{k}.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.7</priority></url>\n'
                     for k in ORDER)
    block += '  <!-- ilgan:end -->\n'
    if '<!-- ilgan:start -->' in s:
        s = re.sub(r'  <!-- ilgan:start -->\n.*?  <!-- ilgan:end -->\n', lambda m: block, s, flags=re.S)
    else:
        s = s.replace('</urlset>', block + '</urlset>')
    path.write_text(s, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='lastmod 날짜 (기본: 오늘, 한국시간)')
    args = ap.parse_args()
    today = args.date or datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d')
    profiles, sipsin = load()
    write_data_js(profiles, sipsin)
    OUT.mkdir(exist_ok=True)
    for i, p in enumerate(profiles):
        (OUT / f"{p['key']}.html").write_text(page(p, profiles, i, today), encoding='utf-8')
    update_sitemap(today)
    print(f'ilgan-data.js + 일간 페이지 {len(profiles)}개 → {OUT}')


if __name__ == '__main__':
    main()
