// 오늘 날짜 표시
function updateDate() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    const dateString = today.toLocaleDateString('ko-KR', options);
    document.getElementById('today-date').textContent = dateString;
}

// 구글 스프레드시트에서 데이터 가져오기
async function fetchFortuneData() {
    try {
        const url = `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/gviz/tq?tqx=out:json&sheet=${CONFIG.SHEET_NAME}`;
        const response = await fetch(url);
        const text = await response.text();
        
        // Google Sheets API 응답 파싱
        const json = JSON.parse(text.substr(47).slice(0, -2));
        
        return parseFortuneData(json);
    } catch (error) {
        console.error('운세 데이터 로딩 실패:', error);
        return null;
    }
}

// 스프레드시트 데이터 파싱
function parseFortuneData(json) {
    const rows = json.table.rows;
    const today = new Date().toISOString().split('T')[0];
    const fortuneData = {};
    
    // 헤더: date, zodiac, category, content
    for (const row of rows) {
        const cells = row.c;
        if (!cells || !cells[0] || !cells[0].v) continue;
        
        const date = cells[0].v;
        const zodiac = cells[1]?.v;
        const category = cells[2]?.v;
        const content = cells[3]?.v;
        
        // 오늘 날짜의 데이터만 사용
        if (date === today) {
            if (!fortuneData[zodiac]) {
                fortuneData[zodiac] = {};
            }
            fortuneData[zodiac][category] = content;
        }
    }
    
    return fortuneData;
}

// 행운 지수 계산 (간단한 알고리즘)
function calculateLuckScore(fortuneText) {
    if (!fortuneText) return 3;
    
    const positiveWords = ['좋', '행운', '기회', '성공', '발전', '상승', '길', '만남', '이익'];
    const negativeWords = ['주의', '조심', '어려움', '갈등', '손실', '하락'];
    
    let score = 3;
    positiveWords.forEach(word => {
        if (fortuneText.includes(word)) score += 0.5;
    });
    negativeWords.forEach(word => {
        if (fortuneText.includes(word)) score -= 0.5;
    });
    
    return Math.max(1, Math.min(5, Math.round(score)));
}

// 별점 표시
function getStars(score) {
    return '⭐'.repeat(score);
}

// 띠 카드 렌더링
async function renderZodiacCards() {
    const grid = document.getElementById('zodiac-grid');
    const fortuneData = await fetchFortuneData();
    
    for (const [key, info] of Object.entries(ZODIAC_INFO)) {
        const card = document.createElement('div');
        card.className = 'zodiac-card';
        card.onclick = () => location.href = `detail.html?zodiac=${key}`;
        
        let luckIndicator = '';
        if (fortuneData && fortuneData[key] && fortuneData[key].overall) {
            const score = calculateLuckScore(fortuneData[key].overall);
            luckIndicator = `
                <div class="luck-indicator">
                    <div class="luck-stars">${getStars(score)}</div>
                </div>
            `;
        }
        
        card.innerHTML = `
            <span class="zodiac-emoji">${info.emoji}</span>
            <h2 class="zodiac-name">${info.name}</h2>
            <p class="zodiac-years">${info.years}</p>
            ${luckIndicator}
        `;
        
        grid.appendChild(card);
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    renderZodiacCards();
});
