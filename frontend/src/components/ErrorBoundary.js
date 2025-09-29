import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaExclamationTriangle, FaRedo } from 'react-icons/fa';
import { THEME_COLORS, ANIMATION } from '../utils/constants';

const ErrorContainer = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px 20px;
  text-align: center;
  background: white;
  border-radius: 20px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  margin: 20px 0;
`;

const ErrorIcon = styled.div`
  font-size: 4rem;
  color: ${THEME_COLORS.error};
  margin-bottom: 20px;
`;

const ErrorTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  color: ${THEME_COLORS.text.primary};
  margin: 0 0 15px 0;
`;

const ErrorMessage = styled.p`
  font-size: 1rem;
  color: ${THEME_COLORS.text.secondary};
  margin: 0 0 30px 0;
  line-height: 1.5;
  max-width: 500px;
`;

const RetryButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 30px;
  background: linear-gradient(135deg, ${THEME_COLORS.primary} 0%, ${THEME_COLORS.secondary} 100%);
  color: white;
  border: none;
  border-radius: 15px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  }

  &:active {
    transform: translateY(0);
  }
`;

const ErrorDetails = styled.details`
  margin-top: 20px;
  text-align: left;
  max-width: 600px;
  width: 100%;
`;

const ErrorSummary = styled.summary`
  cursor: pointer;
  font-weight: 600;
  color: ${THEME_COLORS.text.primary};
  margin-bottom: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
`;

const ErrorCode = styled.pre`
  background: #f8f9fa;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 15px;
  font-size: 0.9rem;
  color: ${THEME_COLORS.text.secondary};
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
`;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // 에러 로깅 (실제 프로덕션에서는 에러 리포팅 서비스 사용)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ErrorContainer
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <ErrorIcon>
            <FaExclamationTriangle />
          </ErrorIcon>
          
          <ErrorTitle>앗! 문제가 발생했습니다</ErrorTitle>
          
          <ErrorMessage>
            예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.
          </ErrorMessage>
          
          <RetryButton
            onClick={this.handleRetry}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaRedo />
            다시 시도
          </RetryButton>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <ErrorDetails>
              <ErrorSummary>개발자 정보 (개발 환경에서만 표시)</ErrorSummary>
              <ErrorCode>
                {this.state.error.toString()}
                {this.state.errorInfo.componentStack}
              </ErrorCode>
            </ErrorDetails>
          )}
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
