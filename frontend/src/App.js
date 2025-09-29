import React from 'react';
import styled, { createGlobalStyle } from 'styled-components';
import { motion } from 'framer-motion';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { Toaster } from 'react-hot-toast';
import { FaGithub, FaInfoCircle } from 'react-icons/fa';

// Components
import SearchForm from './components/SearchForm';
import SearchResults from './components/SearchResults';
import Pagination from './components/Pagination';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

// Hooks
import { useSearch } from './hooks/useSearch';

// Utils
import { THEME_COLORS, ANIMATION } from './utils/constants';

// Global Styles
const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: ${THEME_COLORS.text.primary};
  }

  code {
    font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
      monospace;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  button {
    font-family: inherit;
  }

  input, select, textarea {
    font-family: inherit;
  }
`;

const AppContainer = styled.div`
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow-x: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.05)"/><circle cx="10" cy="60" r="0.5" fill="rgba(255,255,255,0.05)"/><circle cx="90" cy="40" r="0.5" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    opacity: 0.3;
    pointer-events: none;
  }
`;

const Header = styled(motion.header)`
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
`;

const Title = styled(motion.h1)`
  font-size: 3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 15px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }

  @media (max-width: 480px) {
    font-size: 2rem;
  }
`;

const Subtitle = styled(motion.p)`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 20px;
  font-weight: 400;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);

  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

const InfoSection = styled(motion.div)`
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
  }
`;

const InfoCard = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 25px;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);

  @media (max-width: 768px) {
    font-size: 0.8rem;
    padding: 10px 16px;
  }
`;

const MainContent = styled(motion.main)`
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
`;

const ErrorMessage = styled(motion.div)`
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: white;
  padding: 20px;
  border-radius: 15px;
  margin-bottom: 30px;
  text-align: center;
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const Footer = styled(motion.footer)`
  text-align: center;
  margin-top: 60px;
  padding: 30px 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  position: relative;
  z-index: 1;
`;

const FooterLink = styled.a`
  color: white;
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};
  border: 1px solid rgba(255, 255, 255, 0.2);

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  }
`;

function App() {
  const {
    query,
    setQuery,
    results,
    loading,
    error,
    currentPage,
    totalPages,
    totalResults,
    selectedAlgorithm,
    searchTime,
    search,
    changePage,
    changeAlgorithm,
    clearError
  } = useSearch();

  const handleSearch = () => {
    if (query.trim()) {
      search(query, selectedAlgorithm, 1);
    }
  };

  const handleAlgorithmChange = (algorithm) => {
    changeAlgorithm(algorithm);
  };

  const handlePageChange = (page) => {
    changePage(page);
  };

  return (
    <HelmetProvider>
      <Helmet>
        <title>행궁 검색 - 수원시 행궁동 YouTube 데이터 검색</title>
        <meta name="description" content="수원시 행궁동 관련 YouTube 영상을 다양한 검색 알고리즘으로 검색해보세요. 기본 검색, TF-IDF, BM25, 하이브리드 검색 등 7가지 알고리즘을 지원합니다." />
        <meta name="keywords" content="수원, 행궁, YouTube, 검색, 알고리즘, TF-IDF, BM25" />
        <meta property="og:title" content="행궁 검색 - 수원시 행궁동 YouTube 데이터 검색" />
        <meta property="og:description" content="수원시 행궁동 관련 YouTube 영상을 다양한 검색 알고리즘으로 검색해보세요." />
        <meta property="og:type" content="website" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Helmet>

      <GlobalStyle />
      
      <AppContainer>
        <Header
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <Title
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            🔍 행궁 검색
          </Title>
          <Subtitle
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            수원시 행궁동 관련 YouTube 영상을 다양한 알고리즘으로 검색해보세요
          </Subtitle>
          
          <InfoSection
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <InfoCard>
              <FaInfoCircle />
              7가지 검색 알고리즘
            </InfoCard>
            <InfoCard>
              <FaGithub />
              실시간 검색 결과
            </InfoCard>
          </InfoSection>
        </Header>

        <MainContent
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <ErrorBoundary>
            <SearchForm
              query={query}
              setQuery={setQuery}
              selectedAlgorithm={selectedAlgorithm}
              onAlgorithmChange={handleAlgorithmChange}
              onSearch={handleSearch}
              loading={loading}
            />

            {error && (
              <ErrorMessage
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                {error}
                <button 
                  onClick={clearError}
                  style={{ 
                    marginLeft: '15px', 
                    background: 'none', 
                    border: 'none', 
                    color: 'white', 
                    cursor: 'pointer',
                    fontSize: '1.2rem'
                  }}
                >
                  ×
                </button>
              </ErrorMessage>
            )}

            {loading ? (
              <LoadingSpinner 
                message="검색 중..." 
                variant="skeleton"
              />
            ) : (
              <>
                <SearchResults
                  results={results}
                  loading={loading}
                  totalResults={totalResults}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  selectedAlgorithm={selectedAlgorithm}
                  searchTime={searchTime}
                />
                
                {totalPages > 1 && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    loading={loading}
                  />
                )}
              </>
            )}
          </ErrorBoundary>
        </MainContent>

        <Footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.2 }}
        >
          <p>© 2024 행궁 검색. 수원시 행궁동 YouTube 데이터 검색 서비스</p>
          <div style={{ marginTop: '15px' }}>
            <FooterLink href="https://github.com" target="_blank" rel="noopener noreferrer">
              <FaGithub />
              GitHub
            </FooterLink>
          </div>
        </Footer>
      </AppContainer>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
            borderRadius: '10px',
            padding: '16px',
            fontSize: '14px',
            fontWeight: '500',
          },
          success: {
            iconTheme: {
              primary: '#43e97b',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ff6b6b',
              secondary: '#fff',
            },
          },
        }}
      />
    </HelmetProvider>
  );
}

export default App;