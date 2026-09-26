// ─────────────────────────────────────────────
//  별자리 목록 페이지: 순위 + 12별자리 카드
// ─────────────────────────────────────────────

const todayStr = kstDateString();
const todayInfo = formatKoreanDate(todayStr);
const STAR = FORTUNE_KINDS.star;

function renderDate() {
    document.getElementById('today-date').textContent = todayInfo.full;
}

function renderCards() {
    const grid = document.getElementById('star-grid');
    const mine = getMyKey('star');

    grid.innerHTML = STAR_ORDER.map((key, i) => {
        const info = STAR_INFO[key];
        const isMine = key === mine;
        return `
            <a class="zodiac-card${isMine ? ' is-mine' : ''}" href="star-detail.html?sign=${key}"
               data-key="${key}" style="animation-delay:${i * 35}ms">
                ${isMine ? '<span class="mine-badge">내 별자리</span>' : ''}
                <div class="zc-top">
                    <span class="hanja glyph-star" aria-hidden="true">${info.symbol}</span>
                    <div class="zc-name">${info.name}</div>
                </div>
                <div class="zc-years">${starDateRange(key)} · ${info.element}</div>
                <p class="zc-line"><span class="skeleton skeleton-line"></span><span class="skeleton skeleton-line short"></span></p>
                <div class="zc-foot"><span class="skeleton skeleton-line" style="width:90px"></span></div>
            </a>`;
    }).join('');

    document.getElementById('top3').innerHTML = [1, 2, 3].map(() => `
        <li class="top3-item"><span class="skeleton skeleton-line" style="width:70%"></span></li>`).join('');
}

function fillCards(result) {
    const ranking = rankKeys(result, STAR_ORDER);

    STAR_ORDER.forEach(key => {
        const card = document.querySelector(`.zodiac-card[data-key="${key}"]`);
        const map = result.data[key];
        const line = card.querySelector('.zc-line');
        const foot = card.querySelector('.zc-foot');
        if (!map || !map.overall) {
            line.textContent = '오늘의 운세를 준비 중이에요.';
            foot.innerHTML = '';
            return;
        }
        line.textContent = firstSentence(map.overall);
        const rank = ranking.indexOf(key) + 1;
        foot.innerHTML = starsHtml(categoryScore(result, key, 'overall'), { label: false })
            + (rank > 0 ? `<span class="rank-badge${rank <= 3 ? ' top' : ''}">${rank}위</span>` : '');
    });

    document.getElementById('top3').innerHTML = ranking.slice(0, 3).map((key, i) => `
        <li class="top3-item rank-${i + 1}">
            <a href="star-detail.html?sign=${key}">
                <span class="top3-rank">${i + 1}</span>
                <span class="hanja glyph-star" aria-hidden="true">${STAR_INFO[key].symbol}</span>
                <span class="top3-body">
                    <strong>${STAR_INFO[key].name}</strong>
                    <small>${escapeHtml(firstSentence(result.data[key].overall))}</small>
                </span>
            </a>
        </li>`).join('');
}

function showNotice(html) {
    document.getElementById('data-notice').innerHTML = html ? `<div class="notice">${html}</div>` : '';
}

async function loadData() {
    try {
        const result = await loadTodayFortunes('star');
        fillCards(result);
        if (!Object.keys(result.data).length) {
            showNotice('오늘의 운세가 아직 준비되지 않았어요. 잠시 후 다시 확인해 주세요.');
        } else {
            showNotice(result.isFallback
                ? `오늘 데이터 준비 중이라 ${formatKoreanDate(result.date).short} 운세를 대신 보여드려요.`
                : '');
        }
    } catch (err) {
        console.error('운세 데이터 로딩 실패:', err);
        document.querySelectorAll('.zc-line').forEach(el => { el.textContent = '운세를 불러오지 못했어요.'; });
        document.querySelectorAll('.zc-foot').forEach(el => { el.innerHTML = ''; });
        document.getElementById('top3').innerHTML = '';
        showNotice('네트워크가 불안정해요. <button type="button" class="btn btn-ghost" id="retry" style="margin-left:6px;padding:4px 12px">다시 시도</button>');
        document.getElementById('retry').addEventListener('click', () => { renderCards(); loadData(); });
    }
}

function setupFinder() {
    const month = document.getElementById('birth-month');
    const day = document.getElementById('birth-day');
    for (let m = 1; m <= 12; m++) month.insertAdjacentHTML('beforeend', `<option value="${m}">${m}월</option>`);

    const fillDays = () => {
        const m = parseInt(month.value, 10);
        const max = m ? new Date(2024, m, 0).getDate() : 31;   // 윤년 기준 (2월 29일 허용)
        const prev = day.value;
        day.innerHTML = '<option value="">일</option>' +
            Array.from({ length: max }, (_, i) => `<option value="${i + 1}">${i + 1}일</option>`).join('');
        if (prev && parseInt(prev, 10) <= max) day.value = prev;
    };
    fillDays();
    month.addEventListener('change', fillDays);

    document.getElementById('finder').addEventListener('submit', e => {
        e.preventDefault();
        const m = parseInt(month.value, 10);
        const d = parseInt(day.value, 10);
        if (!m || !d) {
            showToast('태어난 월과 일을 골라 주세요');
            return;
        }
        const key = starFromDate(m, d);
        setMyKey('star', key);
        location.href = `star-detail.html?sign=${key}`;
    });
}

function setupShare() {
    const url = `${CONFIG.SITE_URL}/star.html`;
    document.getElementById('share-kakao').addEventListener('click', () => shareKakao({
        title: `오늘의 별자리 운세 · ${todayInfo.short}`,
        description: '12별자리 오늘의 운세와 순위를 확인해 보세요',
        url
    }));
    document.getElementById('share-link').addEventListener('click', () => shareLink({
        title: '오늘의 별자리 운세', text: '12별자리 오늘의 운세와 순위를 확인해 보세요', url
    }));
}

document.addEventListener('DOMContentLoaded', () => {
    renderDate();
    renderCards();
    setupFinder();
    setupShare();
    loadData();
});
