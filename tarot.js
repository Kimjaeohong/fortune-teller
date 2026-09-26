// ─────────────────────────────────────────────
//  타로
// ─────────────────────────────────────────────

const SPREADS = {
    'single':              { title: '한 장 타로',          positions: ['지금의 흐름'] },
    'past-present-future': { title: '과거·현재·미래 타로',  positions: ['과거', '현재', '미래'] },
    'love':                { title: '연애운 타로',          positions: ['나의 마음', '상대방의 마음', '관계의 미래'] },
    'choice':              { title: '양자택일 타로',        positions: ['A를 선택하면', 'B를 선택하면', '조언'] },
    'work':                { title: '직업운 타로',          positions: ['현재 상황', '넘어야 할 장애물', '조언', '최종 결과'] },
    'money':               { title: '재물운 타로',          positions: ['현재 재정 상황', '들어올 기회', '재물 조언'] },
    'study':               { title: '학업·시험운 타로',     positions: ['현재 학업 상태', '극복할 점', '시험·학업 결과'] },
    'year':                { title: '올해의 운세 타로',     positions: ['사랑·관계', '직업·경력', '재물·금전', '건강', '올해의 조언'] }
};

const DECK_SIZE_ON_TABLE = 24;
const REVERSED_CHANCE = 0.5;

// Rider-Waite 이미지 (sacred-texts.com, 퍼블릭 도메인). 실패 시 이모지로 대체.
const IMAGE_BASE = 'https://www.sacred-texts.com/tarot/pkt/img/';
const SUIT_CODES = ['wa', 'cu', 'sw', 'pe'];
const RANK_CODES = ['ac', '02', '03', '04', '05', '06', '07', '08', '09', '10', 'pa', 'kn', 'qu', 'ki'];

function tarotImageUrl(id) {
    if (id < 22) return `${IMAGE_BASE}ar${String(id).padStart(2, '0')}.jpg`;
    const n = id - 22;
    const suit = SUIT_CODES[Math.floor(n / 14)];
    const rank = RANK_CODES[n % 14];
    return suit && rank ? `${IMAGE_BASE}${suit}${rank}.jpg` : null;
}

function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function cardArtHtml(card, reversed) {
    const url = tarotImageUrl(card.id);
    const fallback = `<span class="fallback">${card.emoji}</span>`;
    if (!url) return fallback;
    return `<img src="${url}" alt="${escapeHtml(card.name)}" loading="eager"
                onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'fallback',textContent:'${card.emoji}'}))">`;
}

/* ---------- 상태 ---------- */

const state = {
    type: 'single',
    deck: [],
    drawn: []
};

const el = {
    spreads: document.getElementById('spreads'),
    guide: document.getElementById('tarot-guide'),
    deck: document.getElementById('card-deck'),
    drawBtn: document.getElementById('draw-btn'),
    results: document.getElementById('results'),
    resultCards: document.getElementById('result-cards'),
    resultsTitle: document.getElementById('results-title')
};

function need() { return SPREADS[state.type].positions.length; }

function updateGuide() {
    const n = need();
    const picked = state.drawn.length;
    if (picked >= n) {
        el.guide.innerHTML = '카드를 모두 골랐어요. <b>결과 보기</b>를 눌러 주세요.';
    } else {
        const nextPos = SPREADS[state.type].positions[picked];
        el.guide.innerHTML = n === 1
            ? '마음속 질문을 떠올리며 <b>카드 한 장</b>을 골라 주세요'
            : `<b>${picked + 1}/${n}</b> · '${nextPos}' 자리에 놓을 카드를 골라 주세요`;
    }
}

function resetTable() {
    state.deck = shuffle(TAROT_CARDS);
    state.drawn = [];
    el.results.classList.remove('show');
    el.drawBtn.hidden = true;

    el.deck.innerHTML = Array.from({ length: DECK_SIZE_ON_TABLE }, (_, i) => `
        <button type="button" class="tarot-card" data-slot="${i}" aria-label="${i + 1}번째 카드" style="animation-delay:${i * 18}ms">
            <span class="face back" aria-hidden="true">✦</span>
            <span class="face front"></span>
        </button>`).join('');
    updateGuide();
}

function pickCard(button) {
    if (button.classList.contains('flipped') || state.drawn.length >= need()) return;

    const card = state.deck.pop();               // 뽑은 카드는 덱에서 제거 → 중복 없음
    const reversed = Math.random() < REVERSED_CHANCE;
    state.drawn.push({ card, reversed });

    const front = button.querySelector('.front');
    front.classList.toggle('reversed', reversed);
    front.innerHTML = cardArtHtml(card, reversed);
    button.classList.add('flipped');
    button.setAttribute('aria-label', `${card.name}${reversed ? ' (역방향)' : ''}`);

    if (state.drawn.length >= need()) {
        el.deck.querySelectorAll('.tarot-card:not(.flipped)').forEach(b => { b.disabled = true; });
        setTimeout(() => {
            el.drawBtn.hidden = false;
            if (need() === 1) showResults();
        }, 750);
    }
    updateGuide();
}

function showResults() {
    const spread = SPREADS[state.type];
    el.resultsTitle.textContent = spread.title;
    el.resultCards.innerHTML = state.drawn.map(({ card, reversed }, i) => `
        <article class="result-card" style="animation-delay:${i * 120}ms">
            <div class="result-art${reversed ? ' reversed' : ''}">${cardArtHtml(card, reversed)}</div>
            <div>
                <div class="result-pos">${escapeHtml(spread.positions[i] || `${i + 1}번째 카드`)}</div>
                <h3>${escapeHtml(card.name)}
                    <span class="badge ${reversed ? 'rev' : 'up'}">${reversed ? '역방향' : '정방향'}</span>
                </h3>
                <p>${escapeHtml(reversed ? card.reversed : card.upright)}</p>
            </div>
        </article>`).join('');

    el.results.classList.add('show');
    el.drawBtn.hidden = true;
    setTimeout(() => el.results.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150);
}

function shareSummary() {
    const spread = SPREADS[state.type];
    return state.drawn
        .map(({ card, reversed }, i) => `${spread.positions[i]}: ${card.name.split('(')[0].trim()}${reversed ? '(역)' : ''}`)
        .join('\n');
}

/* ---------- 이벤트 ---------- */

el.spreads.addEventListener('click', e => {
    const btn = e.target.closest('.spread-btn');
    if (!btn) return;
    el.spreads.querySelectorAll('.spread-btn').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    state.type = btn.dataset.type;
    resetTable();
});

el.deck.addEventListener('click', e => {
    const btn = e.target.closest('.tarot-card');
    if (btn && !btn.disabled) pickCard(btn);
});

el.drawBtn.addEventListener('click', showResults);

document.getElementById('reset-btn').addEventListener('click', () => {
    resetTable();
    el.spreads.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

document.getElementById('share-kakao').addEventListener('click', () => shareKakao({
    title: `🔮 ${SPREADS[state.type].title} 결과`,
    description: shareSummary(),
    url: `${CONFIG.SITE_URL}/tarot.html`,
    buttonTitle: '나도 타로 보기'
}));

document.getElementById('share-link').addEventListener('click', () => shareLink({
    title: SPREADS[state.type].title,
    text: shareSummary(),
    url: `${CONFIG.SITE_URL}/tarot.html`
}));

resetTable();
