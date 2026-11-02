"""
생성기 공용 부품: 페이지 머리·꼬리, 날짜(한국시간), 별점 마크업, 행운 아이템·로또 번호

행운 아이템과 로또 번호는 common.js / lotto.js 와 같은 계산이라야 화면에서 같은 값이 나옵니다.
거기를 고치면 여기도 같이 고치세요.
"""
import html
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://fortune.hongspot.com'
KST = timezone(timedelta(hours=9))
e = html.escape

NAV_ITEMS = [('/', '띠별 운세'), ('/ilgan.html', '사주'), ('/invest.html', '투자운'), ('/star.html', '별자리'),
             ('/dream/', '꿈해몽'), ('/name.html', '궁합'), ('/tarot.html', '타로'), ('/lotto.html', '로또')]

ZODIAC_ORDER = ['rat', 'ox', 'tiger', 'rabbit', 'dragon', 'snake', 'horse', 'sheep', 'monkey', 'rooster', 'dog', 'pig']
ZODIAC = {
    'rat': ('쥐띠', '子', '🐭'), 'ox': ('소띠', '丑', '🐮'), 'tiger': ('호랑이띠', '寅', '🐯'),
    'rabbit': ('토끼띠', '卯', '🐰'), 'dragon': ('용띠', '辰', '🐲'), 'snake': ('뱀띠', '巳', '🐍'),
    'horse': ('말띠', '午', '🐴'), 'sheep': ('양띠', '未', '🐑'), 'monkey': ('원숭이띠', '申', '🐵'),
    'rooster': ('닭띠', '酉', '🐔'), 'dog': ('개띠', '戌', '🐶'), 'pig': ('돼지띠', '亥', '🐷'),
}
STAR_ORDER = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius',
              'capricorn', 'aquarius', 'pisces']
# 이름, 기호, 기간, 원소, 수호성 (config.js 의 STAR_INFO 와 같게)
STAR = {
    'aries': ('양자리', '♈︎', '3.21 ~ 4.19', '불', '화성'), 'taurus': ('황소자리', '♉︎', '4.20 ~ 5.20', '흙', '금성'),
    'gemini': ('쌍둥이자리', '♊︎', '5.21 ~ 6.21', '공기', '수성'), 'cancer': ('게자리', '♋︎', '6.22 ~ 7.22', '물', '달'),
    'leo': ('사자자리', '♌︎', '7.23 ~ 8.22', '불', '태양'), 'virgo': ('처녀자리', '♍︎', '8.23 ~ 9.23', '흙', '수성'),
    'libra': ('천칭자리', '♎︎', '9.24 ~ 10.22', '공기', '금성'), 'scorpio': ('전갈자리', '♏︎', '10.23 ~ 11.22', '물', '명왕성'),
    'sagittarius': ('사수자리', '♐︎', '11.23 ~ 12.24', '불', '목성'), 'capricorn': ('염소자리', '♑︎', '12.25 ~ 1.19', '흙', '토성'),
    'aquarius': ('물병자리', '♒︎', '1.20 ~ 2.18', '공기', '천왕성'), 'pisces': ('물고기자리', '♓︎', '2.19 ~ 3.20', '물', '해왕성'),
}
CATEGORIES = [('overall', '종합운'), ('money', '재물운'), ('work', '일·학업운'), ('health', '건강운'), ('relationship', '인연·관계운')]
CATEGORY_COLORS = {'money': '#e3c26b', 'work': '#8fa8e0', 'health': '#86c2a8', 'relationship': '#e08a7a'}
WEEKDAYS = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

HEAD_FONT = '''    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/styles.css">
'''

FOOT_LINKS = '<a href="/about.html">사이트 소개</a> · <a href="/privacy.html">개인정보처리방침</a>'


def today_kst():
    return datetime.now(KST).strftime('%Y-%m-%d')


