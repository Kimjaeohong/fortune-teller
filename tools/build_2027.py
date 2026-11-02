"""
2027년 띠별 운세 페이지 생성기

    python3 tools/build_2027.py

읽는 것: tools/y2027/data_*.json (띠별 본문)
만드는 것: 2027/index.html (허브), 2027/<띠>.html (12개), sitemap.xml 의 <!-- y2027:start --> 구간

띠 관계(합·충·삼재)는 전통 명리 기준이고, 본문은 재미로 읽는 풀이입니다.
"""
import json
import re

from site_common import (ROOT, SITE, ZODIAC, ZODIAC_ORDER, article_ld, e, hash_string, page_foot, page_head, safe_json,
                         stars_html, today_kst, update_block, url_line, LUCKY_COLORS, LUCKY_DIRECTIONS)

PUBLISHED = '2026-11-02'
OUT = ROOT / '2027'
BANNED = ['반드시', '무조건', '100%', '틀림없이', '진단', '처방', '복용', '꼭 사세요']
SEASONS = ['봄 (3~5월)', '여름 (6~8월)', '가을 (9~11월)', '겨울 (12~2월)']

FAQ = [
    ('2027년은 무슨 띠의 해인가요?', '2027년은 정미년(丁未年)으로 양띠의 해예요. 천간 정(丁)이 붉은색을 뜻해서 흔히 붉은 양의 해라고 불러요.'),
    ('2027년 삼재 띠는 무엇인가요?', '돼지띠, 토끼띠, 양띠가 삼재의 마지막 해인 날삼재에 해당해요. 2025년 을사년에 들삼재, 2026년 병오년에 눌삼재를 지났고 2027년 정미년에 끝나요. 호랑이띠, 말띠, 개띠의 들삼재는 2028년 무신년에 시작돼요.'),
    ('2027년 운이 좋은 띠는 무엇인가요?', '전통 풀이로는 해의 지지 미(未)와 육합을 이루는 말띠, 삼합의 일부인 토끼띠와 돼지띠, 방합을 이루는 뱀띠를 좋은 흐름으로 꼽아요. 재미로 보는 해석이니 참고만 해 주세요.'),
    ('1~2월생은 어떤 띠로 봐야 하나요?', '설날을 기준으로 보는 방식과 입춘을 기준으로 보는 방식이 있어요. 2027년 설날은 2월 7일, 입춘은 2월 4일이에요. 그 전에 태어났다면 전년도 띠로 보는 경우가 많아요.'),
]


def load():
    data = {}
    for p in sorted((ROOT / 'tools' / 'y2027').glob('data_*.json')):
        for item in json.loads(p.read_text(encoding='utf-8')):
            data[item['key']] = item
    missing = [k for k in ZODIAC_ORDER if k not in data]
    if missing:
        raise SystemExit(f'본문이 없는 띠: {missing}')
    for k, d in data.items():
        text = json.dumps(d, ensure_ascii=False)
        bad = [w for w in BANNED if w in text]
        if bad:
            raise SystemExit(f'{k}: 쓰면 안 되는 표현 {bad}')
        if len(d['years']) < 5 or len(d['seasons']) != 4:
            raise SystemExit(f'{k}: 출생연도 또는 계절 항목 부족')
        for y in d['years']:
            if (int(y) - 4) % 12 != ZODIAC_ORDER.index(k):
                raise SystemExit(f'{k}: {y}년생은 이 띠가 아님')
    return data


def year_title(d):
    ys = sorted(d['years'])
    return '·'.join(y[2:] for y in ys[:4])


