# 🔮 띠별 운세 자동화 시스템

매일 자정 자동으로 12띠 운세를 생성하는 웹사이트입니다.

## ✨ 기능

- 12띠 카드형 메인 페이지
- 띠별 상세 운세 (종합운, 재물운, 직장/사업운, 가정/건강운, 이성/대인관계)
- Claude AI 자동 운세 생성
- 구글 스프레드시트 데이터 저장
- 매일 자정 자동 업데이트

## 🚀 설정 방법

### 1. 구글 스프레드시트 준비

1. 새 구글 스프레드시트 생성
2. 시트 이름을 `fortune_data`로 변경
3. 첫 번째 행에 헤더 추가:
   ```
   date | zodiac | category | content
   ```
4. 스프레드시트 ID 복사 (URL에서 확인)
   - URL: `https://docs.google.com/spreadsheets/d/[여기가_ID]/edit`

### 2. Google Cloud 서비스 계정 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. API 및 서비스 > 사용자 인증 정보
4. 서비스 계정 만들기
5. JSON 키 다운로드 (`credentials.json`)
6. Google Sheets API와 Google Drive API 활성화
7. 스프레드시트에 서비스 계정 이메일을 편집자로 공유

### 3. GitHub 저장소 설정

1. GitHub에 새 저장소 생성
2. 이 프로젝트 파일들 업로드
3. Settings > Secrets and variables > Actions
4. 다음 시크릿 추가:
   - `ANTHROPIC_API_KEY`: Claude API 키
   - `SPREADSHEET_ID`: 구글 스프레드시트 ID
   - `GOOGLE_CREDENTIALS`: credentials.json 파일 내용 전체

### 4. 웹사이트 설정

1. `config.js` 파일 열기
2. `SPREADSHEET_ID` 값을 실제 스프레드시트 ID로 변경
3. 스프레드시트를 "링크가 있는 모든 사용자" 보기 권한으로 공유

### 5. GitHub Pages 활성화

1. 저장소 Settings > Pages
2. Source: Deploy from a branch
3. Branch: main, 폴더: / (root)
4. Save

### 6. 첫 운세 생성 (수동)

1. Actions 탭으로 이동
2. "Daily Fortune Generator" 워크플로우 선택
3. "Run workflow" 클릭
4. 몇 분 후 스프레드시트에 운세 데이터 확인

## 📁 파일 구조

```
fortune-project/
├── index.html              # 메인 페이지
├── detail.html             # 상세 페이지
├── styles.css              # 스타일시트
├── config.js               # 설정 파일
├── script.js               # 메인 스크립트
├── detail.js               # 상세 페이지 스크립트
├── generate_fortune.py     # 운세 생성 스크립트
├── requirements.txt        # Python 패키지
├── .github/
│   └── workflows/
│       └── daily-fortune.yml  # GitHub Actions 워크플로우
└── README.md
```

## 🔧 트러블슈팅

### 스프레드시트 데이터가 안 보여요
- 스프레드시트가 "링크가 있는 모든 사용자" 보기 권한으로 공유되었는지 확인
- config.js의 SPREADSHEET_ID가 올바른지 확인
- 브라우저 콘솔(F12)에서 에러 메시지 확인

### GitHub Actions가 실행 안 돼요
- Actions 탭에서 워크플로우가 활성화되었는지 확인
- Secrets가 모두 정확히 설정되었는지 확인
- 워크플로우 실행 로그에서 에러 확인

### 운세 생성이 실패해요
- Claude API 키가 유효한지 확인
- API 크레딧이 남아있는지 확인
- 서비스 계정이 스프레드시트 편집 권한을 가지고 있는지 확인

## 💰 예상 비용

- GitHub Actions: 무료 (공개 저장소)
- GitHub Pages: 무료
- Google Sheets API: 무료
- Claude API (Sonnet 4.5):
  - 하루: 약 50-100원
  - 월: 약 1,500-3,000원

## 🎨 커스터마이징

### 운세 생성 스타일 변경
`generate_fortune.py`의 프롬프트 수정

### 디자인 변경
`styles.css` 파일 수정

### 업데이트 시간 변경
`.github/workflows/daily-fortune.yml`의 cron 시간 수정
- 현재: `0 15 * * *` (UTC 15:00 = 한국시간 00:00)

## 📝 라이선스

자유롭게 사용하세요!
