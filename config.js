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
