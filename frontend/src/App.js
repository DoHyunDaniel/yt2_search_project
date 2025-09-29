import React, { useState } from 'react';
import styled, { createGlobalStyle } from 'styled-components';
import { motion } from 'framer-motion';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { Toaster } from 'react-hot-toast';
import { FaGithub, FaInfoCircle, FaSearch, FaChartLine, FaBrain, FaHome } from 'react-icons/fa';

// Components
import SearchForm from './components/SearchForm';
import SearchResults from './components/SearchResults';
import Pagination from './components/Pagination';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';
import StatsDashboard from './components/StatsDashboard';
import RecommendationPage from './components/RecommendationPage';

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

  input, textarea, select {
    font-family: inherit;
  }
`;

// Styled Components
const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
`;

const Navigation = styled(motion.nav)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 15px 0;
  margin-bottom: 20px;
`;

const NavContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 20px;
`;

const NavLink = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'active',
})`
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.2)' : 'transparent'};
  border: 2px solid ${props => props.active ? 'rgba(255, 255, 255, 0.4)' : 'rgba(255, 255, 255, 0.2)'};
  color: white;
  padding: 10px 20px;
  border-radius: 25px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-2px);
  }
`;

const MainContent = styled.div`
  padding: 0 20px;
`;

const Header = styled(motion.div)`
  text-align: center;
  margin-bottom: 40px;
  position: relative;
`;

const Title = styled.h1`
  font-size: 3rem;
  color: white;
  margin-bottom: 10px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const Subtitle = styled.p`
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 20px;
  font-weight: 300;
`;

const Footer = styled.footer`
  text-align: center;
  margin-top: 60px;
  padding: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
`;

const FooterLink = styled.a`
  color: white;
  text-decoration: none;
  font-weight: 600;
  margin-left: 20px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.3s ease;

  &:hover {
    color: #ffd700;
    transform: translateY(-2px);
  }
`;

const InfoButton = styled.button`
  position: absolute;
  top: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
    transform: scale(1.1);
  }
`;

const ErrorMessage = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  color: #e74c3c;
  padding: 20px;
  border-radius: 12px;
  margin: 20px auto;
  max-width: 600px;
  text-align: center;
  font-weight: 500;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #e74c3c;
`;

const NoResultsMessage = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  color: #666;
  padding: 40px;
  border-radius: 12px;
  margin: 40px auto;
  max-width: 600px;
  text-align: center;
  font-size: 1.1rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
`;

// Modal Styles
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 20px;
  padding: 30px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
`;

const ModalCloseButton = styled.button`
  position: absolute;
  top: 15px;
  right: 20px;
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #999;
  transition: color 0.3s ease;

  &:hover {
    color: #333;
  }
`;

const ModalTitle = styled.h2`
  font-size: 1.8rem;
  margin-bottom: 20px;
  color: #333;
  text-align: center;
`;

const ModalBody = styled.div`
  line-height: 1.6;
  color: #666;
`;

const ModalSection = styled.div`
  margin-bottom: 25px;
`;

const ModalSectionTitle = styled.h3`
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: #333;
  font-weight: 600;
`;

const ModalSectionContent = styled.div`
  font-size: 0.95rem;
  line-height: 1.5;

  ul {
    margin: 10px 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 8px;
  }
`;

