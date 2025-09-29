/**
 * 숫자 포맷팅 유틸리티
 */

/**
 * 숫자를 한국식 표기법으로 포맷팅
 * @param {number} num - 포맷팅할 숫자
 * @returns {string} 포맷팅된 문자열
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined || isNaN(num)) {
    return '0';
  }
  
  if (num >= 100000000) {
    return (num / 100000000).toFixed(1) + '억';
  } else if (num >= 10000) {
    return (num / 10000).toFixed(1) + '만';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  
  return num.toLocaleString('ko-KR');
};

/**
 * 날짜를 한국식 표기법으로 포맷팅
 * @param {string|Date} date - 포맷팅할 날짜
 * @returns {string} 포맷팅된 날짜 문자열
 */
export const formatDate = (date) => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return '';
  }
  
  const now = new Date();
  const diffTime = now - dateObj;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return '오늘';
  } else if (diffDays === 1) {
    return '어제';
  } else if (diffDays < 7) {
    return `${diffDays}일 전`;
  } else if (diffDays < 30) {
    return `${Math.floor(diffDays / 7)}주 전`;
  } else if (diffDays < 365) {
    return `${Math.floor(diffDays / 30)}개월 전`;
  } else {
    return `${Math.floor(diffDays / 365)}년 전`;
  }
};

/**
 * 텍스트를 지정된 길이로 자르고 말줄임표 추가
 * @param {string} text - 자를 텍스트
 * @param {number} maxLength - 최대 길이
 * @returns {string} 잘린 텍스트
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * YouTube 썸네일 URL 생성
 * @param {string} videoId - YouTube 비디오 ID
 * @param {string} quality - 썸네일 품질 (maxresdefault, hqdefault, mqdefault, default)
 * @returns {string} 썸네일 URL
 */
export const getYouTubeThumbnail = (videoId, quality = 'maxresdefault') => {
  if (!videoId) return '';
  return `https://img.youtube.com/vi/${videoId}/${quality}.jpg`;
};

/**
 * YouTube 비디오 URL 생성
 * @param {string} videoId - YouTube 비디오 ID
 * @returns {string} YouTube 비디오 URL
 */
export const getYouTubeUrl = (videoId) => {
  if (!videoId) return '';
  return `https://www.youtube.com/watch?v=${videoId}`;
};

/**
 * 검색 시간을 포맷팅
 * @param {number} seconds - 검색 시간 (초)
 * @returns {string} 포맷팅된 시간
 */
export const formatSearchTime = (seconds) => {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  } else if (seconds < 60) {
    return `${seconds.toFixed(2)}초`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}분 ${remainingSeconds.toFixed(1)}초`;
  }
};
