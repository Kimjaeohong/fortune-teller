"""
바뀐 주소를 IndexNow 로 검색엔진에 알림 (네이버·빙 등)

    python3 tools/indexnow.py            # tools/.changed_urls 에 적힌 주소만
    python3 tools/indexnow.py --all      # 사이트맵의 모든 주소

키는 tools/indexnow.key 에 있고, 같은 이름의 <키>.txt 파일이 사이트 맨 위에 있어야 합니다.
결과는 tools/indexnow_last.json 에 남습니다. 실패해도 사이트 배포에는 영향이 없습니다.
"""
import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = 'fortune.hongspot.com'
ENDPOINTS = ['https://searchadvisor.naver.com/indexnow', 'https://api.indexnow.org/indexnow']
LIMIT = 10000


def post(endpoint, payload):
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status
    except urllib.error.HTTPError as err:
        return err.code
    except Exception as err:
        return str(err)[:120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    key = (ROOT / 'tools' / 'indexnow.key').read_text().strip()
    if args.all:
        urls = re.findall(r'<loc>(.*?)</loc>', (ROOT / 'sitemap.xml').read_text(encoding='utf-8'))
    else:
        f = ROOT / 'tools' / '.changed_urls'
        urls = f.read_text(encoding='utf-8').split() if f.exists() else []
    urls = urls[:LIMIT]
    result = {'at': datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M'), 'count': len(urls), 'status': {}}
    if urls:
        payload = {'host': HOST, 'key': key, 'keyLocation': f'https://{HOST}/{key}.txt', 'urlList': urls}
        for ep in ENDPOINTS:
            result['status'][ep] = post(ep, payload)
    (ROOT / 'tools' / 'indexnow_last.json').write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
