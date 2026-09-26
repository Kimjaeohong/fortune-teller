// ─────────────────────────────────────────────
//  공통 유틸: 날짜(한국시간), 데이터 로딩, 점수, 공유
// ─────────────────────────────────────────────

/* ---------- 날짜 (항상 한국시간 기준) ---------- */

function kstDateString(date = new Date()) {
    // en-CA 포맷은 YYYY-MM-DD
    return new Intl.DateTimeFormat('en-CA', {
        timeZone: CONFIG.TIMEZONE, year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(date);
}

function formatKoreanDate(dateStr) {
    const [y, m, d] = dateStr.split('-').map(Number);
    const date = new Date(Date.UTC(y, m - 1, d, 12));
    const weekday = new Intl.DateTimeFormat('ko-KR', { weekday: 'long', timeZone: 'UTC' }).format(date);
    return { full: `${y}년 ${m}월 ${d}일 ${weekday}`, short: `${m}월 ${d}일`, weekday, year: y };
}

/* ---------- 띠 계산 ---------- */

function zodiacFromYear(year) {
    return ZODIAC_ORDER[(((year - 4) % 12) + 12) % 12];
}

function yearsForZodiac(key, uptoYear) {
    const idx = ZODIAC_ORDER.indexOf(key);
    const years = [];
    for (let y = 1946; y <= uptoYear; y++) {
        if ((((y - 4) % 12) + 12) % 12 === idx) years.push(y);
    }
    return years;
}

/* ---------- 문자열 ---------- */

function escapeHtml(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function cleanFortuneText(text) {
    return String(text || '')
        .replace(/\*\*/g, '')
        .replace(/\s+/g, ' ')
        .trim();
}

function firstSentence(text) {
    const t = cleanFortuneText(text);
    const m = t.match(/^.*?[.!?요다](?=\s|$)/);
    return m ? m[0] : t;
}

/* ---------- CSV ---------- */

// 따옴표 안의 쉼표·줄바꿈까지 처리하는 CSV 파서
function parseCSV(text) {
    const rows = [];
    let row = [], cell = '', inQuotes = false;
    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (inQuotes) {
            if (ch === '"') {
                if (text[i + 1] === '"') { cell += '"'; i++; }
                else inQuotes = false;
            } else cell += ch;
        } else if (ch === '"') inQuotes = true;
        else if (ch === ',') { row.push(cell); cell = ''; }
        else if (ch === '\n' || ch === '\r') {
            if (ch === '\r' && text[i + 1] === '\n') i++;
            row.push(cell); rows.push(row); row = []; cell = '';
        } else cell += ch;
    }
    if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
    return rows.filter(r => r.some(c => c.trim() !== ''));
}

/* ---------- 데이터 로딩 ---------- */

function gvizUrl(query) {
    return `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/gviz/tq`
        + `?tqx=out:csv&sheet=${encodeURIComponent(CONFIG.SHEET_NAME)}`
        + `&tq=${encodeURIComponent(query)}`;
}

async function queryRows(query) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);
    try {
        const res = await fetch(gvizUrl(query), { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        return parseCSV(text)
            .filter(r => r.length >= 4 && r[0].trim() !== 'date')
            .map(r => ({
                date: r[0].trim(),
                zodiac: r[1].trim(),
                category: r[2].trim(),
                content: cleanFortuneText(r[3])
            }));
    } finally {
        clearTimeout(timer);
    }
}

function readCache(key) {
    try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; }
}
function writeCache(key, value) {
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* 무시 */ }
}

async function fetchJson(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);
    try {
        const res = await fetch(url, { signal: controller.signal });
        if (res.status === 404) return null;
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } finally {
        clearTimeout(timer);
    }
}

