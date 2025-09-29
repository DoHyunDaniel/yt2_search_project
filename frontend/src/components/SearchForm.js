import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaSearch, FaCog } from 'react-icons/fa';
import { SEARCH_ALGORITHMS, THEME_COLORS, ANIMATION } from '../utils/constants';

const SearchFormContainer = styled(motion.form)`
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
  align-items: flex-end;
  padding: 30px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 15px;
    padding: 20px;
  }
`;

const SearchInputContainer = styled.div`
  display: flex;
  gap: 15px;
  flex: 1;
  min-width: 300px;
  position: relative;

  @media (max-width: 768px) {
    min-width: 100%;
  }
`;

const SearchInput = styled.input`
  flex: 1;
  padding: 18px 20px 18px 50px;
  border: 2px solid #e1e5e9;
  border-radius: 15px;
  font-size: 1.1rem;
  outline: none;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);

  &:focus {
    border-color: ${THEME_COLORS.primary};
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    transform: translateY(-2px);
  }

  &:disabled {
    background: #f8f9fa;
    cursor: not-allowed;
  }

  &::placeholder {
    color: #999;
  }
`;

const SearchIcon = styled(FaSearch)`
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 1.2rem;
  pointer-events: none;
  z-index: 1;
`;

const SearchButton = styled(motion.button)`
  padding: 18px 30px;
  background: linear-gradient(135deg, ${THEME_COLORS.primary} 0%, ${THEME_COLORS.secondary} 100%);
  color: white;
  border: none;
  border-radius: 15px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  @media (max-width: 768px) {
    width: 100%;
    justify-content: center;
  }
`;

const AlgorithmSelector = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 280px;
  background: white;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e5e9;

  @media (max-width: 768px) {
    min-width: 100%;
  }
`;

const AlgorithmLabel = styled.label`
  font-size: 0.9rem;
  font-weight: 600;
  color: ${THEME_COLORS.text.primary};
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const AlgorithmSelect = styled.select`
  padding: 15px;
  border: 2px solid #e1e5e9;
  border-radius: 10px;
  font-size: 1rem;
  background: white;
  outline: none;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);

  &:focus {
    border-color: ${THEME_COLORS.primary};
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  &:hover {
    border-color: ${THEME_COLORS.primary};
  }

  &:disabled {
    background: #f8f9fa;
    cursor: not-allowed;
  }
`;

const AlgorithmOption = styled.option`
  padding: 10px;
`;

const SearchForm = ({ 
  query, 
  setQuery, 
  selectedAlgorithm, 
  onAlgorithmChange, 
  onSearch, 
  loading 
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <SearchFormContainer
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <SearchInputContainer>
        <SearchIcon />
        <SearchInput
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="행궁 관련 검색어를 입력하세요..."
          disabled={loading}
          maxLength={100}
        />
        <SearchButton
          type="submit"
          disabled={loading || !query.trim()}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <FaSearch />
          {loading ? '검색 중...' : '검색'}
        </SearchButton>
      </SearchInputContainer>
      
      <AlgorithmSelector>
        <AlgorithmLabel>
          <FaCog />
          검색 알고리즘
        </AlgorithmLabel>
        <AlgorithmSelect
          value={selectedAlgorithm}
          onChange={(e) => onAlgorithmChange(e.target.value)}
          disabled={loading}
        >
          {SEARCH_ALGORITHMS.map((algo) => (
            <AlgorithmOption key={algo.value} value={algo.value}>
              {algo.icon} {algo.label}
            </AlgorithmOption>
          ))}
        </AlgorithmSelect>
      </AlgorithmSelector>
    </SearchFormContainer>
  );
};

export default SearchForm;
