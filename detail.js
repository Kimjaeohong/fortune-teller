// ─────────────────────────────────────────────
//  상세 페이지 (띠 / 별자리 공용)
//  HTML에서 window.FORTUNE_KIND = 'zodiac' | 'star' 로 종류를 정한다
// ─────────────────────────────────────────────

const KIND_ID = window.FORTUNE_KIND || 'zodiac';
const KIND = FORTUNE_KINDS[KIND_ID];

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);

const CATEGORY_COLORS = {
    money: '#e3c26b',
    work: '#8fa8e0',
    health: '#86c2a8',
    relationship: '#e08a7a'
};

const detailUrl = key => `${KIND.detailPage}?${KIND.param}=${key}`;

function getKeyFromURL() {
    const key = new URLSearchParams(location.search).get(KIND.param);
    return key && KIND.order.includes(key) ? key : null;
}

function renderInvalid() {
    document.getElementById('detail-hero').innerHTML = '';
    document.getElementById('fortune-content').innerHTML = `
        <div class="state">
            <h3>어떤 ${KIND.label}인지 찾지 못했어요</h3>
            <p>목록에서 ${KIND.label}를 다시 골라 주세요.</p>
            <a class="btn btn-gold" href="${KIND.listPage}">12${KIND.label} 보러 가기</a>
        </div>`;
}

function renderSiblings(key) {
    const order = KIND.order;
    const i = order.indexOf(key);
    const prev = order[(i + 11) % 12];
    const next = order[(i + 1) % 12];
    document.getElementById('sibs').innerHTML = `
        <a href="${detailUrl(prev)}" aria-label="이전: ${KIND.name(prev)}">‹ ${KIND.name(prev)}</a>
        <a href="${detailUrl(next)}" aria-label="다음: ${KIND.name(next)}">${KIND.name(next)} ›</a>`;
}

function renderHero(key) {
    const isMine = getMyKey(KIND_ID) === key;
    const meta = KIND.meta(key);
    document.getElementById('detail-hero').innerHTML = `
        <div class="hanja-lg${KIND_ID === 'star' ? ' glyph-star' : ''}" aria-hidden="true">${KIND.glyph(key)}</div>
        <h1>${KIND.headline(key)}</h1>
        <p class="meta">${todayInfo.full}</p>
        <p class="years">${KIND.sub(key, todayInfo.year)}${meta ? ` · ${meta}` : ''}</p>
        <div class="score" id="hero-score"><span class="skeleton skeleton-line" style="width:120px"></span></div>
        ${isMine ? '' : `<div style="margin-top:14px"><button type="button" class="btn btn-ghost" id="set-mine" style="padding:7px 14px;font-size:.85rem">내 ${KIND.label}로 설정</button></div>`}`;

    const btn = document.getElementById('set-mine');
    if (btn) btn.addEventListener('click', () => {
        setMyKey(KIND_ID, key);
        btn.parentElement.remove();
        showToast(`${KIND.name(key)}를 내 ${KIND.label}로 저장했어요`);
    });
}

function renderSkeleton() {
    const blocks = Object.keys(FORTUNE_CATEGORIES).slice(1).map(() => `
        <article class="fortune-item">
            <span class="skeleton skeleton-line" style="width:40%;height:1.1em;margin-bottom:14px"></span>
            <span class="skeleton skeleton-line"></span>
            <span class="skeleton skeleton-line short"></span>
        </article>`).join('');
    document.getElementById('fortune-content').innerHTML = `
        <div class="summary">
            <div class="label">오늘의 한마디</div>
            <span class="skeleton skeleton-line"></span>
            <span class="skeleton skeleton-line"></span>
            <span class="skeleton skeleton-line short"></span>
        </div>
        <div class="fortune-list">${blocks}</div>`;
}

