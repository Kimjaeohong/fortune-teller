"""
사이트맵 수정일 · RSS · 변경 주소 목록을 한 번에 관리

    python3 tools/site_index.py            # 생성기를 모두 돌린 뒤 마지막에 실행
    python3 tools/site_index.py --init     # 지금 상태를 기준점으로 저장 (수정일은 사이트맵 값 유지)

하는 일
    1) sitemap.xml 의 주소마다 본문(<body>~<footer>)의 해시를 tools/site_state.json 과 비교
    2) 본문이 실제로 바뀐 페이지만 lastmod 를 오늘로 바꿈 (푸터·메타만 바뀐 건 수정으로 치지 않음)
    3) feed.xml 을 최신 글 기준으로 새로 씀 (날마다 내용만 바뀌는 띠별·별자리·투자운 페이지는 제외)
    4) 바뀐 주소를 tools/.changed_urls 에 적음 → tools/indexnow.py 가 읽어서 검색엔진에 알림
"""
import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://fortune.hongspot.com'
STATE = ROOT / 'tools' / 'site_state.json'
CHANGED = ROOT / 'tools' / '.changed_urls'
KST = timezone(timedelta(hours=9))
FEED_LIMIT = 30
FEED_SKIP = ('/zodiac/', '/star/', '/invest/')


def file_for(url):
    path = url.replace(SITE, '').lstrip('/')
    if not path or path.endswith('/'):
        path += 'index.html'
    return ROOT / path


def body_hash(text):
    m = re.search(r'<body.*?(?=<footer|</body>)', text, re.S)
    body = m.group(0) if m else text
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    return hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]


def meta_of(text):
    title = re.search(r'<title>(.*?)</title>', text, re.S)
    desc = re.search(r'<meta name="description" content="(.*?)">', text, re.S)
    t = html.unescape(title.group(1)).split(' | ')[0].strip() if title else ''
    d = html.unescape(desc.group(1)).strip() if desc else ''
    return t, d


def write_feed(state, pages, now):
    rows = [(v['lastmod'], u) for u, v in state.items() if u in pages and not any(p in u for p in FEED_SKIP)]
    # 같은 날이면 날짜 페이지 → 2027 → 새로 쓴 글 → 나머지 순
    weight = lambda u: 3 if '/daily/2' in u else 2 if '/2027/' in u else 1 if '/dream/' in u else 0
    rows.sort(key=lambda r: (r[0], weight(r[1]), r[1]), reverse=True)
    items = ''
    for lastmod, url in rows[:FEED_LIMIT]:
        title, desc = meta_of(pages[url])
        y, m, d = map(int, lastmod.split('-'))
        pub = format_datetime(datetime(y, m, d, 0, 0, tzinfo=KST))
        items += (f'    <item>\n      <title>{escape(title)}</title>\n      <link>{escape(url)}</link>\n'
                  f'      <guid isPermaLink="true">{escape(url)}</guid>\n      <pubDate>{pub}</pubDate>\n'
                  f'      <description>{escape(desc)}</description>\n    </item>\n')
    feed = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>홍스팟 운세</title>
    <link>{SITE}/</link>
    <description>오늘의 띠별 운세, 사주 일주, 꿈해몽, 별자리, 2027년 신년운세까지 재미로 보는 운세 모음</description>
    <language>ko</language>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
{items}  </channel>
</rss>
'''
    (ROOT / 'feed.xml').write_text(feed, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--init', action='store_true', help='현재 본문을 기준점으로 저장')
    ap.add_argument('--date', help='오늘 날짜 (기본: 한국시간 오늘)')
    args = ap.parse_args()
    now = datetime.now(KST)
    today = args.date or now.strftime('%Y-%m-%d')

    path = ROOT / 'sitemap.xml'
    sitemap = path.read_text(encoding='utf-8')
    old_lastmod = dict(re.findall(r'<loc>(.*?)</loc><lastmod>(.*?)</lastmod>', sitemap))
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}

    pages, changed, missing = {}, [], []
    for url in re.findall(r'<loc>(.*?)</loc>', sitemap):
        f = file_for(url.split('?')[0])
        if not f.exists():
            missing.append(url)
            continue
        text = f.read_text(encoding='utf-8')
        pages[url] = text
        h = body_hash(text)
        prev = state.get(url)
        if args.init:
            state[url] = {'hash': h, 'lastmod': old_lastmod.get(url, today)}
        elif not prev or prev['hash'] != h:
            state[url] = {'hash': h, 'lastmod': today}
            changed.append(url)

    if missing:
        raise SystemExit(f'사이트맵에 있는데 파일이 없는 주소: {missing[:5]}')
    state = {u: v for u, v in state.items() if u in pages}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=0, sort_keys=True) + '\n', encoding='utf-8')

    def fix(m):
        return f"<loc>{m.group(1)}</loc><lastmod>{state[m.group(1)]['lastmod']}</lastmod>"
    sitemap = re.sub(r'<loc>(.*?)</loc><lastmod>.*?</lastmod>', fix, sitemap)
    path.write_text(sitemap, encoding='utf-8')

    write_feed(state, pages, now)
    CHANGED.write_text('\n'.join(changed) + ('\n' if changed else ''), encoding='utf-8')
    print(f'사이트맵 {len(pages)}개, 바뀐 페이지 {len(changed)}개')


if __name__ == '__main__':
    main()
