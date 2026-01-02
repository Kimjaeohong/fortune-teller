// URL에서 띠 정보 가져오기
function getZodiacFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('zodiac');
}

// 구글 스프레드시트에서 데이터 가져오기 (CSV 방식)
async function fetchFortuneData(zodiac) {
    try {
        const url = `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=${CONFIG.SHEET_NAME}`;
        const response = await fetch(url);
        const text = await response.text();
        
        return parseCSVFortuneData(text, zodiac);
    } catch (error) {
        console.error('운세 데이터 로딩 실패:', error);
        return null;
    }
}

// CSV 데이터 파싱
function parseCSVFortuneData(csvText, zodiac) {
    const lines = csvText.split('\n');
    const today = new Date().toISOString().split('T')[0];
    const fortuneData = {};
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const cells = parseCSVLine(line);
        if (cells.length < 4) continue;
        
        const date = cells[0];
        const rowZodiac = cells[1];
        const category = cells[2];
        const content = cells[3];
        
        // 오늘 날짜 & 해당 띠의 데이터만 사용
        if (date === today && rowZodiac === zodiac) {
            fortuneData[category] = content;
        }
    }
    
    return fortuneData;
}

// CSV 라인 파싱
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                current += '"';
                i++;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    
    result.push(current);
    return result;
}

// 날짜 표시
function getDateString() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    return today.toLocaleDateString('ko-KR', options);
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
});
