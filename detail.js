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
    if (!shareBtn) {
        console.error('공유 버튼을 찾을 수 없습니다');
        return;
    }
    
    const info = ZODIAC_INFO[zodiac];
    const summary = generateFortuneSummary(fortuneData);
    const shareUrl = `https://fortune.hongspot.com/detail.html?zodiac=${zodiac}`;
    
    console.log('카카오톡 공유 설정:', { zodiac, summary, shareUrl });
    
    shareBtn.addEventListener('click', function() {
        console.log('카카오톡 공유 버튼 클릭됨');
        
        // Kakao SDK 로드 확인
        if (typeof Kakao === 'undefined') {
            alert('카카오톡 SDK가 로드되지 않았습니다. 페이지를 새로고침해주세요.');
            return;
        }
        
        // 초기화 확인
        if (!Kakao.isInitialized()) {
            console.log('카카오 SDK 재초기화 시도');
            try {
                Kakao.init('27e9da30e66de45bc054ba884c3bd150');
            } catch (e) {
                console.error('카카오 초기화 실패:', e);
                alert('카카오톡 공유 기능을 사용할 수 없습니다.');
                return;
            }
        }
        
        console.log('카카오톡 공유 실행');
        
        try {
            Kakao.Share.sendDefault({
                objectType: 'feed',
                content: {
                    title: `${info.emoji} ${info.name} 오늘의 운세`,
                    description: summary,
                    imageUrl: 'https://mud-kage.kakao.com/dn/NTmhS/btqfEUdFAUf/FjKzkZsnoeE4o19klTOVI1/openlink_640x640s.jpg',
                    link: {
                        mobileWebUrl: shareUrl,
                        webUrl: shareUrl,
                    },
                },
                buttons: [
                    {
                        title: '운세 보러가기',
                        link: {
                            mobileWebUrl: shareUrl,
                            webUrl: shareUrl,
                        },
                    },
                ],
            });
            console.log('카카오톡 공유 성공');
        } catch (error) {
            console.error('카카오톡 공유 오류:', error);
            alert('카카오톡 공유 중 오류가 발생했습니다: ' + error.message);
        }
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
