"""
띠별 운세 자동 생성 스크립트

- 띠마다 한 번의 API 호출로 5개 카테고리를 함께 생성 (하루 12회 호출)
- 대상 날짜의 행만 교체하고 나머지 데이터는 그대로 둔다
- 사용법
    python generate_fortune.py                 # 내일(한국시간) 1일치
    python generate_fortune.py --date 2027-01-01 --days 31   # 특정 기간 일괄 생성
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

import anthropic
import gspread
from google.oauth2.service_account import Credentials

KST = timezone(timedelta(hours=9))
SHEET_NAME = 'fortune_data'
MODEL = os.environ.get('FORTUNE_MODEL', 'claude-haiku-4-5-20251001')

ZODIAC_NAMES = {
    'rat': '쥐띠', 'ox': '소띠', 'tiger': '호랑이띠', 'rabbit': '토끼띠',
    'dragon': '용띠', 'snake': '뱀띠', 'horse': '말띠', 'sheep': '양띠',
    'monkey': '원숭이띠', 'rooster': '닭띠', 'dog': '개띠', 'pig': '돼지띠',
}

# 웹사이트(config.js)의 FORTUNE_CATEGORIES와 같은 키
CATEGORY_NAMES = {
    'overall': '종합운',
    'money': '재물운',
    'work': '일·학업운',
    'health': '건강운',
    'relationship': '인연·관계운',
}

FALLBACK_TEXT = '오늘은 평온한 하루가 될 거예요. 작은 여유를 챙겨보세요.'

PROMPT = """{date_kr} {zodiac_name}의 오늘의 운세를 카테고리별로 써 주세요.

규칙
- 친근하고 가벼운 톤, 재미로 보는 운세 느낌
- 카테고리마다 2문장, 한 문장은 60자 이내
- 구체적인 행동 팁을 하나씩 포함 (예: 산책, 메모, 먼저 연락하기)
- 너무 무겁거나 불안을 주는 표현, 의학·투자 단정 표현은 피하기
- 모든 카테고리가 똑같이 좋기만 하지 않도록, 하루 안에서도 강약을 주기
- 다른 띠와 겹치지 않도록 {zodiac_name}만의 개성 있는 표현 사용
- 마크다운 금지, 순수 텍스트

카테고리: 종합운(overall), 재물운(money), 일·학업운(work), 건강운(health), 인연·관계운(relationship)

아래 JSON 한 개만 출력하세요. 다른 말은 쓰지 마세요.
{{"overall": "...", "money": "...", "work": "...", "health": "...", "relationship": "..."}}"""


def generate_for_zodiac(client, target: date, zodiac: str) -> dict:
    """한 띠의 5개 카테고리 운세를 생성. 실패 시 최대 3회 재시도."""
    prompt = PROMPT.format(
        date_kr=f'{target.month}월 {target.day}일',
        zodiac_name=ZODIAC_NAMES[zodiac],
    )
    last_error = None
    for attempt in range(3):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1200,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = message.content[0].text.strip()
            match = re.search(r'\{.*\}', text, re.S)
            data = json.loads(match.group(0) if match else text)
            return {
                cat: re.sub(r'\s+', ' ', str(data.get(cat, '')).replace('**', '')).strip() or FALLBACK_TEXT
                for cat in CATEGORY_NAMES
            }
        except Exception as e:  # noqa: BLE001
            last_error = e
            time.sleep(2 * (attempt + 1))
    print(f'   ✗ {ZODIAC_NAMES[zodiac]} 생성 실패: {last_error}')
    return {cat: FALLBACK_TEXT for cat in CATEGORY_NAMES}


def open_sheet():
    creds = Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets'],
    )
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ['SPREADSHEET_ID']).worksheet(SHEET_NAME)


def write_rows(sheet, new_rows_by_date: dict):
    """대상 날짜의 기존 행을 지우고 새 행으로 교체 (한 번에 기록)."""
    all_values = sheet.get_all_values()
    header, body = all_values[0], all_values[1:]
    targets = set(new_rows_by_date)
    kept = [row for row in body if row and row[0] not in targets]
    added = [row for d in sorted(new_rows_by_date) for row in new_rows_by_date[d]]
    merged = sorted(kept + added, key=lambda r: r[0])

    sheet.clear()
    sheet.update([header] + merged, value_input_option='RAW')
    print(f'✅ {len(added)}행 기록 완료 (전체 {len(merged)}행)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='시작 날짜 YYYY-MM-DD (기본: 내일, 한국시간)')
    parser.add_argument('--days', type=int, default=1, help='생성할 일수 (기본 1)')
    args = parser.parse_args()

    start = (datetime.strptime(args.date, '%Y-%m-%d').date() if args.date
             else (datetime.now(KST) + timedelta(days=1)).date())
    dates = [start + timedelta(days=i) for i in range(args.days)]

    print(f'🔮 {dates[0]} ~ {dates[-1]} ({len(dates)}일) 운세 생성 · 모델 {MODEL}')
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

    new_rows_by_date = {}
    for d in dates:
        rows = []
        for zodiac in ZODIAC_NAMES:
            fortunes = generate_for_zodiac(client, d, zodiac)
            rows += [[d.isoformat(), zodiac, cat, fortunes[cat]] for cat in CATEGORY_NAMES]
        new_rows_by_date[d.isoformat()] = rows
        print(f'   ✓ {d} 완료')

    print('\n📊 스프레드시트 업데이트 중...')
    try:
        write_rows(open_sheet(), new_rows_by_date)
    except Exception as e:  # noqa: BLE001
        print(f'❌ 스프레드시트 업데이트 실패: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