def lucky(k):
    h = hash_string(f'2027:{k}')
    return LUCKY_COLORS[h % len(LUCKY_COLORS)], (h // 7) % 45 + 1, LUCKY_DIRECTIONS[(h // 331) % len(LUCKY_DIRECTIONS)]


def page(k, d):
    name, hanja, emoji = ZODIAC[k]
    url = f'{SITE}/2027/{k}.html'
    ys = sorted(d['years'])
    title = f'2027년 {name} 운세 — {year_title(d)}년생 정미년 신년운세 | 홍스팟 운세'
    keywords = f'2027년 {name} 운세, 2027 {name}, 정미년 {name}, {name} 신년운세, ' + ', '.join(f'{y[2:]}년생 2027년 운세' for y in ys)
    ld = article_ld(url, f'2027년 {name} 운세', d['summary'], PUBLISHED, today_kst(),
                    [('홍스팟 운세', SITE + '/'), ('2027년 운세', SITE + '/2027/'), (name, url)])
    i = ZODIAC_ORDER.index(k)
    prev, nxt = ZODIAC_ORDER[(i + 11) % 12], ZODIAC_ORDER[(i + 1) % 12]
    color, number, direction = lucky(k)
    cats = [('재물운', 'money', '#e3c26b'), ('직장·사업운', 'work', '#8fa8e0'), ('연애·인연운', 'love', '#e08a7a'), ('건강운', 'health', '#86c2a8')]
    cat_html = ''.join(f'''
                <article class="fortune-item">
                    <header><h2><span class="cat-dot" style="color:{c};background:{c}"></span>2027년 {name} {t}</h2></header>
                    <p>{e(d[f])}</p>
                </article>''' for t, f, c in cats)
    season_html = ''.join(f'<li><b>{s}</b><span>{e(t)}</span></li>' for s, t in zip(SEASONS, d['seasons']))
    year_html = ''.join(f'''
                <li id="y{y}"><b>{y}년생</b><span>{e(t)}</span></li>''' for y, t in sorted(d['years'].items()))
    chips = ''.join(f'<a class="chip" href="/2027/{x}.html"{" aria-current=\"page\"" if x == k else ""}><span class="hanja" aria-hidden="true">{ZODIAC[x][1]}</span>{ZODIAC[x][0]}</a>' for x in ZODIAC_ORDER)
    body = f'''
        <nav class="crumbs" aria-label="현재 위치">
            <a href="/2027/">← 2027년 띠별 운세</a>
            <span class="dream-path"><a href="/2027/{prev}.html">‹ {ZODIAC[prev][0]}</a> <a href="/2027/{nxt}.html">{ZODIAC[nxt][0]} ›</a></span>
        </nav>

        <main>
            <section class="detail-hero">
                <div class="hanja-lg" aria-hidden="true">{hanja}</div>
                <h1>2027년 {name} 운세</h1>
                <p class="meta">정미년 · {e(d['relation'])} · {e(d['tag'])}</p>
                <p class="years">{' · '.join(f'{y}년생' for y in ys)}</p>
                <div class="score">{stars_html(d['score'])}</div>
            </section>

            <div class="summary">
                <div class="label">2027년 한눈에 보기</div>
                <p>{e(d['summary'])}</p>
            </div>

            <section class="dream-section" aria-labelledby="h-all">
                <h2 id="h-all">2027년 {name} 총운</h2>
                <p>{e(d['overall'])}</p>
            </section>

            <div class="fortune-list">{cat_html}
            </div>

            <section class="dream-section" aria-labelledby="h-year">
                <h2 id="h-year">{name} 출생연도별 2027년 운세</h2>
                <ul class="y27-list">{year_html}
                </ul>
            </section>

            <section class="dream-section" aria-labelledby="h-season">
                <h2 id="h-season">2027년 {name} 계절별 흐름</h2>
                <ul class="y27-list">{season_html}</ul>
            </section>

            <div class="lucky" aria-label="2027년 행운 아이템">
                <div class="lucky-item"><div class="k">행운의 색</div><div class="v"><span class="swatch" style="background:{color[1]}"></span>{color[0]}</div></div>
                <div class="lucky-item"><div class="k">행운의 숫자</div><div class="v">{number}</div></div>
                <div class="lucky-item"><div class="k">행운의 방향</div><div class="v">{direction}</div></div>
            </div>

            <aside class="summary dream-advice" aria-label="2027년 {name}에게 건네는 한마디">
                <div class="label">2027년 {name}에게 건네는 한마디</div>
                <p>{e(d['advice'])}</p>
            </aside>

            <div class="share-row" data-share-title="2027년 {name} 운세" data-share-text="{e(d['summary'])}" data-share-url="{url}">
                <button type="button" class="btn btn-kakao" data-share="kakao">카카오톡 공유</button>
                <button type="button" class="btn btn-ghost" data-share="link">링크 복사</button>
            </div>
        </main>

        <section class="others">
            <div class="section-head"><h2>다른 띠 2027년 운세</h2></div>
            <nav class="chip-row" aria-label="다른 띠">{chips}</nav>
        </section>

        <a class="promo" href="/zodiac/{k}.html">
            <div>
                <h3>{name} 오늘의 운세</h3>
                <p>매일 자정 바뀌는 종합운·재물운·인연운과 행운 아이템까지.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>
'''
    return page_head(title, d['summary'], url, keywords, ld=ld) + body + page_foot('2027년 운세는 전해 내려오는 해석을 재미로 정리한 거예요', '건강·돈·관계의 중요한 결정은 현실의 정보로 내려 주세요')


def hub(data):
    url = f'{SITE}/2027/'
    title = '2027년 띠별 운세 — 정미년 12띠 신년운세·삼재 띠 총정리 | 홍스팟 운세'
    desc = '2027년 정미년 붉은 양의 해, 12띠 신년운세를 한곳에 모았어요. 띠별 총운과 재물·직장·연애운, 출생연도별 흐름, 2027년 삼재 띠까지 무료로 확인해 보세요.'
    keywords = '2027년 운세, 2027 띠별 운세, 정미년 운세, 2027 신년운세, 2027 삼재, 2027년 삼재 띠, 붉은 양의 해'
    org = {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'}
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': '2027년 띠별 운세', 'description': desc, 'url': url, 'inLanguage': 'ko-KR', 'publisher': org,
         'isPartOf': {'@type': 'WebSite', 'name': '홍스팟 운세', 'url': SITE + '/'}},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ]}]}
    cards = ''
    for i, k in enumerate(ZODIAC_ORDER):
        name, hanja, emoji = ZODIAC[k]
        d = data[k]
        ys = ' · '.join(y[2:] for y in sorted(d['years']))
        cards += f'''
            <a class="zodiac-card" href="/2027/{k}.html" style="animation-delay:{i * 35}ms">
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">{hanja}</span>
                    <div class="zc-name">{name}<span class="zc-emoji" aria-hidden="true">{emoji}</span></div>
                </div>
                <div class="zc-years">{ys}년생</div>
                <p class="zc-line">{e(d['tag'])}</p>
                <div class="zc-foot">{stars_html(d['score'], label=False)}<span class="rank-badge">{e(d['relation'].split(' · ')[0].replace('특별한 합충 없음', '무난'))}</span></div>
            </a>'''
    faq = ''.join(f'''
            <section class="dream-section">
                <h3>{e(q)}</h3>
                <p>{e(a)}</p>
            </section>''' for q, a in FAQ)
    body = f'''
        <section class="hero">
            <div class="eyebrow">2027 정미년 · 붉은 양의 해</div>
            <h1>2027년 <em>띠별 운세</em></h1>
            <p class="lead">12띠 총운 · 재물 · 직장 · 연애 · 출생연도별 흐름</p>
        </section>

        <div class="section-head">
            <h2>12띠 2027년 운세</h2>
            <span>카드를 눌러 자세히 보기</span>
        </div>
        <div class="zodiac-grid">{cards}
        </div>

        <main>
            <section class="dream-section" aria-labelledby="h-year">
                <h2 id="h-year">2027년 정미년은 어떤 해인가요</h2>
                <p>2027년은 60갑자의 44번째인 정미년(丁未年)이에요. 천간 정(丁)은 촛불이나 등불처럼 은은하게 오래 타는 불을, 지지 미(未)는 한여름의 마른 흙과 양을 뜻해요. 그래서 2026년 병오년의 강렬한 불기운이 차분하게 가라앉으며, 벌여 놓은 일을 다지고 관계를 정리하는 흐름으로 풀이해요.</p>
            </section>

            <section class="dream-section" aria-labelledby="h-sam">
                <h2 id="h-sam">2027년 삼재 띠</h2>
                <p><a href="/2027/pig.html">돼지띠</a>, <a href="/2027/rabbit.html">토끼띠</a>, <a href="/2027/sheep.html">양띠</a>가 삼재의 마지막 해인 날삼재에 해당해요. 2025년 들삼재, 2026년 눌삼재를 지나 2027년에 삼재가 끝나요. 끝맺음의 해라 시작보다 마무리에 힘을 쓰는 게 좋다고 풀이해요.</p>
            </section>

            <section class="dream-section" aria-labelledby="h-rel">
                <h2 id="h-rel">2027년 띠별 궁합 관계</h2>
                <ul class="y27-list">
                    <li><b>잘 맞는 띠</b><span><a href="/2027/horse.html">말띠</a>(오미 육합), <a href="/2027/rabbit.html">토끼띠</a>·<a href="/2027/pig.html">돼지띠</a>(해묘미 반합), <a href="/2027/snake.html">뱀띠</a>(사오미 방합)</span></li>
                    <li><b>내 해</b><span><a href="/2027/sheep.html">양띠</a>(본명년)</span></li>
                    <li><b>조심할 띠</b><span><a href="/2027/ox.html">소띠</a>(축미충), <a href="/2027/dog.html">개띠</a>(술미 형·파), <a href="/2027/rat.html">쥐띠</a>(자미 원진), <a href="/2027/tiger.html">호랑이띠</a>(인미 귀문)</span></li>
                    <li><b>무난한 띠</b><span><a href="/2027/dragon.html">용띠</a>, <a href="/2027/monkey.html">원숭이띠</a>, <a href="/2027/rooster.html">닭띠</a></span></li>
                </ul>
            </section>

            <section class="dream-faq" aria-labelledby="h-faq">
                <div class="section-head"><h2 id="h-faq">자주 묻는 질문</h2></div>{faq}
            </section>

            <div class="share-row" data-share-title="2027년 띠별 운세" data-share-text="{e(desc)}" data-share-url="{url}">
                <button type="button" class="btn btn-kakao" data-share="kakao">카카오톡 공유</button>
                <button type="button" class="btn btn-ghost" data-share="link">링크 복사</button>
            </div>
        </main>

        <a class="promo" href="/ilgan.html">
            <div>
                <h3>띠보다 자세히 보고 싶다면</h3>
                <p>생년월일로 내 일주를 찾고 오늘의 운세와 7일 흐름을 확인해 보세요.</p>
            </div>
            <span class="arrow" aria-hidden="true">→</span>
        </a>
    </div>
'''
    return page_head(title, desc, url, keywords, og_type='website', ld=ld, narrow=False) + body + page_foot('2027년 운세는 전해 내려오는 해석을 재미로 정리한 거예요', '건강·돈·관계의 중요한 결정은 현실의 정보로 내려 주세요')


def main():
    data = load()
    OUT.mkdir(exist_ok=True)
    for k in ZODIAC_ORDER:
        (OUT / f'{k}.html').write_text(page(k, data[k]), encoding='utf-8')
    (OUT / 'index.html').write_text(hub(data), encoding='utf-8')
    day = today_kst()
    block = url_line(f'{SITE}/2027/', day, 'weekly', '0.9') + ''.join(url_line(f'{SITE}/2027/{k}.html', day, 'monthly', '0.8') for k in ZODIAC_ORDER)
    update_block('y2027', block)
    print(f'2027년 운세 페이지 {len(ZODIAC_ORDER)}개 + 허브 → {OUT}')


if __name__ == '__main__':
    main()
