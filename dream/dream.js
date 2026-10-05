// ─────────────────────────────────────────────
//  꿈해몽 — 검색(메인) · 공유(개별 페이지)
//  페이지 본문은 tools/build_dreams.py 가 미리 만들어 둔 정적 HTML
// ─────────────────────────────────────────────

(function () {
    const VERDICT = {
        good: { short: '좋음' },
        mixed: { short: '반반' },
        caution: { short: '주의' }
    };

    const norm = s => String(s || '').toLowerCase().replace(/[\s·.,!?~'"()\-]/g, '');
    const stripTail = s => s.replace(/(꿈해몽|해몽|풀이|의미|뜻)$/, '').replace(/꿈$/, '');

    /* ---------- 공유 ---------- */

    document.querySelectorAll('.share-row[data-share-url]').forEach(row => {
        const title = row.dataset.shareTitle;
        const text = row.dataset.shareText;
        const url = row.dataset.shareUrl;
        row.querySelectorAll('[data-share]').forEach(btn => btn.addEventListener('click', () => {
            if (btn.dataset.share === 'kakao') {
                shareKakao({ title: `🌙 ${title}`, description: text, url, buttonTitle: '해몽 보러 가기' });
            } else {
                shareLink({ title, text, url });
            }
        }));
    });

    /* ---------- 검색 (메인 페이지에만 데이터가 있음) ---------- */

    const dataEl = document.getElementById('dream-index');
    if (!dataEl) return;

    let INDEX = [];
    try { INDEX = JSON.parse(dataEl.textContent); } catch { return; }

    INDEX.forEach(d => {
        d._title = norm(d.t);
        d._aliases = d.a.map(norm);
        d._cases = d.c.map(norm);
        // 핵심 단어: "강아지·개 꿈" → ["강아지", "개"]
        d._keys = [...new Set([d.t, ...d.a]
            .flatMap(x => x.replace(/꿈.*$/, '').split('·'))
            .map(norm).filter(Boolean))];
    });

    function search(raw) {
        const q = stripTail(norm(raw));
        if (!q) return [];
        const out = [];
        INDEX.forEach((d, order) => {
            let score = 0, caseIdx = -1;
            const titleCore = stripTail(d._title);
            if (titleCore === q || d._aliases.some(a => stripTail(a) === q)) score = 100;
            else if (d._title.includes(q) || d._aliases.some(a => a.includes(q))) score = 80;
            if (score < 80) {
                const i = d._cases.findIndex(c => c.includes(q));
                if (i >= 0) { score = Math.max(score, 60); caseIdx = i; }
            }
            if (!score) {
                // 문장으로 검색한 경우: "어제 뱀이 나왔어요" → 핵심 단어 포함 여부
                // 한 글자 단어(뱀·돈·불…)는 조사가 붙은 경우만 인정 — "뱀이", "돈을", "불꿈"
                const hit = d._keys.find(k => (k.length >= 2 && q.includes(k))
                    || (k.length === 1 && (q === k || q.startsWith(k) || new RegExp(k + '(이|가|을|를|은|는|에게|한테|꿈|떼|들|이랑|하고)').test(q))));
                if (hit) score = hit.length >= 2 ? 40 : 30;
                // 활용형: "이가 빠졌어요" ↔ "이가 빠지는", "돈을 주웠어" ↔ "돈을 줍는"
                if (!hit && d._keys.some(k => k.length >= 4 && q.includes(k.slice(0, -2)))) score = 35;
                const i = d._cases.findIndex(c => q.includes(stripTail(c)) && stripTail(c).length >= 3);
                if (i >= 0) { score = Math.max(score, 50); caseIdx = i; }
            }
            if (score) out.push({ d, score, caseIdx, order });
        });
        out.sort((a, b) => b.score - a.score || a.order - b.order);
        // 확실한 결과가 있으면 어설프게 걸린 결과는 숨긴다 ("강아지" 검색에 "강 꿈"이 섞이지 않게)
        const best = out.length ? out[0].score : 0;
        return out.filter(x => best < 60 || x.score >= 50).slice(0, 30);
    }

    const box = document.getElementById('dream-results');
    const list = document.getElementById('results-list');
    const titleEl = document.getElementById('results-title');
    const input = document.getElementById('dream-q');
    const form = input && input.closest('form');

    function render(raw) {
        const q = raw.trim();
        if (!q) { box.hidden = true; return; }
        const hits = search(q);
        box.hidden = false;
        titleEl.textContent = hits.length ? `'${q}' 검색 결과 ${hits.length}개` : `'${q}' 검색 결과`;
        if (!hits.length) {
            list.innerHTML = `<li class="dream-empty">
                <p>아직 이 꿈은 준비되지 않았어요. 꿈에 나온 <b>핵심 단어 하나</b>로 다시 찾아보세요.</p>
                <p class="panel-hint">예: 뱀 · 돈 · 물 · 이빨 · 엄마</p></li>`;
            return;
        }
        list.innerHTML = hits.map(({ d, caseIdx }) => `
            <li><a class="dream-card" href="/dream/${d.s}.html${caseIdx >= 0 ? `#case-${caseIdx + 1}` : ''}">
                <span class="dream-card-top"><strong>${escapeHtml(d.t)}</strong><span class="verdict verdict--${d.v} verdict--sm">${VERDICT[d.v].short}</span></span>
                ${caseIdx >= 0
                    ? `<small class="dream-card-case">→ ${escapeHtml(d.c[caseIdx])} 풀이 보기</small>`
                    : `<small>${escapeHtml(d.m)}</small>`}
            </a></li>`).join('');
    }

    let timer;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => render(input.value), 120);
    });
    form.addEventListener('submit', ev => {
        ev.preventDefault();
        render(input.value);
        const q = input.value.trim();
        history.replaceState(null, '', q ? `?q=${encodeURIComponent(q)}` : location.pathname);
        if (q) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    document.getElementById('results-clear').addEventListener('click', () => {
        input.value = '';
        render('');
        history.replaceState(null, '', location.pathname);
        input.focus();
    });

    const initial = new URLSearchParams(location.search).get('q');
    if (initial) {
        input.value = initial;
        render(initial);
        setTimeout(() => box.scrollIntoView({ block: 'start' }), 50);
    }
})();
