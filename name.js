// ─────────────────────────────────────────────
//  이름 궁합 (옛날 공책 방식)
//  1) 두 이름을 한 글자씩 번갈아 쓴다   예) 김철수 + 이영희 → 김 이 철 영 수 희
//  2) 글자마다 획수를 센다
//  3) 옆 숫자끼리 더해 끝자리만 남기기를 두 자리가 될 때까지 반복
// ─────────────────────────────────────────────

const CHO = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
const JUNG = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ'];
const JONG = ['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];

// 이름 궁합에서 흔히 쓰는 자모 획수 (곳마다 조금씩 다를 수 있음)
const STROKES = {
    'ㄱ': 2, 'ㄴ': 2, 'ㄷ': 3, 'ㄹ': 5, 'ㅁ': 4, 'ㅂ': 4, 'ㅅ': 2, 'ㅇ': 1, 'ㅈ': 3, 'ㅊ': 4,
    'ㅋ': 3, 'ㅌ': 4, 'ㅍ': 4, 'ㅎ': 3,
    'ㄲ': 4, 'ㄸ': 6, 'ㅃ': 8, 'ㅆ': 4, 'ㅉ': 6,
    'ㄳ': 4, 'ㄵ': 5, 'ㄶ': 5, 'ㄺ': 7, 'ㄻ': 9, 'ㄼ': 9, 'ㄽ': 7, 'ㄾ': 9, 'ㄿ': 9, 'ㅀ': 8, 'ㅄ': 6,
    'ㅏ': 2, 'ㅐ': 3, 'ㅑ': 3, 'ㅒ': 4, 'ㅓ': 2, 'ㅔ': 3, 'ㅕ': 3, 'ㅖ': 4, 'ㅗ': 2, 'ㅘ': 4,
    'ㅙ': 5, 'ㅚ': 3, 'ㅛ': 3, 'ㅜ': 2, 'ㅝ': 4, 'ㅞ': 5, 'ㅟ': 3, 'ㅠ': 3, 'ㅡ': 1, 'ㅢ': 2, 'ㅣ': 1
};

const MESSAGES = [
    { min: 95, title: '천생연분', text: '이름부터 서로를 알아본 사이! 공책에 하트를 그려도 될 만큼 찰떡이에요.' },
    { min: 85, title: '찰떡궁합', text: '말하지 않아도 통하는 사이예요. 함께 있으면 시간이 금방 가요.' },
    { min: 70, title: '좋은 인연', text: '서로에게 편안한 쉼터가 되어 주는 궁합이에요. 작은 배려가 더 가깝게 만들어요.' },
    { min: 55, title: '설렘 진행 중', text: '알아갈수록 더 좋아지는 사이예요. 먼저 말을 걸어 보면 어떨까요?' },
    { min: 40, title: '밀당의 고수', text: '가까워졌다 멀어졌다 하는 재미가 있는 궁합이에요. 솔직한 대화가 열쇠예요.' },
    { min: 25, title: '노력형 궁합', text: '숫자는 조금 낮지만, 원래 공책 궁합은 이름만 보고 하는 거라 노력이 이겨요!' },
    { min: 0,  title: '반전의 주인공', text: '숫자는 낮아도 실제로 잘 맞는 커플이 얼마나 많은데요. 다시 한 번 해볼까요?' }
];

/* ---------- 계산 ---------- */

function syllableStrokes(ch) {
    const code = ch.charCodeAt(0) - 0xAC00;
    if (code < 0 || code > 11171) return 0;
    const cho = CHO[Math.floor(code / 588)];
    const jung = JUNG[Math.floor((code % 588) / 28)];
    const jong = JONG[code % 28];
    return (STROKES[cho] || 0) + (STROKES[jung] || 0) + (jong ? (STROKES[jong] || 0) : 0);
}

function interleave(a, b) {
    const out = [];
    const n = Math.max(a.length, b.length);
    for (let i = 0; i < n; i++) {
        if (i < a.length) out.push(a[i]);
        if (i < b.length) out.push(b[i]);
    }
    return out;
}

function compute(first, second) {
    const letters = interleave([...first], [...second]);
    const rows = [letters.map(syllableStrokes)];          // 첫 줄은 획수 그대로
    while (rows[rows.length - 1].length > 2) {
        const prev = rows[rows.length - 1];
        rows.push(prev.slice(1).map((n, i) => (prev[i] + n) % 10));
    }
    const last = rows[rows.length - 1].map(n => n % 10);
    let score = last.length === 2 ? last[0] * 10 + last[1] : last[0];
    if (last.length === 2 && last[0] === 0 && last[1] === 0) score = 100;   // 공책 규칙: 00은 100%
    return { letters, strokes: letters.map(syllableStrokes), rows, score };
}

function messageFor(score) {
    return MESSAGES.find(m => score >= m.min);
}

/* ---------- 입력 ---------- */

function cleanName(v) {
    return (v || '').replace(/\s+/g, '');
}

function validName(v) {
    return /^[가-힣]{1,5}$/.test(v);
}

/* ---------- 화면 ---------- */

const state = { a: '', b: '', dir: 'ab' };

function pyramidHtml(result, ownerOf) {
    const letterRow = result.letters.map((ch, i) =>
        `<span class="py-cell py-letter ${ownerOf(i)}">${ch}</span>`).join('');
    const rowsHtml = result.rows.map((row, ri) => `
        <div class="py-row${ri === result.rows.length - 1 ? ' py-final' : ''}" style="animation-delay:${200 + ri * 220}ms">
            ${row.map(n => `<span class="py-cell">${n}</span>`).join('')}
        </div>`).join('');
    return `<div class="py-row py-letters">${letterRow}</div>
            ${rowsHtml}`;
}

function render() {
    const { a, b } = state;
    const first = state.dir === 'ab' ? a : b;
    const second = state.dir === 'ab' ? b : a;
    const result = compute(first, second);
    const other = compute(second, first);
    const msg = messageFor(result.score);

    // 번갈아 쓴 글자가 누구 이름인지 (색 구분)
    const n = Math.max(first.length, second.length);
    const owners = [];
    for (let i = 0; i < n; i++) {
        if (i < first.length) owners.push('who-1');
        if (i < second.length) owners.push('who-2');
    }

    document.getElementById('dir-ab').textContent = `${a} → ${b}`;
    document.getElementById('dir-ba').textContent = `${b} → ${a}`;
    document.querySelectorAll('.dir-btn').forEach(btn =>
        btn.setAttribute('aria-selected', String(btn.dataset.dir === state.dir)));

    document.getElementById('pyramid').innerHTML = pyramidHtml(result, i => owners[i]);

    const scoreEl = document.getElementById('score');
    scoreEl.innerHTML = `
        <div class="score-names"><span class="who-1">${escapeHtml(first)}</span><span class="heart" aria-hidden="true">♥</span><span class="who-2">${escapeHtml(second)}</span></div>
        <div class="score-num"><span id="score-count">0</span><small>%</small></div>
        <div class="score-title">${msg.title}</div>
        <p class="score-text">${msg.text}</p>
        <p class="score-other">반대로 <b>${escapeHtml(second)} → ${escapeHtml(first)}</b>는 <b>${other.score}%</b>예요</p>`;

    // 숫자 올라가는 연출
    const target = result.score;
    const countEl = document.getElementById('score-count');
    const start = performance.now();
    const delay = 200 + result.rows.length * 220;
    const tick = now => {
        const t = Math.min(1, Math.max(0, (now - start - delay) / 700));
        countEl.textContent = Math.round(target * (1 - Math.pow(1 - t, 3)));
        if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);

    document.getElementById('result').hidden = false;
}

function shareUrl() {
    return `${CONFIG.SITE_URL}/name.html#a=${encodeURIComponent(state.a)}&b=${encodeURIComponent(state.b)}`;
}

function readHash() {
    const params = new URLSearchParams(location.hash.slice(1));
    const a = cleanName(params.get('a'));
    const b = cleanName(params.get('b'));
    return validName(a) && validName(b) ? { a, b } : null;
}

function submit(a, b, scroll = true) {
    state.a = a;
    state.b = b;
    state.dir = 'ab';
    render();
    // 이름은 서버로 보내지 않고 주소의 # 뒤에만 둠 (공유용)
    history.replaceState(null, '', `#a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
    if (scroll) setTimeout(() => document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('name-form');
    const inA = document.getElementById('name-a');
    const inB = document.getElementById('name-b');

    form.addEventListener('submit', e => {
        e.preventDefault();
        const a = cleanName(inA.value);
        const b = cleanName(inB.value);
        if (!validName(a) || !validName(b)) {
            showToast('두 이름을 한글 1~5글자로 적어 주세요');
            (validName(a) ? inB : inA).focus();
            return;
        }
        submit(a, b);
    });

    document.getElementById('swap').addEventListener('click', () => {
        [inA.value, inB.value] = [inB.value, inA.value];
    });

    document.querySelectorAll('.dir-btn').forEach(btn => btn.addEventListener('click', () => {
        state.dir = btn.dataset.dir;
        render();
    }));

    document.getElementById('retry').addEventListener('click', () => {
        inA.value = '';
        inB.value = '';
        document.getElementById('result').hidden = true;
        history.replaceState(null, '', location.pathname);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        inA.focus();
    });

    document.getElementById('share-kakao').addEventListener('click', () => {
        const r = compute(state.a, state.b);
        shareKakao({
            title: `💘 ${state.a} ♥ ${state.b} 이름 궁합 ${r.score}%`,
            description: `${messageFor(r.score).title} · 우리 이름 궁합도 확인해 볼까?`,
            url: shareUrl(),
            buttonTitle: '나도 궁합 보기'
        });
    });
    document.getElementById('share-link').addEventListener('click', () => {
        const r = compute(state.a, state.b);
        shareLink({ title: '이름 궁합', text: `${state.a} ♥ ${state.b} 이름 궁합 ${r.score}%`, url: shareUrl() });
    });

    const fromHash = readHash();
    if (fromHash) {
        inA.value = fromHash.a;
        inB.value = fromHash.b;
        submit(fromHash.a, fromHash.b, false);
    }
});
