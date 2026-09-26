// ─────────────────────────────────────────────
//  상세 페이지: 띠 하나의 오늘 운세
// ─────────────────────────────────────────────

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);

const CATEGORY_COLORS = {
    money: '#e3c26b',
    work: '#8fa8e0',
    health: '#86c2a8',
    relationship: '#e08a7a'
};

function getZodiacFromURL() {
    const key = new URLSearchParams(location.search).get('zodiac');
    return key && ZODIAC_INFO[key] ? key : null;
}

function renderInvalid() {
    document.getElementById('detail-hero').innerHTML = '';
    document.getElementById('fortune-content').innerHTML = `
        <div class="state">
            <h3>어떤 띠인지 찾지 못했어요</h3>
            <p>메인에서 띠를 다시 골라 주세요.</p>
            <a class="btn btn-gold" href="./">12띠 보러 가기</a>
        </div>`;
}

function renderSiblings(key) {
    const i = ZODIAC_ORDER.indexOf(key);
    const prev = ZODIAC_ORDER[(i + 11) % 12];
    const next = ZODIAC_ORDER[(i + 1) % 12];
    document.getElementById('sibs').innerHTML = `
        <a href="detail.html?zodiac=${prev}" aria-label="이전 띠: ${ZODIAC_INFO[prev].name}">‹ ${ZODIAC_INFO[prev].name}</a>
        <a href="detail.html?zodiac=${next}" aria-label="다음 띠: ${ZODIAC_INFO[next].name}">${ZODIAC_INFO[next].name} ›</a>`;
}

function renderHero(key, score) {
    const info = ZODIAC_INFO[key];
    const years = yearsForZodiac(key, todayInfo.year).join(' · ');
    const isMine = getMyZodiac() === key;
    document.getElementById('detail-hero').innerHTML = `
        <div class="hanja-lg" aria-hidden="true">${info.hanja}</div>
        <h1>${info.name} 오늘의 운세</h1>
        <p class="meta">${todayInfo.full}</p>
        <p class="years">${years}년생</p>
        <div class="score" id="hero-score">
            ${score == null ? '<span class="skeleton skeleton-line" style="width:120px"></span>' : starsHtml(score)}
        </div>
        ${isMine ? '' : `<div style="margin-top:14px"><button type="button" class="btn btn-ghost" id="set-mine" style="padding:7px 14px;font-size:.85rem">내 띠로 설정</button></div>`}`;

    const btn = document.getElementById('set-mine');
    if (btn) btn.addEventListener('click', () => {
        setMyZodiac(key);
        btn.parentElement.remove();
        showToast(`${info.name}를 내 띠로 저장했어요`);
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

    if (!Object.keys(map).length) {
        content.innerHTML = `
            <div class="state">
                <h3>오늘의 운세를 준비 중이에요</h3>
                <p>잠시 후 다시 확인해 주세요.</p>
            </div>`;
        document.getElementById('hero-score').innerHTML = '';
        return;
    }

    document.getElementById('hero-score').innerHTML = starsHtml(scoreZodiac(map));

    const items = Object.entries(FORTUNE_CATEGORIES)
        .filter(([cat]) => cat !== 'overall')
        .map(([cat, meta], i) => {
            const text = map[cat];
            if (!text) return '';
            return `
                <article class="fortune-item" style="animation-delay:${i * 60}ms">
                    <header>
                        <h2><span class="cat-dot" style="color:${CATEGORY_COLORS[cat]};background:${CATEGORY_COLORS[cat]}"></span>${meta.title}</h2>
                        ${starsHtml(scoreText(text), { label: false })}
                    </header>
                    <p>${escapeHtml(text)}</p>
                </article>`;
        }).join('');

    const lucky = luckyItems(result.date, key);
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
    document.getElementById('other-zodiacs').innerHTML = ZODIAC_ORDER.map(k => `
        <a class="chip" href="detail.html?zodiac=${k}"${k === key ? ' aria-current="page"' : ''}>
            <span class="hanja" aria-hidden="true">${ZODIAC_INFO[k].hanja}</span>${ZODIAC_INFO[k].name}
        </a>`).join('');
    const row = document.getElementById('other-zodiacs');
    const current = row.querySelector('.chip[aria-current="page"]');
    if (current) row.scrollLeft = current.offsetLeft - (row.clientWidth - current.offsetWidth) / 2;
}

function setupShare(key, map) {
    const info = ZODIAC_INFO[key];
    const url = `${CONFIG.SITE_URL}/detail.html?zodiac=${key}`;
    const summary = map.overall ? firstSentence(map.overall) : '오늘의 운세를 확인해 보세요!';
    const title = `${info.emoji} ${info.name} 오늘의 운세 · ${todayInfo.short}`;

    document.getElementById('share-row').hidden = false;
    document.getElementById('share-kakao').onclick = () => shareKakao({ title, description: summary, url });
    document.getElementById('share-link').onclick = () => shareLink({ title, text: summary, url });
}

async function load(key) {
    renderSkeleton();
    try {
        const result = await loadTodayFortunes();
        renderFortune(key, result);
    } catch (err) {
        console.error('운세 데이터 로딩 실패:', err);
        renderError(key);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const key = getZodiacFromURL();
    if (!key) {
        renderInvalid();
        renderOthers(null);
        return;
    }
    const info = ZODIAC_INFO[key];
    document.title = `${info.name} 오늘의 운세 (${todayInfo.short}) | 홍스팟 운세`;

    renderSiblings(key);
    renderHero(key, null);
    renderOthers(key);
    load(key);
});
