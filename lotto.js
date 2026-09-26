// ─────────────────────────────────────────────
//  행운의 로또 번호 (6/45)
//  - 운세로 뽑기: 날짜 + 띠/별자리 기준으로 하루 동안 같은 번호
//  - 무작위 뽑기: 누를 때마다 새 번호
// ─────────────────────────────────────────────

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);

const GAMES = 5;
const MAX_INCLUDE = 5;
const GAME_LABELS = ['A', 'B', 'C', 'D', 'E'];
const HISTORY_KEY = 'fortune:lotto-history';

const state = {
    mode: 'fortune',
    include: new Set(),
    exclude: new Set(),
    games: [],
    luckyNumber: null
};

/* ---------- 회차·추첨일 ---------- */

// 1회 추첨: 2002-12-07(토), 이후 매주 토요일
function nextDraw() {
    const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
        timeZone: CONFIG.TIMEZONE, year: 'numeric', month: 'numeric', day: 'numeric',
        hour: 'numeric', hourCycle: 'h23', weekday: 'short'
    }).formatToParts(new Date()).map(p => [p.type, p.value]));
    const weekday = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(parts.weekday);
    let add = (6 - weekday + 7) % 7;                                   // 이번 주 토요일
    if (add === 0 && parseInt(parts.hour, 10) >= 20) add = 7;         // 토요일 20시 판매 마감 이후면 다음 주
    const draw = new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day + add));
    const round = Math.round((draw - Date.UTC(2002, 11, 7)) / 86400000 / 7) + 1;
    return { round, month: draw.getUTCMonth() + 1, day: draw.getUTCDate() };
}

/* ---------- 난수 ---------- */

function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
        a = (a + 0x6D2B79F5) >>> 0;
        let t = a;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function secureRandom() {
    if (window.crypto && crypto.getRandomValues) {
        return crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296;
    }
    return Math.random();
}

/* ---------- 번호 만들기 ---------- */

function makeGame(rand, fixed) {
    const picked = new Set(fixed);
    const pool = [];
    for (let n = 1; n <= 45; n++) {
        if (!picked.has(n) && !state.exclude.has(n)) pool.push(n);
    }
    while (picked.size < 6 && pool.length) {
        const i = Math.floor(rand() * pool.length);
        picked.add(pool.splice(i, 1)[0]);
    }
    return [...picked].sort((a, b) => a - b);
}

function parseBasis(value) {
    const [kind, key] = value.split(':');
    return { kind, key };
}

function basisLabel(value) {
    const { kind, key } = parseBasis(value);
    return FORTUNE_KINDS[kind].name(key);
}

function luckyNumberFor(value) {
    const { kind, key } = parseBasis(value);
    // 상세 페이지의 '행운의 숫자'와 같은 값
    return luckyItems(todayStr, kind === 'zodiac' ? key : `${kind}:${key}`).number;
}

function generate() {
    const include = [...state.include];
    let rand;
    state.luckyNumber = null;

    if (state.mode === 'fortune') {
        const basis = document.getElementById('basis').value;
        const seedText = [todayStr, basis, include.sort((a, b) => a - b).join('.'), [...state.exclude].sort((a, b) => a - b).join('.')].join('|');
        rand = mulberry32(hashString(seedText));
        const lucky = luckyNumberFor(basis);
        if (!state.exclude.has(lucky)) state.luckyNumber = lucky;
    } else {
        rand = secureRandom;
    }

    const games = [];
    const seen = new Set();
    let guard = 0;
    while (games.length < GAMES && guard++ < 200) {
        const fixed = [...include];
        if (games.length === 0 && state.luckyNumber && fixed.length < 6 && !fixed.includes(state.luckyNumber)) {
            fixed.push(state.luckyNumber);
        }
        const game = makeGame(rand, fixed);
        const sig = game.join(',');
        if (game.length === 6 && !seen.has(sig)) {
            seen.add(sig);
            games.push(game);
        }
    }
    state.games = games;
    return games;
}

/* ---------- 화면 ---------- */

function ballClass(n) {
    if (n <= 10) return 'b1';
    if (n <= 20) return 'b2';
    if (n <= 30) return 'b3';
    if (n <= 40) return 'b4';
    return 'b5';
}

function ballHtml(n, delay, extra = '') {
    return `<span class="ball ${ballClass(n)}${extra}" style="animation-delay:${delay}ms">${n}</span>`;
}

