// ─────────────────────────────────────────────
//  사이트 설정
//  스프레드시트는 "링크가 있는 모든 사용자 - 뷰어"로 공유되어 있어야 합니다.
// ─────────────────────────────────────────────
const CONFIG = {
    SPREADSHEET_ID: '1Jav7oWd9bMwV3TmY0R3Hhxus7O_gGXOqiHd81TC5h6A',
    SHEET_NAME: 'fortune_data',
    SITE_URL: 'https://fortune.hongspot.com',
    SHARE_IMAGE: 'https://fortune.hongspot.com/fortune-image.png',
    KAKAO_KEY: '27e9da30e66de45bc054ba884c3bd150',
    TIMEZONE: 'Asia/Seoul',
    FETCH_TIMEOUT_MS: 8000
};

// 12띠 (순서 = 자축인묘진사오미신유술해)
const ZODIAC_ORDER = ['rat', 'ox', 'tiger', 'rabbit', 'dragon', 'snake',
                      'horse', 'sheep', 'monkey', 'rooster', 'dog', 'pig'];

const ZODIAC_INFO = {
    rat:     { name: '쥐띠',     hanja: '子', animal: '쥐',     emoji: '🐭' },
    ox:      { name: '소띠',     hanja: '丑', animal: '소',     emoji: '🐮' },
    tiger:   { name: '호랑이띠', hanja: '寅', animal: '호랑이', emoji: '🐯' },
    rabbit:  { name: '토끼띠',   hanja: '卯', animal: '토끼',   emoji: '🐰' },
    dragon:  { name: '용띠',     hanja: '辰', animal: '용',     emoji: '🐲' },
    snake:   { name: '뱀띠',     hanja: '巳', animal: '뱀',     emoji: '🐍' },
    horse:   { name: '말띠',     hanja: '午', animal: '말',     emoji: '🐴' },
    sheep:   { name: '양띠',     hanja: '未', animal: '양',     emoji: '🐑' },
    monkey:  { name: '원숭이띠', hanja: '申', animal: '원숭이', emoji: '🐵' },
    rooster: { name: '닭띠',     hanja: '酉', animal: '닭',     emoji: '🐔' },
    dog:     { name: '개띠',     hanja: '戌', animal: '개',     emoji: '🐶' },
    pig:     { name: '돼지띠',   hanja: '亥', animal: '돼지',   emoji: '🐷' }
};

// 운세 카테고리 (시트의 category 값과 일치해야 함)
const FORTUNE_CATEGORIES = {
    overall:      { title: '종합운',      short: '종합' },
    money:        { title: '재물운',      short: '재물' },
    work:         { title: '일·학업운',   short: '일' },
    health:       { title: '건강운',      short: '건강' },
    relationship: { title: '인연·관계운', short: '인연' }
};

// ─────────────────────────────────────────────
//  별자리
// ─────────────────────────────────────────────
const STAR_ORDER = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'];

// from/to: [월, 일] — 경계일은 해마다 하루 정도 차이가 날 수 있음
// symbol 끝의 변형 선택자(U+FE0E)는 이모지가 아닌 글자 모양으로 표시하라는 뜻
const STAR_INFO = {
    aries:       { name: '양자리',     symbol: '♈︎', from: [3, 21],  to: [4, 19],  element: '불',   planet: '화성' },
    taurus:      { name: '황소자리',   symbol: '♉︎', from: [4, 20],  to: [5, 20],  element: '흙',   planet: '금성' },
    gemini:      { name: '쌍둥이자리', symbol: '♊︎', from: [5, 21],  to: [6, 21],  element: '공기', planet: '수성' },
    cancer:      { name: '게자리',     symbol: '♋︎', from: [6, 22],  to: [7, 22],  element: '물',   planet: '달' },
    leo:         { name: '사자자리',   symbol: '♌︎', from: [7, 23],  to: [8, 22],  element: '불',   planet: '태양' },
    virgo:       { name: '처녀자리',   symbol: '♍︎', from: [8, 23],  to: [9, 23],  element: '흙',   planet: '수성' },
    libra:       { name: '천칭자리',   symbol: '♎︎', from: [9, 24],  to: [10, 22], element: '공기', planet: '금성' },
    scorpio:     { name: '전갈자리',   symbol: '♏︎', from: [10, 23], to: [11, 22], element: '물',   planet: '명왕성' },
    sagittarius: { name: '사수자리',   symbol: '♐︎', from: [11, 23], to: [12, 24], element: '불',   planet: '목성' },
    capricorn:   { name: '염소자리',   symbol: '♑︎', from: [12, 25], to: [1, 19],  element: '흙',   planet: '토성' },
    aquarius:    { name: '물병자리',   symbol: '♒︎', from: [1, 20],  to: [2, 18],  element: '공기', planet: '천왕성' },
    pisces:      { name: '물고기자리', symbol: '♓︎', from: [2, 19],  to: [3, 20],  element: '물',   planet: '해왕성' }
};
