// ─────────────────────────────────────────────
//  일간(日干) 운세 — 일주 계산 · 십신 · 합충 · 점수
//  ilgan.html(생년월일 입력) 과 ilgan/<key>.html(일간 소개 페이지의 오늘 운세) 에서 함께 쓴다.
//  문장 데이터는 ilgan-data.js (tools/build_ilgan.py 가 생성)
// ─────────────────────────────────────────────

const GZ = (() => {
    const STEMS = [
        { key: 'gap',    s: '갑', h: '甲', e: 0 }, { key: 'eul',   s: '을', h: '乙', e: 0 },
        { key: 'byeong', s: '병', h: '丙', e: 1 }, { key: 'jeong', s: '정', h: '丁', e: 1 },
        { key: 'mu',     s: '무', h: '戊', e: 2 }, { key: 'gi',    s: '기', h: '己', e: 2 },
        { key: 'gyeong', s: '경', h: '庚', e: 3 }, { key: 'sin',   s: '신', h: '辛', e: 3 },
        { key: 'im',     s: '임', h: '壬', e: 4 }, { key: 'gye',   s: '계', h: '癸', e: 4 }
    ];
    const BRANCHES = [
        { s: '자', h: '子', a: '쥐' }, { s: '축', h: '丑', a: '소' }, { s: '인', h: '寅', a: '호랑이' },
        { s: '묘', h: '卯', a: '토끼' }, { s: '진', h: '辰', a: '용' }, { s: '사', h: '巳', a: '뱀' },
        { s: '오', h: '午', a: '말' }, { s: '미', h: '未', a: '양' }, { s: '신', h: '申', a: '원숭이' },
        { s: '유', h: '酉', a: '닭' }, { s: '술', h: '戌', a: '개' }, { s: '해', h: '亥', a: '돼지' }
    ];
    // 오행: 0 목 1 화 2 토 3 금 4 수
    const ELEMENTS = [
        { name: '목', h: '木', color: '초록', hex: '#5f9e6e', dir: '동쪽', nums: [3, 8] },
        { name: '화', h: '火', color: '빨강', hex: '#d5654f', dir: '남쪽', nums: [2, 7] },
        { name: '토', h: '土', color: '노랑', hex: '#d4a72c', dir: '중앙', nums: [5, 10] },
        { name: '금', h: '金', color: '흰색', hex: '#ece8de', dir: '서쪽', nums: [4, 9] },
        { name: '수', h: '水', color: '남색', hex: '#2f4a7c', dir: '북쪽', nums: [1, 6] }
    ];

    // 율리우스 적일 기준 60갑자: (JDN + 49) mod 60, 0 = 갑자 (1949-10-01 갑자일, 2026-05-01 을해일로 검증)
    function dayIndex(y, m, d) {
        const jdn = Math.floor(Date.UTC(y, m - 1, d) / 86400000) + 2440588;
        return ((jdn + 49) % 60 + 60) % 60;
    }
    function pillar(idx) {
        const st = STEMS[idx % 10], br = BRANCHES[idx % 12];
        return { idx, stem: idx % 10, branch: idx % 12, name: st.s + br.s, hanja: st.h + br.h, st, br };
    }
    function pillarOfDate(dateStr) {
        const [y, m, d] = dateStr.split('-').map(Number);
        return pillar(dayIndex(y, m, d));
    }
    function addDays(dateStr, n) {
        const [y, m, d] = dateStr.split('-').map(Number);
        const t = new Date(Date.UTC(y, m - 1, d + n));
        return t.toISOString().slice(0, 10);
    }

    /** 내 일간(me) 기준으로 본 상대 천간(other)의 십신 */
    function sipsin(me, other) {
        const a = STEMS[me].e, b = STEMS[other].e;
        const same = (me % 2) === (other % 2);
        switch ((b - a + 5) % 5) {
            case 0: return same ? 'bigyeon' : 'geopjae';
            case 1: return same ? 'siksin' : 'sanggwan';
            case 2: return same ? 'pyeonjae' : 'jeongjae';
            case 3: return same ? 'pyeongwan' : 'jeonggwan';
            default: return same ? 'pyeonin' : 'jeongin';
        }
    }

    /** 내 일지(mine)와 오늘 지지(today)의 관계 */
    function branchRelation(mine, today) {
        if (mine === today) return 'same';
        if (Math.abs(mine - today) === 6) return 'chung';
        if ((mine + today) % 12 === 1) return 'hap';            // 자축·인해·묘술·진유·사신·오미
        if (mine % 4 === today % 4) return 'samhap';             // 신자진·해묘미·인오술·사유축
        return null;
    }

    return { STEMS, BRANCHES, ELEMENTS, dayIndex, pillar, pillarOfDate, addDays, sipsin, branchRelation };
})();