/** 1순위: 사이트에 함께 배포된 data/YYYY-MM-DD.json (없으면 최근 몇 해 같은 월·일) */
async function loadFromJson(today) {
    const [y, m, d] = today.split('-').map(Number);
    const candidates = [today];
    for (let back = 1; back <= 3; back++) {
        const day = (m === 2 && d === 29) ? 28 : d;
        candidates.push(`${y - back}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`);
    }
    for (const date of candidates) {
        const json = await fetchJson(`data/${date}.json`);
        if (json && json.fortunes) return { date, data: json.fortunes, scores: json.scores || null };
    }
    return null;
}

/** 2순위: 구글 시트 (해당 날짜 행만 gviz 쿼리) */
async function loadFromSheet(today) {
    let rows = await queryRows(`select A, B, C, D where A = '${today}'`);
    let date = today;
    if (!rows.length) {
        const past = await queryRows(`select A, B, C, D where A ends with '${today.slice(4)}' order by A desc`);
        if (past.length) {
            date = past[0].date;
            rows = past.filter(r => r.date === date);
        }
    }
    if (!rows.length) return null;
    const data = {};
    rows.forEach(r => {
        if (!ZODIAC_INFO[r.zodiac] || !FORTUNE_CATEGORIES[r.category]) return;
        (data[r.zodiac] ||= {})[r.category] = r.content;
    });
    return { date, data, scores: null };
}

/**
 * 오늘(한국시간) 운세를 가져온다.
 * 반환: { date, requestedDate, isFallback, data: {zodiac:{category:text}}, scores: {zodiac:{category:1~5}} | null }
 */
async function loadTodayFortunes() {
    const today = kstDateString();
    const cacheKey = `fortune:v3:${today}`;
    const cached = readCache(cacheKey);
    if (cached) return cached;

    let found = null;
    try {
        found = await loadFromJson(today);
    } catch (e) {
        console.warn('JSON 데이터 로딩 실패, 시트로 대체:', e);
    }
    if (!found) found = await loadFromSheet(today);

    const result = found
        ? { ...found, requestedDate: today, isFallback: found.date !== today }
        : { date: today, requestedDate: today, isFallback: false, data: {}, scores: null };
    if (found) writeCache(cacheKey, result);
    return result;
}

/** 카테고리 별점: 데이터에 점수가 있으면 그대로, 없으면 문장 톤으로 계산 */
function categoryScore(result, zodiac, category) {
    const s = result.scores && result.scores[zodiac] && result.scores[zodiac][category];
    if (s) return s;
    const text = result.data[zodiac] && result.data[zodiac][category];
    return text ? scoreText(text) : null;
}

/* ---------- 행운 지수 ---------- */

const POSITIVE_WORDS = ['행운', '기회', '좋은 소식', '기쁜', '결실', '성과', '인정', '칭찬', '수익', '이득',
    '유리', '응원', '성장', '빛나', '순조', '활력', '매력', '가까워', '풀리', '여유가 생', '빨라', '살아나'];
const NEGATIVE_WORDS = ['주의', '조심', '피해야', '무리', '실수', '오해', '갈등', '손실', '하락', '긴장',
    '불편', '충동', '새는 돈', '민감', '과한', '서두르'];

/** 텍스트 톤으로 1~5점 계산 */
function scoreText(text) {
    const t = cleanFortuneText(text);
    if (!t) return 3;
    let score = 3;
    POSITIVE_WORDS.forEach(w => { if (t.includes(w)) score += 0.75; });
    NEGATIVE_WORDS.forEach(w => { if (t.includes(w)) score -= 0.75; });
    return Math.max(1, Math.min(5, Math.round(score)));
}

/** 띠의 대표 점수 = 종합운 점수 (없으면 나머지 평균) */
function scoreZodiac(categoryMap) {
    if (!categoryMap) return null;
    if (categoryMap.overall) return scoreText(categoryMap.overall);
    const scores = Object.values(categoryMap).map(scoreText);
    if (!scores.length) return null;
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
}

function scoreLabel(score) {
    if (score == null) return '';
    if (score >= 4.5) return '아주 좋음';
    if (score >= 3.5) return '좋음';
    if (score >= 2.5) return '무난';
    return '신중하게';
}

