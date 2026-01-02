"""
띠별 운세 자동 생성 스크립트
매일 자정에 실행되어 새로운 운세를 생성하고 구글 스프레드시트에 저장
"""

import os
import anthropic
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# 12띠 목록
ZODIACS = ['rat', 'ox', 'tiger', 'rabbit', 'dragon', 'snake', 
           'horse', 'sheep', 'monkey', 'rooster', 'dog', 'pig']

ZODIAC_NAMES = {
    'rat': '쥐띠',
    'ox': '소띠',
    'tiger': '호랑이띠',
    'rabbit': '토끼띠',
    'dragon': '용띠',
    'snake': '뱀띠',
    'horse': '말띠',
    'sheep': '양띠',
    'monkey': '원숭이띠',
    'rooster': '닭띠',
    'dog': '개띠',
    'pig': '돼지띠'
}

# 운세 카테고리
CATEGORIES = ['overall', 'money', 'work', 'health', 'relationship']

CATEGORY_NAMES = {
    'overall': '종합운',
    'money': '재물운',
    'work': '직장/사업운',
    'health': '가정/건강운',
    'relationship': '이성/대인관계'
}

def generate_fortune(zodiac, category):
    """Claude API를 사용하여 운세 생성"""
    
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    zodiac_name = ZODIAC_NAMES[zodiac]
    category_name = CATEGORY_NAMES[category]
    
    prompt = f"""오늘의 {zodiac_name} {category_name}를 생성해주세요.

요구사항:
- 친근하고 가벼운 톤으로 작성
- 재미로 보는 운세라는 느낌
- 2-3문장으로 간결하게
- 구체적이면서도 긍정적인 내용
- 과도하게 무겁거나 진지하지 않게
- 운세 내용만 작성 (인사말이나 부가 설명 없이)

카테고리별 가이드:
- 종합운: 오늘 하루 전반적인 운세
- 재물운: 금전, 재테크, 수입 관련
- 직장/사업운: 업무, 사업, 커리어 관련
- 가정/건강운: 가족, 건강, 집안일 관련
- 이성/대인관계: 연애, 인간관계, 소통 관련

예시 스타일:
"오늘은 예상치 못한 곳에서 기쁜 소식이 들려올 수 있어요. 주변 사람들의 말에 귀 기울이면 좋은 기회를 발견할 거예요. 긍정적인 마인드를 유지하세요!"
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text.strip()

def update_google_sheet(fortune_data):
    """구글 스프레드시트에 운세 데이터 업데이트 (Batch 방식)"""
    
    # 서비스 계정 인증
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds = Credentials.from_service_account_file(
        'credentials.json',
        scopes=scope
    )
    
    client = gspread.authorize(creds)
    
    # 스프레드시트 열기
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sheet = client.open_by_key(spreadsheet_id).worksheet('fortune_data')
    
    # 내일 날짜 (운세는 다음 날 것을 미리 생성)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 모든 데이터 가져오기
    all_values = sheet.get_all_values()
    
    # 내일 날짜가 아닌 데이터만 유지 (헤더 포함)
    filtered_data = [all_values[0]]  # 헤더
    for row in all_values[1:]:  # 데이터 행
        if row[0] != tomorrow:  # 내일 날짜가 아닌 것만
            filtered_data.append(row)
    
    # 새 데이터 추가
    new_rows = []
    for zodiac, categories in fortune_data.items():
        for category, content in categories.items():
            new_rows.append([tomorrow, zodiac, category, content])
    
    # 기존 데이터 + 새 데이터 합치기
    all_new_data = filtered_data + new_rows
    
    # 한 번에 업데이트 (단 1회의 API 호출!)
    sheet.clear()  # 시트 전체 클리어
    sheet.update(all_new_data, value_input_option='RAW')  # 모든 데이터 한 번에 입력
    
    print(f"✅ {len(new_rows)}개의 운세가 성공적으로 업데이트되었습니다!")

def main():
    """메인 실행 함수"""
    print("🔮 운세 생성을 시작합니다...")
    
    fortune_data = {}
    
    # 모든 띠와 카테고리에 대해 운세 생성
    for zodiac in ZODIACS:
        print(f"\n📝 {ZODIAC_NAMES[zodiac]} 운세 생성 중...")
        fortune_data[zodiac] = {}
        
        for category in CATEGORIES:
            try:
                fortune = generate_fortune(zodiac, category)
                fortune_data[zodiac][category] = fortune
                print(f"   ✓ {CATEGORY_NAMES[category]}: {fortune[:30]}...")
            except Exception as e:
                print(f"   ✗ {CATEGORY_NAMES[category]} 생성 실패: {e}")
                fortune_data[zodiac][category] = "오늘은 평온한 하루가 될 것입니다."
    
    # 구글 스프레드시트에 업데이트
    print("\n📊 구글 스프레드시트 업데이트 중...")
    try:
        update_google_sheet(fortune_data)
        print("\n🎉 모든 작업이 완료되었습니다!")
    except Exception as e:
        print(f"\n❌ 스프레드시트 업데이트 실패: {e}")
        print("운세 데이터는 생성되었지만 스프레드시트에 저장하지 못했습니다.")

if __name__ == "__main__":
    main()