def korean_date(s):
    d = date.fromisoformat(s)
    wd = WEEKDAYS[d.weekday()]
    return {'full': f'{d.year}년 {d.month}월 {d.day}일 {wd}', 'short': f'{d.month}월 {d.day}일', 'weekday': wd, 'year': d.year}


def safe_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def nav_html(current=None):
    out = []
    for href, label in NAV_ITEMS:
        cur = ' aria-current="page"' if href == current else ''
        out.append(f'                <a href="{href}"{cur}>{label}</a>\n')
    return ''.join(out)


def page_head(title, desc, url, keywords='', og_type='article', ld=None, current=None, narrow=True):
    kw = f'    <meta name="keywords" content="{e(keywords)}">\n' if keywords else ''
    ld_tag = f'    <script type="application/ld+json">{safe_json(ld)}</script>\n' if ld else ''
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(title)}</title>
    <meta name="description" content="{e(desc)}">
{kw}    <meta name="theme-color" content="#0c0f1d">
    <link rel="canonical" href="{url}">
    <link rel="alternate" type="application/rss+xml" title="홍스팟 운세" href="{SITE}/feed.xml">

    <meta property="og:type" content="{og_type}">
    <meta property="og:site_name" content="홍스팟 운세">
    <meta property="og:title" content="{e(title.split(' | ')[0])}">
    <meta property="og:description" content="{e(desc)}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{SITE}/fortune-image.png">
    <meta name="twitter:card" content="summary">

    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2248%22 fill=%22%230c0f1d%22/><text x=%2250%22 y=%2268%22 font-size=%2252%22 text-anchor=%22middle%22 fill=%22%23d9b673%22>福</text></svg>">

{HEAD_FONT}
    <!-- Google AdSense 자동 광고 -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2438640431184534" crossorigin="anonymous"></script>
    <!-- 카카오톡 공유 SDK -->
    <script defer src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js" crossorigin="anonymous"></script>
{ld_tag}</head>
<body>
    <div class="page{' page--narrow' if narrow else ''}">
        <header class="topbar">
            <a href="/" class="brand"><span class="brand-mark">福</span><span class="brand-text">홍스팟 운세</span></a>
            <nav class="nav" aria-label="주요 메뉴">
{nav_html(current)}            </nav>
        </header>
'''


def page_foot(note='운세는 재미로만 봐 주세요', note2=''):
    n2 = f'        <p>{e(note2)}</p>\n' if note2 else ''
    return f'''
    <footer class="footer">
        <p>{e(note)}</p>
{n2}        <p>{FOOT_LINKS}</p>
    </footer>

    <script src="/config.js"></script>
    <script src="/common.js"></script>
    <script src="/dream/dream.js"></script>
