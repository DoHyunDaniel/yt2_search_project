/**
 * 애플리케이션 상수 정의
 */

// 검색 알고리즘 옵션
export const SEARCH_ALGORITHMS = [
  {
    value: 'basic',
    label: '기본 검색 (ILIKE)',
    description: '단순 텍스트 매칭으로 빠른 검색',
    icon: '🔍',
    color: '#667eea'
  },
  {
    value: 'tfidf',
    label: 'TF-IDF 검색',
    description: '단어 중요도 기반 의미적 검색',
    icon: '🧮',
    color: '#764ba2'
  },
  {
    value: 'weighted',
    label: '가중치 검색',
    description: '제목, 태그, 설명에 다른 가중치 적용',
    icon: '⚖️',
    color: '#f093fb'
  },
  {
    value: 'bm25',
    label: 'BM25 검색',
    description: 'OpenSearch 전문 검색 엔진',
    icon: '🔍',
    color: '#4facfe'
  },
  {
    value: 'hybrid',
    label: '하이브리드 검색',
    description: 'TF-IDF와 BM25를 결합한 고급 검색',
    icon: '🔗',
    color: '#43e97b'
  },
  {
    value: 'semantic',
    label: '의미 기반 검색',
    description: '임베딩 유사도 기반 의미적 검색',
    icon: '🧠',
    color: '#fa709a'
  },
  {
    value: 'sentiment',
    label: '감정 분석 검색',
    description: '댓글 감정 점수를 고려한 검색',
    icon: '😊',
    color: '#ffecd2'
  }
];

// 페이지네이션 설정
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 5,
  MAX_PAGE_SIZE: 20,
  MAX_VISIBLE_PAGES: 5
};

// 검색 설정
export const SEARCH_CONFIG = {
  MIN_QUERY_LENGTH: 1,
  MAX_QUERY_LENGTH: 100,
  DEBOUNCE_DELAY: 300,
  CACHE_DURATION: 5 * 60 * 1000 // 5분
};

// API 설정
export const API_CONFIG = {
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
};

// 애니메이션 설정
export const ANIMATION = {
  DURATION: 300,
  EASING: 'cubic-bezier(0.4, 0, 0.2, 1)'
};

// 반응형 브레이크포인트
export const BREAKPOINTS = {
  mobile: '768px',
  tablet: '1024px',
  desktop: '1200px'
};

// 테마 색상
export const THEME_COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#43e97b',
  warning: '#f093fb',
  error: '#ff6b6b',
  info: '#4facfe',
  background: '#f8f9fa',
  surface: '#ffffff',
  text: {
    primary: '#333333',
    secondary: '#666666',
    disabled: '#999999'
  }
};

// 로컬 스토리지 키
export const STORAGE_KEYS = {
  SEARCH_HISTORY: 'yt2_search_history',
  PREFERENCES: 'yt2_preferences',
  CACHE: 'yt2_cache'
};

// 에러 메시지
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '네트워크 연결을 확인해주세요.',
  SERVER_ERROR: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  NOT_FOUND: '검색 결과를 찾을 수 없습니다.',
  INVALID_QUERY: '검색어를 입력해주세요.',
  TIMEOUT: '요청 시간이 초과되었습니다.',
  UNKNOWN: '알 수 없는 오류가 발생했습니다.'
};