const ILGAN_SCORE = {
    base:   { bigyeon: 3, geopjae: 2.5, siksin: 4, sanggwan: 3, pyeonjae: 3.5, jeongjae: 4, pyeongwan: 2.5, jeonggwan: 4, pyeonin: 3, jeongin: 4 },
    branch: { hap: 1, samhap: 0.5, chung: -1, same: 0 },
    // 카테고리별 기울기 (재물 · 일 · 관계 · 건강)
    bias: {
        bigyeon:   [-0.5, 0, 0.5, 0.5],  geopjae:   [-1, 0.5, 0, 0],
        siksin:    [0.5, 0.5, 0.5, 1],   sanggwan:  [0, 0.5, -0.5, 0],
        pyeonjae:  [1, 0, 0.5, -0.5],    jeongjae:  [1, 0.5, 0, 0],
        pyeongwan: [-0.5, 0.5, -0.5, -0.5], jeonggwan: [0, 1, 0.5, 0],
        pyeonin:   [-0.5, 0, -0.5, 0.5], jeongin:   [0, 0.5, 0.5, 1]
    }
};
const ILGAN_CATS = [
    { key: 'money', title: '재물운', color: '#e3c26b' },
    { key: 'work', title: '일·학업운', color: '#8fa8e0' },
    { key: 'relation', title: '인연·관계운', color: '#e08a7a' },
    { key: 'health', title: '건강·마음', color: '#86c2a8' }
];

const clampScore = x => Math.max(1, Math.min(5, Math.round(x)));

/** 받침에 따라 조사 고르기: josa('병화', '은', '는') → '병화는' */
function josa(word, withFinal, withoutFinal) {
    const code = word.charCodeAt(word.length - 1) - 0xAC00;
    const hasFinal = code >= 0 && code <= 11171 && code % 28 !== 0;
    return word + (hasFinal ? withFinal : withoutFinal);
}
const pickBy = (arr, seed) => arr[hashString(seed) % arr.length];

/**
 * 하루 운세 계산
 * me: { stem, branch|null, label }  — branch 가 없으면 천간 관계만 본다 (일간 소개 페이지용)
 */
function ilganFortune(me, dateStr) {
    const day = GZ.pillarOfDate(dateStr);
    const rel = GZ.sipsin(me.stem, day.stem);
    const br = me.branch == null ? null : GZ.branchRelation(me.branch, day.branch);
    const S = ILGAN_DATA.sipsin[rel];
    const seed = `${dateStr}:${me.label}`;
    const total = ILGAN_SCORE.base[rel] + (br ? ILGAN_SCORE.branch[br] : 0);
    const cats = ILGAN_CATS.map((c, i) => {
        const jitter = ((hashString(seed + c.key) % 3) - 1) * 0.5;   // -0.5 · 0 · +0.5
        return { ...c, score: clampScore(total + ILGAN_SCORE.bias[rel][i] + jitter), text: pickBy(S[c.key], seed + c.key) };
    });
    return {
        date: dateStr, day, rel, S, branchRel: br,
        branchNote: br ? pickBy(ILGAN_DATA.branch[br], seed + 'br') : '',
        score: clampScore(total),
        headline: pickBy(S.headline, seed + 'h'),
        tip: pickBy(S.tip, seed + 't'),
        keyword: pickBy(S.keywords, seed + 'k'),
        cats
    };
}