</body>
</html>
'''


def article_ld(url, headline, desc, published, modified, crumbs):
    org = {'@type': 'Organization', 'name': '홍스팟 운세', 'url': SITE + '/'}
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': headline, 'description': desc, 'inLanguage': 'ko-KR', 'mainEntityOfPage': url,
         'image': f'{SITE}/fortune-image.png', 'datePublished': published, 'dateModified': modified,
         'author': org, 'publisher': org},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]}]}


def update_block(name, block):
    """sitemap.xml 의 <!-- name:start --> ~ <!-- name:end --> 구간을 새로 쓴다"""
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    new = f'  <!-- {name}:start -->\n{block}  <!-- {name}:end -->\n'
    if f'<!-- {name}:start -->' in s:
        s = re.sub(rf'  <!-- {name}:start -->\n.*?  <!-- {name}:end -->\n', lambda m: new, s, flags=re.S)
    else:
        s = s.replace('</urlset>', new + '</urlset>')
    path.write_text(s, encoding='utf-8')


def url_line(url, lastmod, freq='weekly', prio='0.7'):
    return f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>\n'


# ── 화면 마크업 (common.js 와 같은 모양) ──────────────────

def score_label(s):
    return '아주 좋음' if s >= 4.5 else '좋음' if s >= 3.5 else '무난' if s >= 2.5 else '신중하게'


def stars_html(score, label=True):
    if score is None:
        return ''
    out = '<span class="stars" aria-hidden="true">'
    for i in range(1, 6):
        cls = 'on' if score >= i else ('half' if score >= i - 0.5 else '')
        out += f'<i class="{cls}">★</i>'
    out += '</span>' + f'<span class="sr-only">행운 지수 5점 중 {score}점</span>'
    return out + (f'<span class="stars-label">{score_label(score)}</span>' if label else '')


def first_sentence(text):
    t = re.sub(r'\s+', ' ', str(text or '').replace('**', '')).strip()
    m = re.match(r'^.*?[.!?](?=\s|$)', t)
    return m.group(0) if m else t


def ball_class(n):
    return 'b1' if n <= 10 else 'b2' if n <= 20 else 'b3' if n <= 30 else 'b4' if n <= 40 else 'b5'


def balls_html(nums, lucky=None):
    return '<div class="balls">' + ''.join(
        f'<span class="ball {ball_class(n)}{" is-fixed" if n == lucky else ""}">{n}</span>' for n in nums) + '</div>'


def years_for(key, upto):
    idx = ZODIAC_ORDER.index(key)
    return [y for y in range(1946, upto + 1) if (y - 4) % 12 == idx]


# ── 행운 아이템·로또 번호 (common.js / lotto.js 와 같은 계산) ─────

def hash_string(s):
    h = 2166136261
    data = s.encode('utf-16-le')
    for i in range(0, len(data), 2):
        h ^= data[i] | (data[i + 1] << 8)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


LUCKY_COLORS = [('버건디', '#8c2f39'), ('올리브', '#7a7d3a'), ('네이비', '#23345c'), ('머스터드', '#d4a72c'),
                ('라벤더', '#a697cf'), ('민트', '#8fcfb8'), ('코랄', '#ef8a6f'), ('베이지', '#d9c6a5'),
                ('스카이블루', '#7fb4e0'), ('포레스트 그린', '#2f5d4a'), ('화이트', '#f3f0e8'), ('차콜', '#3a3a3f')]
LUCKY_DIRECTIONS = ['동쪽', '서쪽', '남쪽', '북쪽', '동남쪽', '동북쪽', '서남쪽', '서북쪽']
LUCKY_TIMES = ['이른 아침', '오전', '점심 무렵', '오후', '해 질 녘', '저녁', '늦은 밤']


def lucky_items(date_str, key):
    h = hash_string(f'{date_str}:{key}')
    return {'color': LUCKY_COLORS[h % len(LUCKY_COLORS)], 'number': (h // 7) % 45 + 1,
            'direction': LUCKY_DIRECTIONS[(h // 331) % len(LUCKY_DIRECTIONS)],
            'time': LUCKY_TIMES[(h // 2417) % len(LUCKY_TIMES)]}


def _imul(a, b):
    return (a * b) & 0xFFFFFFFF


def mulberry32(seed):
    a = [seed & 0xFFFFFFFF]

    def rand():
        a[0] = (a[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = a[0]
        t = _imul(t ^ (t >> 15), t | 1)
        t = t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF)
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rand


def lotto_numbers(date_str, zodiac):
    """로또 페이지에서 그 띠로 뽑았을 때 나오는 A게임과 같은 번호 (행운의 숫자 포함)"""
    rand = mulberry32(hash_string('|'.join([date_str, f'zodiac:{zodiac}', '', ''])))
    lucky = lucky_items(date_str, zodiac)['number']
    picked = {lucky}
    pool = [n for n in range(1, 46) if n != lucky]
    while len(picked) < 6:
        picked.add(pool.pop(int(rand() * len(pool))))
    return sorted(picked), lucky


def next_draw(date_str):
    d = date.fromisoformat(date_str)
    draw = d + timedelta(days=(5 - d.weekday()) % 7)
    return (draw - date(2002, 12, 7)).days // 7 + 1, draw
