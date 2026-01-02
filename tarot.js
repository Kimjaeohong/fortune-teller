// 타로 애플리케이션 상태
let selectedSpread = 1; // 카드 장수
let spreadType = 'single'; // 스프레드 타입
let selectedCards = [];
let drawnResults = [];

// 스프레드 포지션 정의
const SPREAD_POSITIONS = {
    'single': ['현재 상황'],
    'past-present-future': ['과거', '현재', '미래'],
    'love': ['나의 마음', '상대방의 마음', '관계의 미래'],
    'choice': ['A 선택의 결과', 'B 선택의 결과', '조언'],
    'work': ['현재 직업 상황', '극복해야 할 장애물', '조언', '최종 결과'],
    'money': ['현재 재정 상황', '들어올 기회', '재물 증대 조언'],
    'study': ['현재 학업 상태', '극복 포인트', '시험/학업 결과'],
    'year': ['사랑/관계운', '직업/경력운', '재물/금전운', '건강운', '올해의 조언']
};

// DOM 요소
const spreadBtns = document.querySelectorAll('.spread-btn');
const cardDeck = document.getElementById('card-deck');
const drawBtn = document.getElementById('draw-btn');
const results = document.getElementById('results');
const resultCards = document.getElementById('result-cards');
const shareBtn = document.getElementById('share-btn');
const resetBtn = document.getElementById('reset-btn');

// 스프레드 선택
spreadBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        spreadBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedSpread = parseInt(btn.dataset.spread);
        spreadType = btn.dataset.type;
        resetGame();
    });
});

// 게임 초기화
function resetGame() {
    selectedCards = [];
    drawnResults = [];
    results.classList.remove('show');
    drawBtn.style.display = 'none';
    createCardDeck();
}

// 카드 덱 생성
function createCardDeck() {
    cardDeck.innerHTML = '';
    
    // 22장의 뒷면 카드 생성 (충분한 선택지)
    for (let i = 0; i < 22; i++) {
        const card = document.createElement('div');
        card.className = 'tarot-card';
        card.dataset.index = i;
        
        card.innerHTML = `
            <div class="card-back">🔮</div>
            <div class="card-front">
                <div class="emoji">?</div>
                <div class="name">?</div>
            </div>
        `;
        
        card.addEventListener('click', () => selectCard(card, i));
        cardDeck.appendChild(card);
    }
}

// 카드 선택
function selectCard(cardElement, index) {
    // 이미 선택된 카드면 무시
    if (selectedCards.includes(index)) return;
    
    // 선택 가능한 카드 수 체크
    if (selectedCards.length >= selectedSpread) return;
    
    // 카드 선택
    selectedCards.push(index);
    cardElement.classList.add('flipped');
    
    // 실제 타로 카드 랜덤 선택
    const randomCard = TAROT_CARDS[Math.floor(Math.random() * TAROT_CARDS.length)];
    const isReversed = Math.random() < 0.5; // 50% 역방향
    
    drawnResults.push({
        card: randomCard,
        reversed: isReversed
    });
    
    // 카드 앞면 업데이트
    setTimeout(() => {
        const emoji = cardElement.querySelector('.emoji');
        const name = cardElement.querySelector('.name');
        emoji.textContent = isReversed ? '🔄' : randomCard.emoji;
        name.textContent = randomCard.name;
    }, 300);
    
    // 모든 카드 선택 완료
    if (selectedCards.length === selectedSpread) {
        setTimeout(() => {
            drawBtn.style.display = 'block';
        }, 600);
    }
}

// 결과 펼치기
drawBtn.addEventListener('click', () => {
    showResults();
});

// 결과 표시
function showResults() {
    resultCards.innerHTML = '';
    
    const spreadPositions = SPREAD_POSITIONS[spreadType] || ['현재 상황'];
    
    drawnResults.forEach((result, index) => {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        resultCard.style.animationDelay = `${index * 0.2}s`;
        
        const meaning = result.reversed ? result.card.reversed : result.card.upright;
        const positionLabel = spreadPositions[index] || `카드 ${index + 1}`;
        
        resultCard.innerHTML = `
            <div class="result-header">
                <div class="result-emoji">${result.reversed ? '🔄' : result.card.emoji}</div>
                <div class="result-info">
                    <h2>
                        ${result.card.name}
                        ${result.reversed ? '<span class="reversed-indicator">역방향</span>' : ''}
                    </h2>
                    <p class="result-position">${positionLabel}</p>
                </div>
            </div>
            <div class="result-meaning">${meaning}</div>
        `;
        
        resultCards.appendChild(resultCard);
    });
    
    results.classList.add('show');
    
    // 결과로 스크롤
    setTimeout(() => {
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

// 카카오톡 공유
shareBtn.addEventListener('click', () => {
    if (!Kakao.isInitialized()) {
        alert('카카오톡 SDK 초기화 실패');
        return;
    }
    
    // 스프레드 타입별 제목
    const spreadTitles = {
        'single': '오늘의 타로',
        'past-present-future': '과거·현재·미래 타로',
        'love': '연애운 타로',
        'choice': '양자택일 타로',
        'work': '직업운 타로',
        'money': '재물운 타로',
        'study': '학업운 타로',
        'year': '올해의 운세 타로'
    };
    
    // 결과 요약 생성
    let summary = '';
    const spreadPositions = SPREAD_POSITIONS[spreadType] || ['현재 상황'];
    
    drawnResults.forEach((result, index) => {
        const position = spreadPositions[index] || `${index + 1}번째`;
        const direction = result.reversed ? '역방향' : '정방향';
        summary += `${position}: ${result.card.name}(${direction})\n`;
    });
    
    const title = spreadTitles[spreadType] || '오늘의 타로';
    
    try {
        Kakao.Share.sendDefault({
            objectType: 'feed',
            content: {
                title: `🔮 ${title} 결과`,
                description: summary.trim(),
                imageUrl: 'https://raw.githubusercontent.com/Kimjaeohong/fortune-teller/main/fortune-image.png?v=' + Date.now(),
                link: {
                    mobileWebUrl: 'https://fortune.hongspot.com/tarot.html',
                    webUrl: 'https://fortune.hongspot.com/tarot.html',
                },
            },
            buttons: [
                {
                    title: '나도 타로 보기',
                    link: {
                        mobileWebUrl: 'https://fortune.hongspot.com/tarot.html',
                        webUrl: 'https://fortune.hongspot.com/tarot.html',
                    },
                },
            ],
        });
    } catch (error) {
        console.error('카카오톡 공유 오류:', error);
        alert('카카오톡 공유 중 오류가 발생했습니다: ' + error.message);
    }
});

// 다시하기
resetBtn.addEventListener('click', () => {
    resetGame();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 초기 카드 덱 생성
createCardDeck();