/** 나를 북돋는 오행 = 나를 낳는 오행 (인성) */
function supportElement(stem) {
    return GZ.ELEMENTS[(GZ.STEMS[stem].e + 4) % 5];
}

const BRANCH_REL_LABEL = { hap: '육합', samhap: '반합', chung: '충', same: '같은 기운' };

/* ---------- 공용 마크업 ---------- */

function relPill(f) {
    return `<span class="sipsin-pill">${f.S.name}<small>${f.S.hanja}</small></span>`;
}

function catsHtml(f) {
    return f.cats.map(c => `
        <article class="fortune-item">
            <header>
                <h3><span class="cat-dot" style="color:${c.color};background:${c.color}"></span>${c.title}</h3>
                ${starsHtml(c.score, { label: false })}
            </header>
            <p>${escapeHtml(c.text)}</p>
        </article>`).join('');
}

function weekHtml(me, startDate) {
    return Array.from({ length: 7 }, (_, i) => {
        const date = GZ.addDays(startDate, i);
        const f = ilganFortune(me, date);
        const info = formatKoreanDate(date);
        return `
            <li class="week-day${i === 0 ? ' is-today' : ''}">
                <span class="wd-date">${i === 0 ? '오늘' : info.short.replace(/^\d+월 /, '') + ' ' + info.weekday.slice(0, 1)}</span>
                <span class="wd-bar"><i style="height:${f.score * 20}%"></i></span>
                <span class="wd-score">${f.score}</span>
                <span class="wd-rel">${f.S.name}</span>
            </li>`;
    }).join('');
}

/* ═════════════ ilgan.html — 생년월일로 보는 오늘의 일간 운세 ═════════════ */

const BIRTH_KEY = 'fortune:ilgan-birth';

function readBirth() {
    try {
        const b = JSON.parse(localStorage.getItem(BIRTH_KEY));
        return b && b.y && b.m && b.d ? b : null;
    } catch { return null; }
}
function writeBirth(b) {
    try { localStorage.setItem(BIRTH_KEY, JSON.stringify(b)); } catch { /* 무시 */ }
}

function birthPillar(b) {
    const base = `${b.y}-${String(b.m).padStart(2, '0')}-${String(b.d).padStart(2, '0')}`;
    return GZ.pillarOfDate(b.late ? GZ.addDays(base, 1) : base);
}