function renderGames() {
    const games = state.games;
    const title = document.getElementById('results-title');
    const sub = document.getElementById('results-sub');
    if (state.mode === 'fortune') {
        const basis = document.getElementById('basis').value;
        title.textContent = `${basisLabel(basis)}의 오늘 행운 번호`;
        sub.textContent = state.luckyNumber ? `행운의 숫자 ${state.luckyNumber} 포함` : todayInfo.short;
    } else {
        title.textContent = '무작위 행운 번호';
        sub.textContent = '누를 때마다 새로 뽑혀요';
    }

    document.getElementById('games').innerHTML = games.map((g, gi) => `
        <li class="game">
            <span class="game-label">${GAME_LABELS[gi]}</span>
            <span class="balls">
                ${g.map((n, ni) => ballHtml(n, gi * 120 + ni * 70,
                    (state.include.has(n) ? ' is-fixed' : '') + (gi === 0 && n === state.luckyNumber ? ' is-lucky' : ''))).join('')}
            </span>
        </li>`).join('');

    const results = document.getElementById('results');
    results.hidden = false;
    setTimeout(() => results.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
}

function gamesText() {
    return state.games.map((g, i) => `${GAME_LABELS[i]}  ${g.map(n => String(n).padStart(2, '0')).join(' ')}`).join('\n');
}

/* ---------- 포함·제외 번호 ---------- */

function renderGrid() {
    const grid = document.getElementById('num-grid');
    grid.innerHTML = Array.from({ length: 45 }, (_, i) => {
        const n = i + 1;
        const st = state.include.has(n) ? 'inc' : state.exclude.has(n) ? 'exc' : '';
        const label = st === 'inc' ? '포함' : st === 'exc' ? '제외' : '선택 안 함';
        return `<button type="button" class="num ${ballClass(n)} ${st}" data-n="${n}" aria-label="${n}번 ${label}">${n}</button>`;
    }).join('');

    const parts = [];
    if (state.include.size) parts.push(`포함 ${state.include.size}`);
    if (state.exclude.size) parts.push(`제외 ${state.exclude.size}`);
    document.getElementById('picker-count').textContent = parts.join(' · ') || '선택 없음';
}

function cycleNumber(n) {
    if (state.include.has(n)) {
        state.include.delete(n);
        if (45 - state.exclude.size - 1 < 6) {
            showToast('남은 번호가 6개보다 적어질 수 없어요');
        } else {
            state.exclude.add(n);
        }
    } else if (state.exclude.has(n)) {
        state.exclude.delete(n);
    } else if (state.include.size >= MAX_INCLUDE) {
        showToast(`포함 번호는 최대 ${MAX_INCLUDE}개까지 고를 수 있어요`);
        return;
    } else {
        state.include.add(n);
    }
    renderGrid();
}

/* ---------- 기록 ---------- */

function readHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; } catch { return []; }
}
function writeHistory(list) {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list)); } catch { /* 무시 */ }
}

function saveHistory() {
    const label = state.mode === 'fortune' ? basisLabel(document.getElementById('basis').value) : '무작위';
    const list = readHistory();
    const sig = JSON.stringify(state.games);
    if (list[0] && list[0].sig === sig) return;
    list.unshift({ date: todayStr, label, games: state.games, sig });
    writeHistory(list.slice(0, 10));
    renderHistory();
}

function renderHistory() {
    const list = readHistory();
    const box = document.getElementById('history');
    box.hidden = !list.length;
    document.getElementById('history-list').innerHTML = list.map(item => `
        <li>
            <div class="history-meta">${formatKoreanDate(item.date).short} · ${escapeHtml(item.label)}</div>
            <div class="history-games">
                ${item.games.map(g => `<span class="mini-balls">${g.map(n => `<span class="ball mini ${ballClass(n)}">${n}</span>`).join('')}</span>`).join('')}
            </div>
        </li>`).join('');
}

/* ---------- 설정 ---------- */

function setupBasis() {
    const select = document.getElementById('basis');
    const zodiacOpts = ZODIAC_ORDER.map(k => `<option value="zodiac:${k}">${ZODIAC_INFO[k].name}</option>`).join('');
    const starOpts = STAR_ORDER.map(k => `<option value="star:${k}">${STAR_INFO[k].name}</option>`).join('');
    select.innerHTML = `<optgroup label="띠">${zodiacOpts}</optgroup><optgroup label="별자리">${starOpts}</optgroup>`;

    const myZodiac = getMyKey('zodiac');
    const myStar = getMyKey('star');
    if (myZodiac) select.value = `zodiac:${myZodiac}`;
    else if (myStar) select.value = `star:${myStar}`;
}

function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.seg-btn').forEach(b => b.setAttribute('aria-selected', String(b.dataset.mode === mode)));
    document.getElementById('basis-row').hidden = mode !== 'fortune';
    document.getElementById('mode-hint').textContent = mode === 'fortune'
        ? '오늘 날짜와 고른 띠·별자리로 번호를 정해요. 하루 동안은 같은 번호가 나와요.'
        : '누를 때마다 완전히 새로운 번호 5게임을 뽑아요.';
}

function setupDrawInfo() {
    const d = nextDraw();
    document.getElementById('draw-info').textContent = `제${d.round}회 · ${d.month}월 ${d.day}일(토) 추첨`;
}

document.addEventListener('DOMContentLoaded', () => {
    setupDrawInfo();
    setupBasis();
    setMode('fortune');
    renderGrid();
    renderHistory();

    document.querySelectorAll('.seg-btn').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));

    document.getElementById('num-grid').addEventListener('click', e => {
        const btn = e.target.closest('.num');
        if (btn) cycleNumber(parseInt(btn.dataset.n, 10));
    });
    document.getElementById('picker-reset').addEventListener('click', () => {
        state.include.clear();
        state.exclude.clear();
        renderGrid();
    });

    document.getElementById('draw-btn').addEventListener('click', () => {
        generate();
        renderGames();
        saveHistory();
    });

    document.getElementById('copy-btn').addEventListener('click', async () => {
        const text = `홍스팟 운세 행운 번호 (${todayInfo.short})\n${gamesText()}`;
        try {
            await navigator.clipboard.writeText(text);
            showToast('번호를 복사했어요');
        } catch {
            window.prompt('아래 번호를 복사하세요', text);
        }
    });

    document.getElementById('share-kakao').addEventListener('click', () => shareKakao({
        title: `🍀 ${document.getElementById('results-title').textContent}`,
        description: gamesText(),
        url: `${CONFIG.SITE_URL}/lotto.html`,
        buttonTitle: '나도 번호 뽑기'
    }));

    document.getElementById('history-clear').addEventListener('click', () => {
        writeHistory([]);
        renderHistory();
        showToast('기록을 지웠어요');
    });
});
