// ─────────────────────────────────────────────
//  오늘의 투자운 (띠별)
//  data/invest/YYYY-MM-DD.json → 12띠 카드 + 순위 + 선택한 띠의 상세
// ─────────────────────────────────────────────

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);

const STANCE_INFO = {
    flow:    { label: '흐름 타기', short: '매수 분위기', color: '#86c2a8' },
    split:   { label: '나눠 담기', short: '분할 매수',   color: '#8fa8e0' },
    harvest: { label: '챙기기',    short: '수익 실현',   color: '#e3c26b' },
    watch:   { label: '지켜보기',  short: '관망',        color: '#b9a9e6' },
    rest:    { label: '쉬어가기',  short: '매매 휴식',   color: '#e08a7a' },
    closed:  { label: '충전하기',  short: '휴장일',      color: '#9aa0b4' }
};

const state = { result: null, key: null };

/* ---------- 데이터 ---------- */

async function loadInvest() {
    const cacheKey = `fortune:v1:invest:${todayStr}`;
    const cached = readCache(cacheKey);
    if (cached) return cached;

    const [y, m, d] = todayStr.split('-').map(Number);
    const candidates = [todayStr];
    for (let back = 1; back <= 3; back++) {
        const day = (m === 2 && d === 29) ? 28 : d;
        candidates.push(`${y - back}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`);
    }
    for (const date of candidates) {
        const json = await fetchJson(`data/invest/${date}.json`);
        if (json && json.fortunes) {
            const result = {
                date, requestedDate: todayStr, isFallback: date !== todayStr,
                market: json.market || { open: true },
                data: json.fortunes
            };
            writeCache(cacheKey, result);
            return result;
        }
    }
    return { date: todayStr, requestedDate: todayStr, isFallback: false, market: { open: true }, data: {} };
}

function rankInvest(result) {
    return ZODIAC_ORDER
        .filter(k => result.data[k])
        .map(k => ({ k, s: result.data[k].score || 0, h: hashString(result.date + ':invest:' + k) }))
        .sort((a, b) => b.s - a.s || a.h - b.h)
        .map(x => x.k);
}

function luckyDigit(date, key) {
    return hashString(`invest:${date}:${key}`) % 10;
}

function stancePill(stance, { withShort = true } = {}) {
    const s = STANCE_INFO[stance] || STANCE_INFO.watch;
    return `<span class="stance stance--${stance}" style="--stance:${s.color}">${s.label}${withShort ? `<small>${s.short}</small>` : ''}</span>`;
}

/* ---------- 화면: 날짜·장 상태 ---------- */

function renderDate() {
    document.getElementById('today-date').textContent = todayInfo.full;
}

function renderMarket(result) {
    const pill = document.getElementById('market-pill');
    const text = document.getElementById('market-text');
    const m = result.market || { open: true };
    pill.hidden = false;
    pill.classList.toggle('closed', !m.open);
    text.textContent = m.open
        ? '오늘은 장이 열리는 날이에요'
        : `오늘은 장이 쉬는 날이에요 · ${m.reason || '휴장'}`;
}

function showNotice(html) {
    document.getElementById('data-notice').innerHTML = html ? `<div class="notice">${html}</div>` : '';
}

/* ---------- 화면: 카드 ---------- */

function renderCards() {
    const grid = document.getElementById('invest-grid');
    const mine = getMyZodiac();
    grid.innerHTML = ZODIAC_ORDER.map((key, i) => {
        const info = ZODIAC_INFO[key];
        const isMine = key === mine;
        return `
            <a class="zodiac-card${isMine ? ' is-mine' : ''}" href="invest.html?zodiac=${key}"
               data-zodiac="${key}" style="animation-delay:${i * 35}ms">
                ${isMine ? '<span class="mine-badge">내 띠</span>' : ''}
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">${info.hanja}</span>
                    <div class="zc-name">${info.name}<span class="zc-emoji" aria-hidden="true">${info.emoji}</span></div>
                </div>
                <div class="zc-stance"><span class="skeleton skeleton-line" style="width:80px"></span></div>
                <p class="zc-line"><span class="skeleton skeleton-line"></span><span class="skeleton skeleton-line short"></span></p>
                <div class="zc-foot"><span class="skeleton skeleton-line" style="width:90px"></span></div>
            </a>`;
    }).join('');

    document.getElementById('top3').innerHTML = [1, 2, 3].map(() => `
        <li class="top3-item"><span class="skeleton skeleton-line" style="width:70%"></span></li>`).join('');
}

