import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { THEME_COLORS, ANIMATION, PAGINATION } from '../utils/constants';

const PaginationContainer = styled(motion.div)`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 40px;
  padding: 20px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e5e9;

  @media (max-width: 768px) {
    gap: 5px;
    padding: 15px;
  }
`;

const PageButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 45px;
  height: 45px;
  padding: 0 15px;
  border: 2px solid ${props => props.active ? THEME_COLORS.primary : '#e1e5e9'};
  border-radius: 10px;
  background: ${props => props.active ? THEME_COLORS.primary : 'white'};
  color: ${props => props.active ? 'white' : THEME_COLORS.text.primary};
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};
  box-shadow: ${props => props.active ? '0 4px 15px rgba(102, 126, 234, 0.3)' : '0 2px 5px rgba(0, 0, 0, 0.05)'};

  &:hover:not(:disabled) {
    border-color: ${THEME_COLORS.primary};
    background: ${props => props.active ? THEME_COLORS.primary : '#f8f9fa'};
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    background: #f8f9fa;
    color: #ccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  @media (max-width: 768px) {
    min-width: 40px;
    height: 40px;
    padding: 0 10px;
    font-size: 0.9rem;
  }
`;

const Ellipsis = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 45px;
  height: 45px;
  color: ${THEME_COLORS.text.secondary};
  font-size: 1rem;
  font-weight: 600;

  @media (max-width: 768px) {
    min-width: 40px;
    height: 40px;
    font-size: 0.9rem;
  }
`;

const PageInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 0 20px;
  color: ${THEME_COLORS.text.secondary};
  font-size: 0.9rem;
  font-weight: 500;

  @media (max-width: 768px) {
    margin: 0 10px;
    font-size: 0.8rem;
  }
`;

const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  loading = false 
}) => {
  if (totalPages <= 1) {
    return null;
  }

  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxVisible = PAGINATION.MAX_VISIBLE_PAGES;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }

    return pageNumbers;
  };

  const pageNumbers = getPageNumbers();
  const showStartEllipsis = pageNumbers[0] > 1;
  const showEndEllipsis = pageNumbers[pageNumbers.length - 1] < totalPages;

  return (
    <PaginationContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <PageButton
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1 || loading}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <FaChevronLeft />
      </PageButton>

      {showStartEllipsis && (
        <>
          <PageButton
            onClick={() => onPageChange(1)}
            disabled={loading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            1
          </PageButton>
          <Ellipsis>...</Ellipsis>
        </>
      )}

      {pageNumbers.map((pageNumber) => (
        <PageButton
          key={pageNumber}
          onClick={() => onPageChange(pageNumber)}
          active={pageNumber === currentPage}
          disabled={loading}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {pageNumber}
        </PageButton>
      ))}

      {showEndEllipsis && (
        <>
          <Ellipsis>...</Ellipsis>
          <PageButton
            onClick={() => onPageChange(totalPages)}
            disabled={loading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {totalPages}
          </PageButton>
        </>
      )}

      <PageButton
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages || loading}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <FaChevronRight />
      </PageButton>

      <PageInfo>
        {currentPage} / {totalPages}
      </PageInfo>
    </PaginationContainer>
  );
};

export default Pagination;