function App() {
  const [currentPage, setCurrentPage] = useState('search');
  const [showInfoModal, setShowInfoModal] = useState(false);

  const {
    query,
    setQuery,
    results,
    loading,
    error,
    currentPage: searchPage,
    totalPages,
    totalResults,
    selectedAlgorithm,
    searchTime,
    search,
    changePage,
    changeAlgorithm,
    changeQuery,
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

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'search':
        return (
          <>
            <Header
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <Title>행궁 검색</Title>
              <Subtitle>수원시 행궁동 관련 YouTube 영상을 검색해보세요</Subtitle>
              <InfoButton onClick={() => setShowInfoModal(true)}>
                <FaInfoCircle />
              </InfoButton>
            </Header>

            <ErrorBoundary>
              <SearchForm
                query={query}
                setQuery={changeQuery}
                selectedAlgorithm={selectedAlgorithm}
                onAlgorithmChange={handleAlgorithmChange}
                onSearch={handleSearch}
                loading={loading}
              />

              {error && <ErrorMessage>{error}</ErrorMessage>}

              {loading && <LoadingSpinner />}

              {!loading && results.length > 0 && (
                <>
                  <SearchResults
                    results={results}
                    totalResults={totalResults}
                    currentPage={searchPage}
                    selectedAlgorithm={selectedAlgorithm}
                  />
                  {totalPages > 1 && (
                    <Pagination
                      currentPage={searchPage}
                      totalPages={totalPages}
                      handlePageChange={handlePageChange}
                    />
                  )}
                </>
              )}

              {!loading && !error && results.length === 0 && query && totalResults === 0 && (
                <NoResultsMessage
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  "{query}"에 대한 검색 결과가 없습니다. 다른 검색어를 시도해보세요.
                </NoResultsMessage>
              )}
            </ErrorBoundary>
          </>
        );
      case 'stats':
        return <StatsDashboard />;
      case 'recommendations':
        return <RecommendationPage />;
      default:
        return null;
    }
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
        <Navigation
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <NavContainer>
            <Logo>
              <FaHome /> 행궁 검색
            </Logo>
            <NavLinks>
              <NavLink
                active={currentPage === 'search'}
                onClick={() => setCurrentPage('search')}
              >
                <FaSearch /> 검색
              </NavLink>
              <NavLink
                active={currentPage === 'stats'}
                onClick={() => setCurrentPage('stats')}
              >
                <FaChartLine /> 통계
              </NavLink>
              <NavLink
                active={currentPage === 'recommendations'}
                onClick={() => setCurrentPage('recommendations')}
              >
                <FaBrain /> AI 추천
              </NavLink>
            </NavLinks>
          </NavContainer>
        </Navigation>

        <MainContent>
          {renderCurrentPage()}
        </MainContent>

        <Footer>
          <p>&copy; {new Date().getFullYear()} YT2 Search System. All rights reserved.</p>
          <FooterLink href="https://github.com/DoHyunDaniel/yt2_search_project" target="_blank" rel="noopener noreferrer">
            <FaGithub /> GitHub
          </FooterLink>
        </Footer>

        {showInfoModal && (
          <ModalOverlay onClick={() => setShowInfoModal(false)}>
            <ModalContent onClick={(e) => e.stopPropagation()}>
              <ModalCloseButton onClick={() => setShowInfoModal(false)}>&times;</ModalCloseButton>
              <ModalTitle>YT2 Search System 정보</ModalTitle>
              <ModalBody>
                <ModalSection>
                  <ModalSectionTitle>프로젝트 개요</ModalSectionTitle>
                  <ModalSectionContent>
                    이 프로젝트는 수원시 행궁동 관련 YouTube 데이터를 수집하고, 7가지 다양한 검색 알고리즘을 통해 사용자에게 가장 관련성 높은 결과를 제공하는 시스템입니다.
                  </ModalSectionContent>
                </ModalSection>
                <ModalSection>
                  <ModalSectionTitle>구현된 검색 알고리즘</ModalSectionTitle>
                  <ModalSectionContent>
                    <ul>
                      <li><strong>기본 검색</strong>: ILIKE를 사용한 단순 텍스트 매칭</li>
                      <li><strong>TF-IDF 검색</strong>: Term Frequency-Inverse Document Frequency 기반 가중치 검색</li>
                      <li><strong>가중치 검색</strong>: 필드별 가중치를 적용한 검색</li>
                      <li><strong>BM25 검색</strong>: OpenSearch의 BM25 알고리즘 활용</li>
                      <li><strong>하이브리드 검색</strong>: TF-IDF와 BM25를 결합한 앙상블 검색</li>
                      <li><strong>의미 기반 검색</strong>: 임베딩 벡터를 이용한 의미적 유사도 검색</li>
                      <li><strong>감정 분석 검색</strong>: 댓글의 감정 점수를 고려한 검색</li>
                    </ul>
                  </ModalSectionContent>
                </ModalSection>
                <ModalSection>
                  <ModalSectionTitle>기술 스택</ModalSectionTitle>
                  <ModalSectionContent>
                    <strong>프론트엔드</strong>: React 18, Styled Components, Framer Motion <br />
                    <strong>백엔드</strong>: Python 3.11, FastAPI, PostgreSQL, OpenSearch, Redis <br />
                    <strong>인프라</strong>: Docker, Docker Compose, Nginx
                  </ModalSectionContent>
                </ModalSection>
              </ModalBody>
            </ModalContent>
          </ModalOverlay>
        )}
      </AppContainer>

      <Toaster
        position="top-center"
        reverseOrder={false}
        gutter={8}
        containerClassName=""
        containerStyle={{}}
        toastOptions={{
          className: '',
          duration: 5000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            theme: {
              primary: 'green',
              secondary: 'black',
            },
          },
          error: {
            duration: 5000,
            theme: {
              primary: 'red',
              secondary: 'black',
            },
          },
        }}
      />
    </HelmetProvider>
  );
}

export default App;