function fillCards(result) {
    const ranking = rankInvest(result);
    ZODIAC_ORDER.forEach(key => {
        const card = document.querySelector(`.zodiac-card[data-zodiac="${key}"]`);
        const f = result.data[key];
        const stanceEl = card.querySelector('.zc-stance');
        const line = card.querySelector('.zc-line');
        const foot = card.querySelector('.zc-foot');
        if (!f) {
            stanceEl.innerHTML = '';
            line.textContent = '오늘의 투자운을 준비 중이에요.';
            foot.innerHTML = '';
            return;
        }
        stanceEl.innerHTML = stancePill(f.stance, { withShort: false });
        line.textContent = firstSentence(f.text);
        const rank = ranking.indexOf(key) + 1;
        foot.innerHTML = starsHtml(f.score, { label: false })
            + (rank > 0 ? `<span class="rank-badge${rank <= 3 ? ' top' : ''}">${rank}위</span>` : '');
    });

    document.getElementById('top3').innerHTML = ranking.slice(0, 3).map((key, i) => `
        <li class="top3-item rank-${i + 1}">
            <a href="invest.html?zodiac=${key}" data-zodiac="${key}">
                <span class="top3-rank">${i + 1}</span>
                <span class="hanja" aria-hidden="true">${ZODIAC_INFO[key].hanja}</span>
                <span class="top3-body">
                    <strong>${ZODIAC_INFO[key].name} <span class="top3-stance">${STANCE_INFO[result.data[key].stance].label}</span></strong>
                    <small>${escapeHtml(firstSentence(result.data[key].text))}</small>
                </span>
            </a>
        </li>`).join('');
}

/* ---------- 화면: 선택한 띠 상세 ---------- */

function renderFocus(key) {
    const result = state.result;
    const box = document.getElementById('focus');
    const f = result && result.data[key];
    if (!f) { box.hidden = true; return; }

    const info = ZODIAC_INFO[key];
    const s = STANCE_INFO[f.stance] || STANCE_INFO.watch;
    const rank = rankInvest(result).indexOf(key) + 1;
    const years = yearsForZodiac(key, todayInfo.year).slice(-6).join(' · ');
    const isMine = getMyZodiac() === key;
    const open = result.market && result.market.open !== false;

    box.hidden = false;
    box.innerHTML = `
        <div class="invest-focus-head">
            <span class="hanja" aria-hidden="true">${info.hanja}</span>
            <div class="invest-focus-title">
                <h2>${info.name} 오늘의 투자운 <span class="zc-emoji" aria-hidden="true">${info.emoji}</span></h2>
                <p class="years">${years}년생 · ${todayInfo.short}</p>
            </div>
            <div class="invest-focus-score">
                ${starsHtml(f.score)}
                ${rank > 0 ? `<span class="rank-pill">오늘 ${rank}위</span>` : ''}
            </div>
        </div>

        <div class="invest-stance-row">
            ${stancePill(f.stance)}
            ${isMine ? '<span class="mine-chip">내 띠</span>' : `<button type="button" class="link-btn" id="set-mine">내 띠로 설정</button>`}
        </div>

        <div class="summary">
            <div class="label">오늘의 투자 한마디</div>
            <p>${escapeHtml(f.text)}</p>
        </div>

        <div class="lucky invest-lucky" aria-label="오늘의 투자 포인트">
            <div class="lucky-item"><div class="k">${open ? '행운의 섹터' : '다음 장 관심 섹터'}</div><div class="v">${escapeHtml(f.sector)}</div></div>
            <div class="lucky-item"><div class="k">좋은 시간대</div><div class="v">${escapeHtml(f.time)}</div></div>
            <div class="lucky-item"><div class="k">오늘의 키워드</div><div class="v">#${escapeHtml(f.keyword)}</div></div>
            <div class="lucky-item"><div class="k">행운의 끝자리</div><div class="v">${luckyDigit(result.date, key)}<small class="v-sub">종목코드 끝자리</small></div></div>
        </div>

        <div class="invest-notes">
            <article class="fortune-item">
                <header><h3><span class="cat-dot" style="color:${s.color};background:${s.color}"></span>오늘의 팁</h3></header>
                <p>${escapeHtml(f.tip)}</p>
            </article>
            <article class="fortune-item">
                <header><h3><span class="cat-dot" style="color:var(--rose);background:var(--rose)"></span>주의 포인트</h3></header>
                <p>${escapeHtml(f.caution)}</p>
            </article>
        </div>

        <div class="share-row">
            <button type="button" class="btn btn-kakao" id="share-kakao">카카오톡 공유</button>
            <button type="button" class="btn btn-ghost" id="share-link">링크 복사</button>
            <a class="btn btn-ghost" href="detail.html?zodiac=${key}">${info.name} 종합 운세 →</a>
        </div>`;

    const setMine = document.getElementById('set-mine');
    if (setMine) setMine.addEventListener('click', () => {
        setMyZodiac(key);
        showToast(`${info.name}를 내 띠로 저장했어요`);
        renderCards(); fillCards(result); renderFocus(key); markActive(key);
    });

    const url = `${CONFIG.SITE_URL}/invest.html?zodiac=${key}`;
    const summary = firstSentence(f.text);
    const title = `${info.emoji} ${info.name} 오늘의 투자운 · ${todayInfo.short}`;
    document.getElementById('share-kakao').addEventListener('click', () => shareKakao({
        title, description: `${s.label} · ${summary}`, url, buttonTitle: '내 투자운 보기'
    }));
    document.getElementById('share-link').addEventListener('click', () => shareLink({ title, text: summary, url }));

    document.title = `${info.name} 오늘의 투자운 (${todayInfo.short}) | 홍스팟 운세`;
}