function renderFortune(key, result) {
    const map = result.data[key] || {};
    const content = document.getElementById('fortune-content');
    const heroScore = document.getElementById('hero-score');

    if (!Object.keys(map).length) {
        content.innerHTML = `
            <div class="state">
                <h3>오늘의 운세를 준비 중이에요</h3>
                <p>잠시 후 다시 확인해 주세요.</p>
            </div>`;
        heroScore.innerHTML = '';
        return;
    }

    let scoreHtml = starsHtml(categoryScore(result, key, 'overall') ?? scoreZodiac(map));
    if (KIND_ID === 'star') {
        const rank = rankKeys(result, KIND.order).indexOf(key) + 1;
        if (rank > 0) scoreHtml += `<span class="rank-pill">오늘 ${rank}위</span>`;
    }
    heroScore.innerHTML = scoreHtml;

    const items = Object.entries(FORTUNE_CATEGORIES)
        .filter(([cat]) => cat !== 'overall')
        .map(([cat, meta], i) => {
            const text = map[cat];
            if (!text) return '';
            return `
                <article class="fortune-item" style="animation-delay:${i * 60}ms">
                    <header>
                        <h2><span class="cat-dot" style="color:${CATEGORY_COLORS[cat]};background:${CATEGORY_COLORS[cat]}"></span>${meta.title}</h2>
                        ${starsHtml(categoryScore(result, key, cat), { label: false })}
                    </header>
                    <p>${escapeHtml(text)}</p>
                </article>`;
        }).join('');

    const lucky = luckyItems(result.date, KIND_ID === 'zodiac' ? key : `${KIND_ID}:${key}`);
    const fallbackNote = result.isFallback
        ? `<div class="notice" style="margin:0 0 14px">오늘 데이터 준비 중이라 ${formatKoreanDate(result.date).short} 운세를 대신 보여드려요.</div>`
        : '';

    content.innerHTML = `
        ${fallbackNote}
        <div class="summary">
            <div class="label">오늘의 한마디 · 종합운</div>
            <p>${escapeHtml(map.overall || '오늘은 평온한 하루가 될 거예요.')}</p>
        </div>
        <div class="fortune-list">${items}</div>
        <div class="lucky" aria-label="오늘의 행운 아이템">
            <div class="lucky-item"><div class="k">행운의 색</div><div class="v"><span class="swatch" style="background:${lucky.color.hex}"></span>${lucky.color.name}</div></div>
            <div class="lucky-item"><div class="k">행운의 숫자</div><div class="v">${lucky.number}</div></div>
            <div class="lucky-item"><div class="k">행운의 방향</div><div class="v">${lucky.direction}</div></div>
            <div class="lucky-item"><div class="k">좋은 시간대</div><div class="v">${lucky.time}</div></div>
        </div>`;

    setupShare(key, map);
}

function renderError(key) {
    document.getElementById('hero-score').innerHTML = '';
    document.getElementById('fortune-content').innerHTML = `
        <div class="state">
            <h3>운세를 불러오지 못했어요</h3>
            <p>네트워크 상태를 확인하고 다시 시도해 주세요.</p>
            <button type="button" class="btn btn-gold" id="retry">다시 시도</button>
        </div>`;
    document.getElementById('retry').addEventListener('click', () => load(key));
}

function renderOthers(key) {
    const row = document.getElementById('other-keys');
    row.innerHTML = KIND.order.map(k => `
        <a class="chip" href="${detailUrl(k)}"${k === key ? ' aria-current="page"' : ''}>
            <span class="hanja${KIND_ID === 'star' ? ' glyph-star' : ''}" aria-hidden="true">${KIND.glyph(k)}</span>${KIND.name(k)}
        </a>`).join('');
    const current = row.querySelector('.chip[aria-current="page"]');
    if (current) row.scrollLeft = current.offsetLeft - (row.clientWidth - current.offsetWidth) / 2;
}

function setupShare(key, map) {
    const url = KIND.shareUrl(key);
    const summary = map.overall ? firstSentence(map.overall) : '오늘의 운세를 확인해 보세요!';
    const title = `${KIND.emoji(key)} ${KIND.headline(key)} · ${todayInfo.short}`;

    document.getElementById('share-row').hidden = false;
    document.getElementById('share-kakao').onclick = () => shareKakao({ title, description: summary, url });
    document.getElementById('share-link').onclick = () => shareLink({ title, text: summary, url });
}

async function load(key) {
    renderSkeleton();
    try {
        const result = await loadTodayFortunes(KIND_ID);
        renderFortune(key, result);
    } catch (err) {
        console.error('운세 데이터 로딩 실패:', err);
        renderError(key);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const key = getKeyFromURL();
    if (!key) {
        renderInvalid();
        renderOthers(null);
        return;
    }
    document.title = `${KIND.headline(key)} (${todayInfo.short}) | 홍스팟 운세`;

    renderSiblings(key);
    renderHero(key);
    renderOthers(key);
    load(key);
});
