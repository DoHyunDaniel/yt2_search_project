import { useState, useCallback, useRef, useEffect } from 'react';
import { searchVideos } from '../services/api';
import { SEARCH_CONFIG, ERROR_MESSAGES } from '../utils/constants';

/**
 * 검색 기능을 위한 커스텀 훅
 */
export const useSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalResults, setTotalResults] = useState(0);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('basic');
  const [searchTime, setSearchTime] = useState(0);
  
  const abortControllerRef = useRef(null);
  const cacheRef = useRef(new Map());

  // 검색 실행
  const executeSearch = useCallback(async (searchQuery, algorithm, page = 1) => {
    if (!searchQuery.trim()) {
      setError(ERROR_MESSAGES.INVALID_QUERY);
      return;
    }

    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 새로운 AbortController 생성
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError('');

    try {
      const startTime = performance.now();
      
      // 캐시 확인
      const cacheKey = `${searchQuery}-${algorithm}-${page}`;
      const cachedResult = cacheRef.current.get(cacheKey);
      
      if (cachedResult && Date.now() - cachedResult.timestamp < SEARCH_CONFIG.CACHE_DURATION) {
        setResults(cachedResult.data.videos);
        setTotalPages(cachedResult.data.total_pages);
        setTotalResults(cachedResult.data.total_count);
        setSearchTime(cachedResult.data.search_time);
        setCurrentPage(page);
        setLoading(false);
        return;
      }

      const response = await searchVideos({
        q: searchQuery,
        page,
        limit: 5,
        algorithm
      });

      const endTime = performance.now();
      const searchTimeMs = (endTime - startTime) / 1000;

      // 결과 설정
      setResults(response.videos || []);
      setTotalPages(response.total_pages || 0);
      setTotalResults(response.total_count || 0);
      setSearchTime(response.search_time || searchTimeMs);
      setCurrentPage(page);

      // 캐시에 저장
      cacheRef.current.set(cacheKey, {
        data: response,
        timestamp: Date.now()
      });

    } catch (err) {
      if (err.name === 'AbortError') {
        return; // 요청이 취소된 경우
      }
      
      console.error('Search error:', err);
      setError(err.message || ERROR_MESSAGES.UNKNOWN);
      setResults([]);
      setTotalPages(0);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // 검색 실행 (디바운싱)
  const search = useCallback((searchQuery, algorithm, page = 1) => {
    if (searchQuery.length < SEARCH_CONFIG.MIN_QUERY_LENGTH) {
      setResults([]);
      setTotalPages(0);
      setTotalResults(0);
      setError('');
      return;
    }

    executeSearch(searchQuery, algorithm, page);
  }, [executeSearch]);

  // 페이지 변경
  const changePage = useCallback((page) => {
    if (page < 1 || page > totalPages || loading) return;
    search(query, selectedAlgorithm, page);
  }, [query, selectedAlgorithm, totalPages, loading, search]);

  // 알고리즘 변경
  const changeAlgorithm = useCallback((algorithm) => {
    setSelectedAlgorithm(algorithm);
    if (query.trim()) {
      search(query, algorithm, 1);
    }
  }, [query, search]);

  // 쿼리 변경
  const changeQuery = useCallback((newQuery) => {
    setQuery(newQuery);
    if (newQuery.trim()) {
      search(newQuery, selectedAlgorithm, 1);
    } else {
      setResults([]);
      setTotalPages(0);
      setTotalResults(0);
      setError('');
    }
  }, [selectedAlgorithm, search]);

  // 컴포넌트 언마운트 시 요청 취소
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // 캐시 정리 (5분마다)
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      for (const [key, value] of cacheRef.current.entries()) {
        if (now - value.timestamp > SEARCH_CONFIG.CACHE_DURATION) {
          cacheRef.current.delete(key);
        }
      }
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    // 상태
    query,
    results,
    loading,
    error,
    currentPage,
    totalPages,
    totalResults,
    selectedAlgorithm,
    searchTime,
    
    // 액션
    search,
    changePage,
    changeAlgorithm,
    changeQuery,
    setQuery,
    clearError: () => setError('')
  };
};
