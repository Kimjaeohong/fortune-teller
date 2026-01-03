// 오늘 날짜 표시
function updateDate() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    const dateString = today.toLocaleDateString('ko-KR', options);
    document.getElementById('today-date').textContent = dateString;
}

// 구글 스프레드시트에서 데이터 가져오기 (CSV 방식 - AdBlocker 우회)
async function fetchFortuneData() {
    try {
        // CSV export URL 사용 (AdBlocker가 차단하지 않음)
        const url = `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=${CONFIG.SHEET_NAME}`;
        const response = await fetch(url);
        const text = await response.text();
        
        return parseCSVFortuneData(text);
    } catch (error) {
        console.error('운세 데이터 로딩 실패:', error);
        return null;
    }
}

// CSV 데이터 파싱
function parseCSVFortuneData(csvText) {
    const lines = csvText.split('\n');
    
    // 오늘 날짜 (YYYY-MM-DD 포맷, 0 패딩)
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${day}`;
    
    const fortuneData = {};
    
    // 첫 번째 줄은 헤더이므로 건너뜀
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        // CSV 파싱 (따옴표 처리 포함)
        const cells = parseCSVLine(line);
        if (cells.length < 4) continue;
        
        const date = cells[0];
        const zodiac = cells[1];
        const category = cells[2];
        const content = cells[3];
        
        // 오늘 날짜의 데이터만 사용
        if (date === todayStr) {
            if (!fortuneData[zodiac]) {
                fortuneData[zodiac] = {};
            }
            fortuneData[zodiac][category] = content;
        }
    }
    
    return fortuneData;
}

// CSV 라인 파싱 (따옴표 처리)
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                // 이스케이프된 따옴표
                current += '"';
                i++;
            } else {
                // 따옴표 토글
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            // 셀 구분
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    
    result.push(current);
    return result;
}

// 행운 지수 계산 (간단한 알고리즘)
function calculateLuckScore(fortuneText) {
    if (!fortuneText) return 3;
    
    // 텍스트 정리 (마크다운, 줄바꿈 제거)
    const cleanText = fortuneText
        .replace(/\*\*/g, '')
        .replace(/\n+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    
    const positiveWords = ['좋', '행운', '기회', '성공', '발전', '상승', '길', '만남', '이익'];
    const negativeWords = ['주의', '조심', '어려움', '갈등', '손실', '하락'];
    
    let score = 3;
    positiveWords.forEach(word => {
        if (cleanText.includes(word)) score += 0.5;
    });
    negativeWords.forEach(word => {
        if (cleanText.includes(word)) score -= 0.5;
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
