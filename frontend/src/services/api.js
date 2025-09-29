import axios from 'axios';

// API 기본 설정
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 요청 로깅 (개발 환경에서만)
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    // 응답 로깅 (개발 환경에서만)
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error);
    
    // 에러 타입별 처리
    if (error.response) {
      // 서버에서 응답을 받았지만 에러 상태
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          throw new Error(data.detail || '잘못된 요청입니다.');
        case 404:
          throw new Error('요청한 리소스를 찾을 수 없습니다.');
        case 500:
          throw new Error('서버 내부 오류가 발생했습니다.');
        default:
          throw new Error(data.detail || `서버 오류 (${status})`);
      }
    } else if (error.request) {
      // 요청이 전송되었지만 응답을 받지 못함
      throw new Error('네트워크 연결을 확인해주세요.');
    } else {
      // 요청 설정 중 오류 발생
      throw new Error('요청 처리 중 오류가 발생했습니다.');
    }
  }
);

// API 엔드포인트
export const apiEndpoints = {
  search: '/api/search',
  health: '/health',
  stats: '/api/stats',
};

// 검색 API
export const searchVideos = async (params) => {
  try {
    const response = await apiClient.get(apiEndpoints.search, { params });
    return response.data;
  } catch (error) {
    console.error('Search API Error:', error);
    throw error;
  }
};

// 헬스 체크 API
export const checkHealth = async () => {
  try {
    const response = await apiClient.get(apiEndpoints.health);
    return response.data;
  } catch (error) {
    console.error('Health Check Error:', error);
    throw error;
  }
};

// 통계 API
export const getStats = async () => {
  try {
    const response = await apiClient.get(apiEndpoints.stats);
    return response.data;
  } catch (error) {
    console.error('Stats API Error:', error);
    throw error;
  }
};

export default apiClient;
