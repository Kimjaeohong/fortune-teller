# ⚡ 빠른 시작 가이드

10분 안에 띠별 운세 사이트를 완성하세요!

## 📋 준비물

- [ ] GitHub 계정
- [ ] Google 계정
- [ ] Anthropic Claude API 키 ([console.anthropic.com](https://console.anthropic.com))

## 🚀 5단계 설정

### 1단계: 구글 스프레드시트 만들기 (2분)

1. [Google Sheets](https://sheets.google.com) 접속
2. 빈 스프레드시트 생성
3. 시트 이름을 `fortune_data`로 변경
4. 첫 번째 행에 입력:
   ```
   date    zodiac    category    content
   ```
5. 우측 상단 "공유" → "링크가 있는 모든 사용자" → "뷰어"
6. URL에서 스프레드시트 ID 복사 (나중에 사용)
   - `https://docs.google.com/spreadsheets/d/[여기_부분]/edit`

### 2단계: Google Cloud 서비스 계정 만들기 (3분)

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 (이름: fortune-bot)
3. 좌측 메뉴 → API 및 서비스 → 사용자 인증 정보
4. "사용자 인증 정보 만들기" → "서비스 계정"
5. 이름 입력 (예: fortune-generator) → "만들기"
6. 역할: 편집자 → "완료"
7. 생성된 서비스 계정 클릭 → "키" 탭 → "키 추가" → JSON
8. JSON 파일 다운로드 (나중에 사용)
9. 좌측 메뉴 → API 및 서비스 → 라이브러리
10. "Google Sheets API" 검색 → 사용 설정
11. "Google Drive API" 검색 → 사용 설정
12. 스프레드시트로 돌아가서 서비스 계정 이메일 주소를 편집자로 공유
    - 이메일 형식: `fortune-generator@프로젝트명.iam.gserviceaccount.com`

### 3단계: GitHub 저장소 만들기 (2분)

1. [GitHub](https://github.com) 로그인
2. "New repository" 클릭
3. 저장소 이름: `fortune-teller` (또는 원하는 이름)
4. Public 선택
5. "Create repository"
6. 로컬에서 이 프로젝트 폴더의 모든 파일을 저장소에 업로드
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/사용자명/fortune-teller.git
   git push -u origin main
   ```

### 4단계: GitHub Secrets 설정 (2분)

1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. "New repository secret" 클릭하여 3개 추가:

**ANTHROPIC_API_KEY**
- Value: Claude API 키 붙여넣기

**SPREADSHEET_ID**
- Value: 1단계에서 복사한 스프레드시트 ID

**GOOGLE_CREDENTIALS**
- Value: 2단계에서 다운로드한 JSON 파일 전체 내용 복사 붙여넣기

### 5단계: 웹사이트 설정 및 실행 (1분)

1. 저장소의 `config.js` 파일 편집
2. `YOUR_SPREADSHEET_ID_HERE`를 실제 ID로 변경
3. 커밋 & 푸시
4. Settings → Pages → Source: main branch
5. Actions 탭 → "Daily Fortune Generator" → "Run workflow"
6. 2-3분 후 스프레드시트에 데이터 확인
7. Pages 설정에 표시된 URL로 접속!

## 🎉 완료!

웹사이트 주소: `https://사용자명.github.io/fortune-teller/`

## ⏰ 자동 업데이트

- 매일 자정(한국시간)에 자동으로 새 운세 생성
- 손 안 대도 됨!

## 🔍 확인사항

### 웹사이트가 안 보여요?
1. GitHub Pages가 활성화되었는지 확인 (Settings → Pages)
2. `config.js`의 스프레드시트 ID가 올바른지 확인
3. 스프레드시트 공유 설정이 "링크가 있는 모든 사용자"인지 확인

### 운세가 생성 안 돼요?
1. Actions 탭에서 워크플로우 로그 확인
2. 3개의 Secrets가 모두 설정되었는지 확인
3. Claude API 크레딧이 있는지 확인
4. 서비스 계정이 스프레드시트 편집 권한을 가졌는지 확인

## 💡 팁

### 지금 바로 운세 생성하기
- Actions → Daily Fortune Generator → Run workflow

### 운세 스타일 바꾸기
- `generate_fortune.py`의 프롬프트 수정

### 디자인 바꾸기
- `styles.css` 파일 수정

### 업데이트 시간 바꾸기
- `.github/workflows/daily-fortune.yml`의 cron 수정

## 📱 모바일에서도 잘 보여요!

반응형 디자인으로 모바일, 태블릿, PC 모두 완벽 지원!

---

문제가 있으면 README.md의 트러블슈팅 섹션을 참고하세요!