function markActive(key) {
    document.querySelectorAll('.zodiac-card').forEach(c => c.classList.toggle('is-active', c.dataset.zodiac === key));
}

function selectZodiac(key, { scroll = true, push = true } = {}) {
    if (!ZODIAC_ORDER.includes(key)) return;
    state.key = key;
    renderFocus(key);
    markActive(key);
    if (push) history.replaceState(null, '', `?zodiac=${key}`);
    if (scroll) setTimeout(() => document.getElementById('focus').scrollIntoView({ behavior: 'smooth', block: 'start' }), 40);
}

/* ---------- 로딩 ---------- */

async function loadData() {
    try {
        const result = await loadInvest();
        state.result = result;
        if (!Object.keys(result.data).length) {
            fillCards(result);
            showNotice('오늘의 투자운이 아직 준비되지 않았어요. 잠시 후 다시 확인해 주세요.');
            return;
        }
        renderMarket(result);
        fillCards(result);
        showNotice(result.isFallback
            ? `오늘 데이터 준비 중이라 ${formatKoreanDate(result.date).short} 투자운을 대신 보여드려요.`
            : '');
        const fromUrl = new URLSearchParams(location.search).get('zodiac');
        const key = ZODIAC_ORDER.includes(fromUrl) ? fromUrl : getMyZodiac();
        if (key) selectZodiac(key, { scroll: false, push: false });
    } catch (err) {
        console.error('투자운 데이터 로딩 실패:', err);
        document.querySelectorAll('.zc-line').forEach(el => { el.textContent = '투자운을 불러오지 못했어요.'; });
        document.querySelectorAll('.zc-foot, .zc-stance').forEach(el => { el.innerHTML = ''; });
        document.getElementById('top3').innerHTML = '';
        showNotice('네트워크가 불안정해요. <button type="button" class="btn btn-ghost" id="retry" style="margin-left:6px;padding:4px 12px">다시 시도</button>');
        document.getElementById('retry').addEventListener('click', () => { renderCards(); loadData(); });
    }
}

function setupFinder() {
    const form = document.getElementById('finder');
    const input = document.getElementById('birth-year');
    form.addEventListener('submit', e => {
        e.preventDefault();
        const year = parseInt(input.value, 10);
        if (!year || year < 1900 || year > todayInfo.year) {
            showToast('태어난 해를 4자리로 입력해 주세요');
            input.focus();
            return;
        }
        const key = zodiacFromYear(year);
        setMyZodiac(key);
        if (state.result) { renderCards(); fillCards(state.result); }
        selectZodiac(key);
    });
}

function setupCardClicks() {
    document.body.addEventListener('click', e => {
        const a = e.target.closest('a[data-zodiac]');
        if (!a || !state.result) return;
        e.preventDefault();
        selectZodiac(a.dataset.zodiac);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderDate();
    renderCards();
    setupFinder();
    setupCardClicks();
    loadData();
});
