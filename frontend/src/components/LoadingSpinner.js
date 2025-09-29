import React from 'react';
import styled, { keyframes } from 'styled-components';
import { motion } from 'framer-motion';
import { THEME_COLORS } from '../utils/constants';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`;

const LoadingContainer = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
`;

const Spinner = styled.div`
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid ${THEME_COLORS.primary};
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
  margin-bottom: 20px;
`;

const LoadingText = styled.div`
  font-size: 1.1rem;
  color: ${THEME_COLORS.text.secondary};
  font-weight: 500;
  animation: ${pulse} 1.5s ease-in-out infinite;
`;

const LoadingDots = styled.div`
  display: flex;
  gap: 4px;
  margin-top: 10px;
`;

const Dot = styled.div`
  width: 8px;
  height: 8px;
  background: ${THEME_COLORS.primary};
  border-radius: 50%;
  animation: ${pulse} 1.5s ease-in-out infinite;
  animation-delay: ${props => props.delay}s;
`;

const SkeletonCard = styled(motion.div)`
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  margin-bottom: 25px;
`;

const SkeletonLine = styled.div`
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: ${spin} 1.5s linear infinite;
  border-radius: 10px;
  margin-bottom: 15px;
`;

const SkeletonThumbnail = styled.div`
  width: 100%;
  height: 200px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: ${spin} 1.5s linear infinite;
  border-radius: 15px;
  margin-bottom: 20px;
`;

const LoadingSpinner = ({ 
  message = '로딩 중...', 
  showDots = true, 
  variant = 'spinner' 
}) => {
  if (variant === 'skeleton') {
    return (
      <LoadingContainer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {[...Array(3)].map((_, index) => (
          <SkeletonCard
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <SkeletonThumbnail />
            <SkeletonLine style={{ width: '80%' }} />
            <SkeletonLine style={{ width: '60%' }} />
            <SkeletonLine style={{ width: '40%' }} />
          </SkeletonCard>
        ))}
      </LoadingContainer>
    );
  }

  return (
    <LoadingContainer
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Spinner />
      <LoadingText>{message}</LoadingText>
      {showDots && (
        <LoadingDots>
          <Dot delay={0} />
          <Dot delay={0.2} />
          <Dot delay={0.4} />
        </LoadingDots>
      )}
    </LoadingContainer>
  );
};

export default LoadingSpinner;