function renderMine(b) {
    const box = document.getElementById('my-ilgan');
    if (!box) return;
    const today = kstDateString();
    const p = birthPillar(b);
    const prof = ILGAN_DATA.ilgan[p.stem];
    const me = { stem: p.stem, branch: p.branch, label: p.name };
    const f = ilganFortune(me, today);
    const sup = supportElement(p.stem);
    const luckyNum = sup.nums[hashString(today + p.name) % 2];
    const info = formatKoreanDate(today);

    box.hidden = false;
    box.innerHTML = `
        <div class="ilju-card">
            <div class="ilju-glyph" aria-hidden="true"><span>${p.st.h}</span><span>${p.br.h}</span></div>
            <div class="ilju-body">
                <div class="ilju-label">${b.y}년 ${b.m}월 ${b.d}일생${b.late ? ' · 밤 11시 이후' : ''}</div>
                <h2>${p.name}일주 <small>${p.hanja}</small></h2>
                <p>일간 <b>${prof.name}(${prof.hanja}${GZ.ELEMENTS[p.st.e].h})</b> · ${escapeHtml(prof.image)}</p>
                <a class="ilju-more" href="ilgan/${prof.key}.html">${prof.name} 일간 성격 보기 →</a>
            </div>
            <button type="button" class="link-btn ilju-reset" id="birth-reset">다시 입력</button>
        </div>

        <div class="ilgan-today">
            <div class="ilgan-today-head">
                <div>
                    <div class="eyebrow-sm">${info.full} · 오늘은 ${f.day.name}(${f.day.hanja})일</div>
                    <h2>오늘은 ${relPill(f)}의 날 <span class="tagline">${escapeHtml(f.S.tagline)}</span></h2>
                </div>
                <div class="ilgan-score">${starsHtml(f.score)}</div>
            </div>
            <p class="ilgan-explain">${escapeHtml(f.S.explain)}</p>

            <div class="summary">
                <div class="label">오늘의 한마디 · 종합운</div>
                <p>${escapeHtml(f.headline)}</p>
                ${f.branchNote ? `<p class="branch-note"><span class="branch-tag branch-tag--${f.branchRel}">${p.br.s}·${f.day.br.s} ${BRANCH_REL_LABEL[f.branchRel]}</span>${escapeHtml(f.branchNote)}</p>` : ''}
            </div>

            <div class="fortune-list">${catsHtml(f)}</div>

            <div class="lucky" aria-label="오늘의 행운 포인트">
                <div class="lucky-item"><div class="k">기운을 채우는 색</div><div class="v"><span class="swatch" style="background:${sup.hex}"></span>${sup.color}</div></div>
                <div class="lucky-item"><div class="k">좋은 방향</div><div class="v">${sup.dir}</div></div>
                <div class="lucky-item"><div class="k">행운의 숫자</div><div class="v">${luckyNum}</div></div>
                <div class="lucky-item"><div class="k">오늘의 키워드</div><div class="v">#${escapeHtml(f.keyword)}</div></div>
            </div>
            <p class="panel-hint lucky-hint">행운의 색·방향·숫자는 ${josa(prof.name, '을', '를')} 북돋는 ${sup.name}(${sup.h}) 기운에서 골랐어요.</p>

            <div class="summary ilgan-tip">
                <div class="label">오늘 해 볼 작은 일</div>
                <p>${escapeHtml(f.tip)}</p>
            </div>
        </div>

        <section class="ilgan-week" aria-labelledby="week-title">
            <div class="section-head"><h2 id="week-title">7일 운세 흐름</h2><span>${p.name}일주 기준</span></div>
            <ol class="week-chart">${weekHtml(me, today)}</ol>
        </section>

        <div class="share-row">
            <button type="button" class="btn btn-kakao" id="share-kakao">카카오톡 공유</button>
            <button type="button" class="btn btn-ghost" id="share-link">링크 복사</button>
        </div>`;

    document.getElementById('birth-reset').addEventListener('click', () => {
        try { localStorage.removeItem(BIRTH_KEY); } catch { /* 무시 */ }
        box.hidden = true;
        document.getElementById('birth-form').hidden = false;
        document.getElementById('birth-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    const url = `${CONFIG.SITE_URL}/ilgan.html`;
    const title = `☯ 오늘 ${p.name}일주의 운세 · ${info.short}`;
    const desc = `오늘은 ${f.S.name}의 날 — ${f.headline}`;
    document.getElementById('share-kakao').addEventListener('click', () => shareKakao({ title, description: desc, url, buttonTitle: '내 일주 운세 보기' }));
    document.getElementById('share-link').addEventListener('click', () => shareLink({ title, text: desc, url }));
}

function renderAllStems(dateStr) {
    const grid = document.getElementById('stem-grid');
    if (!grid) return;
    const rows = GZ.STEMS.map((st, i) => {
        const f = ilganFortune({ stem: i, branch: null, label: st.s }, dateStr);
        return { i, st, f, prof: ILGAN_DATA.ilgan[i] };
    });
    const rank = rows.slice().sort((a, b) => b.f.score - a.f.score || hashString(dateStr + a.st.key) - hashString(dateStr + b.st.key))
        .map(r => r.i);
    grid.innerHTML = rows.map(({ i, st, f, prof }) => {
        const r = rank.indexOf(i) + 1;
        return `
            <a class="zodiac-card stem-card" href="ilgan/${st.key}.html" style="animation-delay:${i * 35}ms">
                <div class="zc-top">
                    <span class="hanja" aria-hidden="true">${st.h}</span>
                    <div class="zc-name">${prof.name}</div>
                </div>
                <div class="zc-years">${escapeHtml(prof.image)}</div>
                <p class="zc-line"><b class="stem-rel">${f.S.name}의 날</b> ${escapeHtml(f.headline)}</p>
                <div class="zc-foot">${starsHtml(f.score, { label: false })}<span class="rank-badge${r <= 3 ? ' top' : ''}">${r}위</span></div>
            </a>`;
    }).join('');
}

function setupBirthForm() {
    const form = document.getElementById('birth-form');
    if (!form) return;
    const ys = document.getElementById('b-year'), ms = document.getElementById('b-month'), ds = document.getElementById('b-day');
    const thisYear = Number(kstDateString().slice(0, 4));
    ys.innerHTML = '<option value="">태어난 해</option>' +
        Array.from({ length: thisYear - 1919 }, (_, i) => thisYear - i).map(y => `<option value="${y}">${y}년</option>`).join('');
    ms.innerHTML = '<option value="">월</option>' + Array.from({ length: 12 }, (_, i) => `<option value="${i + 1}">${i + 1}월</option>`).join('');
    const fillDays = () => {
        const y = Number(ys.value) || 2000, m = Number(ms.value) || 1;
        const max = new Date(Date.UTC(y, m, 0)).getUTCDate();
        const prev = ds.value;
        ds.innerHTML = '<option value="">일</option>' + Array.from({ length: max }, (_, i) => `<option value="${i + 1}">${i + 1}일</option>`).join('');
        if (prev && Number(prev) <= max) ds.value = prev;
    };
    fillDays();
    ys.addEventListener('change', fillDays);
    ms.addEventListener('change', fillDays);
    if (!ys.value) ys.value = '1990';

    form.addEventListener('submit', e => {
        e.preventDefault();
        const b = { y: Number(ys.value), m: Number(ms.value), d: Number(ds.value), late: document.getElementById('b-late').checked };
        if (!b.y || !b.m || !b.d) { showToast('태어난 날을 모두 골라 주세요'); return; }
        writeBirth(b);
        form.hidden = true;
        renderMine(b);
        setTimeout(() => document.getElementById('my-ilgan').scrollIntoView({ behavior: 'smooth', block: 'start' }), 40);
    });

    const saved = readBirth();
    if (saved) {
        ys.value = saved.y; ms.value = saved.m; fillDays(); ds.value = saved.d;
        document.getElementById('b-late').checked = !!saved.late;
        form.hidden = true;
        renderMine(saved);
    }
}

/* ═════════════ ilgan/<key>.html — 일간 소개 페이지의 오늘 운세 ═════════════ */

function renderStemToday() {
    const box = document.getElementById('stem-today');
    if (!box) return;
    const stem = Number(box.dataset.stem);
    const today = kstDateString();
    const st = GZ.STEMS[stem];
    const f = ilganFortune({ stem, branch: null, label: st.s }, today);
    const info = formatKoreanDate(today);
    box.innerHTML = `
        <div class="ilgan-today-head">
            <div>
                <div class="eyebrow-sm">${info.full} · ${f.day.name}(${f.day.hanja})일</div>
                <h2>오늘 ${josa(ILGAN_DATA.ilgan[stem].name, '은', '는')} ${relPill(f)}의 날</h2>
            </div>
            <div class="ilgan-score">${starsHtml(f.score)}</div>
        </div>
        <div class="summary"><div class="label">${escapeHtml(f.S.tagline)}</div><p>${escapeHtml(f.headline)}</p></div>
        <div class="fortune-list">${catsHtml(f)}</div>
        <p class="panel-hint">일간만으로 본 운세예요. 생년월일을 넣으면 일지의 합·충까지 반영한 내 일주 운세를 볼 수 있어요.</p>
        <a class="btn btn-gold" href="/ilgan.html">내 일주로 자세히 보기 →</a>`;
}

document.addEventListener('DOMContentLoaded', () => {
    const today = kstDateString();
    const dateEl = document.getElementById('today-date');
    if (dateEl) {
        const p = GZ.pillarOfDate(today);
        dateEl.textContent = `${formatKoreanDate(today).full} · ${p.name}(${p.hanja})일`;
    }
    setupBirthForm();
    renderAllStems(today);
    renderStemToday();
});
