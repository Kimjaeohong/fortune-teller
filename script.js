// ─────────────────────────────────────────────
//  메인 페이지: 12띠 카드
// ─────────────────────────────────────────────

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);

function renderDate() {
    document.getElementById('today-date').textContent = todayInfo.full;
}

function renderCards() {
    const grid = document.getElementById('zodiac-grid');
    const mine = getMyZodiac();

    grid.innerHTML = ZODIAC_ORDER.map((key, i) => {
        const info = ZODIAC_INFO[key];
        const years = yearsForZodiac(key, todayInfo.year).slice(-6).map(y => String(y).slice(2)).join(' · ');
        const isMine = key === mine;
        return `
            <a class="zodiac-card${isMine ? ' is-mine' : ''}" href="detail.html?zodiac=${key}"
               data-zodiac="${key}" style="animation-delay:${i * 35}ms">
                ${isMine ? '<span class="mine-badge">내 띠</span>' : ''}
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">${info.hanja}</span>
                    <div class="zc-name">${info.name}<span class="zc-emoji" aria-hidden="true">${info.emoji}</span></div>
                </div>
                <div class="zc-years">${years}년생</div>
                <p class="zc-line"><span class="skeleton skeleton-line"></span><span class="skeleton skeleton-line short"></span></p>
                <div class="zc-foot"><span class="skeleton skeleton-line" style="width:90px"></span></div>
            </a>`;
    }).join('');
}

function fillCards(result) {
    ZODIAC_ORDER.forEach(key => {
        const card = document.querySelector(`.zodiac-card[data-zodiac="${key}"]`);
        const map = result.data[key];
        const line = card.querySelector('.zc-line');
        const foot = card.querySelector('.zc-foot');
        if (!map || !map.overall) {
            line.textContent = '오늘의 운세를 준비 중이에요.';
            foot.innerHTML = '';
            return;
        }
        // "오늘은 쥐띠에게 …" 같은 반복되는 머리말은 카드에서 생략
        line.textContent = firstSentence(map.overall).replace(/^오늘은\s*\S+띠(?:에게|는|의)\s*/, '');
        foot.innerHTML = starsHtml(categoryScore(result, key, 'overall'));
    });
}

function showNotice(html) {
    document.getElementById('data-notice').innerHTML = html ? `<div class="notice">${html}</div>` : '';
}

async function loadData() {
    try {
        const result = await loadTodayFortunes();
        if (!Object.keys(result.data).length) {
            fillCards(result);
            showNotice('오늘의 운세가 아직 준비되지 않았어요. 잠시 후 다시 확인해 주세요.');
            return;
        }
        fillCards(result);
        showNotice(result.isFallback
            ? `오늘 데이터 준비 중이라 ${formatKoreanDate(result.date).short} 운세를 대신 보여드려요.`
            : '');
    } catch (err) {
        console.error('운세 데이터 로딩 실패:', err);
        document.querySelectorAll('.zc-line').forEach(el => { el.textContent = '운세를 불러오지 못했어요.'; });
        document.querySelectorAll('.zc-foot').forEach(el => { el.innerHTML = ''; });
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
        location.href = `detail.html?zodiac=${key}`;
    });
}

function setupShare() {
    const url = CONFIG.SITE_URL + '/';
    document.getElementById('share-kakao').addEventListener('click', () => shareKakao({
        title: `오늘의 띠별 운세 · ${todayInfo.short}`,
        description: '12띠 오늘의 운세를 확인해 보세요',
        url
    }));
    document.getElementById('share-link').addEventListener('click', () => shareLink({
        title: '오늘의 띠별 운세', text: '12띠 오늘의 운세를 확인해 보세요', url
    }));
}

document.addEventListener('DOMContentLoaded', () => {
    renderDate();
    renderCards();
    setupFinder();
    setupShare();
    loadData();
});
