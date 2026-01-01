// URL에서 띠 정보 가져오기
function getZodiacFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('zodiac');
}

// 구글 스프레드시트에서 데이터 가져오기
async function fetchFortuneData(zodiac) {
    try {
        const url = `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/gviz/tq?tqx=out:json&sheet=${CONFIG.SHEET_NAME}`;
        const response = await fetch(url);
        const text = await response.text();
        
        // Google Sheets API 응답 파싱
        const json = JSON.parse(text.substr(47).slice(0, -2));
        
        return parseFortuneData(json, zodiac);
    } catch (error) {
        console.error('운세 데이터 로딩 실패:', error);
        return null;
    }
}

// 스프레드시트 데이터 파싱
function parseFortuneData(json, zodiac) {
    const rows = json.table.rows;
    const today = new Date().toISOString().split('T')[0];
    const fortuneData = {};
    
    // 헤더: date, zodiac, category, content
    for (const row of rows) {
        const cells = row.c;
        if (!cells || !cells[0] || !cells[0].v) continue;
        
        const date = cells[0].v;
        const rowZodiac = cells[1]?.v;
        const category = cells[2]?.v;
        const content = cells[3]?.v;
        
        // 오늘 날짜 & 해당 띠의 데이터만 사용
        if (date === today && rowZodiac === zodiac) {
            fortuneData[category] = content;
        }
    }
    
    return fortuneData;
}

// 날짜 표시
function getDateString() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    return today.toLocaleDateString('ko-KR', options);
}

// 운세 요약 생성 (50자 이내)
function generateFortuneSummary(fortuneData) {
    // overall (종합운)이 있으면 그걸 요약, 없으면 다른 운세 사용
    let text = fortuneData['overall'] || fortuneData['money'] || fortuneData['work'] || '오늘의 운세를 확인하세요!';
    
    // 공백 제거 후 50자로 자르기
    text = text.replace(/\s/g, '');
    if (text.length > 50) {
        text = text.substring(0, 47) + '...';
    }
    
    return text;
}

// 헤더 렌더링
function renderHeader(zodiac) {
    const info = ZODIAC_INFO[zodiac];
    const header = document.getElementById('detail-header');
    
    header.innerHTML = `
        <div class="detail-emoji">${info.emoji}</div>
        <h1 class="detail-title">${info.name} 운세</h1>
        <p class="date">${getDateString()}</p>
        <p class="zodiac-years">${info.years}</p>
    `;
}

// 운세 내용 렌더링
function renderFortune(fortuneData) {
    const content = document.getElementById('fortune-content');
    
    if (!fortuneData || Object.keys(fortuneData).length === 0) {
        content.innerHTML = `
            <div class="error">
                <h3>😅 운세를 불러올 수 없습니다</h3>
                <p>잠시 후 다시 시도해주세요</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    for (const [categoryKey, categoryInfo] of Object.entries(FORTUNE_CATEGORIES)) {
        const fortuneText = fortuneData[categoryKey] || '오늘은 평온한 하루가 될 것입니다.';
        
        html += `
            <div class="fortune-section">
                <h2 class="section-title">
                    <span class="section-icon">${categoryInfo.icon}</span>
                    ${categoryInfo.title}
                </h2>
                <p class="section-content">${fortuneText}</p>
            </div>
        `;
    }
    
    content.innerHTML = html;
}

// 카카오톡 공유 버튼 설정
function setupKakaoShare(zodiac, fortuneData) {
    const shareBtn = document.getElementById('kakao-share-btn');
    if (!shareBtn) return;
    
    const info = ZODIAC_INFO[zodiac];
    const summary = generateFortuneSummary(fortuneData);
    const shareUrl = `https://fortune.hongspot.com/detail.html?zodiac=${zodiac}`;
    
    shareBtn.addEventListener('click', function() {
        if (!Kakao.isInitialized()) {
            alert('카카오톡 SDK 초기화 실패');
            return;
        }
        
        Kakao.Share.sendDefault({
            objectType: 'feed',
            content: {
                title: `${info.emoji} ${info.name} 오늘의 운세`,
                description: summary,
                imageUrl: 'https://fortune.hongspot.com/og-image.png',
                link: {
                    mobileWebUrl: shareUrl,
                    webUrl: shareUrl,
                },
            },
            buttons: [
                {
                    title: '내 운세 보기',
                    link: {
                        mobileWebUrl: shareUrl,
                        webUrl: shareUrl,
                    },
                },
                {
                    title: '다른 띠 보기',
                    link: {
                        mobileWebUrl: 'https://fortune.hongspot.com',
                        webUrl: 'https://fortune.hongspot.com',
                    },
                },
            ],
        });
    });
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async () => {
    const zodiac = getZodiacFromURL();
    
    if (!zodiac || !ZODIAC_INFO[zodiac]) {
        document.getElementById('fortune-content').innerHTML = `
            <div class="error">
                <h3>잘못된 접근입니다</h3>
                <p><a href="index.html">메인으로 돌아가기</a></p>
            </div>
        `;
        return;
    }
    
    renderHeader(zodiac);
    
    const fortuneData = await fetchFortuneData(zodiac);
    renderFortune(fortuneData);
    
    // 카카오톡 공유 버튼 설정
    if (fortuneData && Object.keys(fortuneData).length > 0) {
        setupKakaoShare(zodiac, fortuneData);
    }
});