/** 별점 마크업 (반 개 지원) */
function starsHtml(score, { label = true } = {}) {
    if (score == null) return '';
    let html = '<span class="stars" aria-hidden="true">';
    for (let i = 1; i <= 5; i++) {
        const cls = score >= i ? 'on' : (score >= i - 0.5 ? 'half' : '');
        html += `<i class="${cls}">★</i>`;
    }
    html += '</span>';
    const sr = `<span class="sr-only">행운 지수 5점 중 ${score}점</span>`;
    return html + sr + (label ? `<span class="stars-label">${scoreLabel(score)}</span>` : '');
}

/* ---------- 오늘의 행운 아이템 (날짜+띠로 고정된 재미 요소) ---------- */

function hashString(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) {
        h ^= str.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    return h >>> 0;
}

const LUCKY_COLORS = [
    { name: '버건디', hex: '#8c2f39' }, { name: '올리브', hex: '#7a7d3a' }, { name: '네이비', hex: '#23345c' },
    { name: '머스터드', hex: '#d4a72c' }, { name: '라벤더', hex: '#a697cf' }, { name: '민트', hex: '#8fcfb8' },
    { name: '코랄', hex: '#ef8a6f' }, { name: '베이지', hex: '#d9c6a5' }, { name: '스카이블루', hex: '#7fb4e0' },
    { name: '포레스트 그린', hex: '#2f5d4a' }, { name: '화이트', hex: '#f3f0e8' }, { name: '차콜', hex: '#3a3a3f' }
];
const LUCKY_DIRECTIONS = ['동쪽', '서쪽', '남쪽', '북쪽', '동남쪽', '동북쪽', '서남쪽', '서북쪽'];
const LUCKY_TIMES = ['이른 아침', '오전', '점심 무렵', '오후', '해 질 녘', '저녁', '늦은 밤'];

function luckyItems(dateStr, zodiac) {
    const h = hashString(`${dateStr}:${zodiac}`);
    return {
        color: LUCKY_COLORS[h % LUCKY_COLORS.length],
        number: (Math.floor(h / 7) % 45) + 1,
        direction: LUCKY_DIRECTIONS[Math.floor(h / 331) % LUCKY_DIRECTIONS.length],
        time: LUCKY_TIMES[Math.floor(h / 2417) % LUCKY_TIMES.length]
    };
}

/* ---------- 내 띠 기억 ---------- */

function getMyZodiac() {
    try { return localStorage.getItem('fortune:my-zodiac'); } catch { return null; }
}
function setMyZodiac(key) {
    try { localStorage.setItem('fortune:my-zodiac', key); } catch { /* 무시 */ }
}

/* ---------- 공유 ---------- */

function initKakao() {
    try {
        if (window.Kakao && !window.Kakao.isInitialized()) window.Kakao.init(CONFIG.KAKAO_KEY);
        return !!(window.Kakao && window.Kakao.isInitialized());
    } catch { return false; }
}

function shareKakao({ title, description, url, buttonTitle = '운세 보러가기' }) {
    if (!initKakao()) {
        showToast('카카오톡 공유를 불러오지 못했어요. 링크 복사를 이용해 주세요.');
        return;
    }
    window.Kakao.Share.sendDefault({
        objectType: 'feed',
        content: {
            title,
            description,
            imageUrl: CONFIG.SHARE_IMAGE,
            link: { mobileWebUrl: url, webUrl: url }
        },
        buttons: [{ title: buttonTitle, link: { mobileWebUrl: url, webUrl: url } }]
    });
}

async function shareLink({ title, text, url }) {
    if (navigator.share) {
        try { await navigator.share({ title, text, url }); return; }
        catch (e) { if (e.name === 'AbortError') return; }
    }
    try {
        await navigator.clipboard.writeText(url);
        showToast('링크를 복사했어요');
    } catch {
        window.prompt('아래 링크를 복사하세요', url);
    }
}

function showToast(message) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'status');
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('show'), 2200);
}
