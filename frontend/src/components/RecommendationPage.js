import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaBrain, FaFire, FaClock, FaSearch, FaPlay, FaExternalLinkAlt, FaThumbsUp, FaEye } from 'react-icons/fa';
import { api } from '../services/api';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 40px;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
`;

const Subtitle = styled.p`
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 30px;
`;

const TabContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 5px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
`;

const Tab = styled.button`
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: ${props => props.active ? 'white' : 'transparent'};
  color: ${props => props.active ? '#667eea' : '#666'};
  border-radius: 8px;
  font-weight: ${props => props.active ? '600' : '400'};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  &:hover {
    background: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.5)'};
  }
`;

const SearchContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  margin-bottom: 30px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 15px;
  transition: border-color 0.3s ease;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const SearchButton = styled.button`
  width: 100%;
  padding: 12px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const VideoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
  margin-bottom: 30px;
`;

const VideoCard = styled(motion.div)`
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #e0e0e0;

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  }
`;

const VideoThumbnail = styled.div`
  position: relative;
  width: 100%;
  height: 200px;
  background: #f0f0f0;
  overflow: hidden;
`;

const ThumbnailImg = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

// YouTube 썸네일 URL 생성 함수
const getYouTubeThumbnail = (videoId) => {
  if (!videoId) return null;
  return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
};

const PlayButton = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: translate(-50%, -50%) scale(1.1);
  }
`;

const VideoContent = styled.div`
  padding: 20px;
`;

const VideoTitle = styled.h3`
  font-size: 1.1rem;
  color: #333;
  margin-bottom: 10px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const VideoChannel = styled.div`
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 15px;
`;

const VideoStats = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 0.85rem;
  color: #888;
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
`;

const RecommendationReason = styled.div`
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  color: white;
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 15px;
  display: inline-block;
`;

const SimilarityScore = styled.div`
  background: #e8f4fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 15px;
  display: inline-block;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const ActionButton = styled.button`
  flex: 1;
  padding: 8px 12px;
  border: 2px solid #667eea;
  background: ${props => props.primary ? '#667eea' : 'white'};
  color: ${props => props.primary ? 'white' : '#667eea'};
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;

  &:hover {
    background: ${props => props.primary ? '#5a6fd8' : '#667eea'};
    color: white;
    transform: translateY(-2px);
  }
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.2rem;
  color: #666;
`;

const ErrorMessage = styled.div`
  background: #ffebee;
  color: #c62828;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
  text-align: center;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #666;
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.5;
`;

function RecommendationPage() {
  const [activeTab, setActiveTab] = useState('popularity');
  const [searchVideoId, setSearchVideoId] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const tabs = [
    { id: 'popularity', label: '인기도 기반', icon: FaFire },
    { id: 'trending', label: '최신 트렌드', icon: FaClock },
    { id: 'content', label: '콘텐츠 기반', icon: FaBrain }
  ];

  useEffect(() => {
    if (activeTab === 'popularity' || activeTab === 'trending') {
      fetchRecommendations();
    }
  }, [activeTab]);

  const fetchRecommendations = async (videoId = null) => {
    try {
      setLoading(true);
      setError(null);

      let endpoint = '';
      let params = { limit: 6 };

      switch (activeTab) {
        case 'popularity':
          endpoint = '/api/recommendations/popularity';
          break;
        case 'trending':
          endpoint = '/api/recommendations/trending';
          break;
        case 'content':
          if (!videoId) {
            setError('콘텐츠 기반 추천을 위해서는 YouTube 비디오 ID가 필요합니다.');
            return;
          }
          endpoint = '/api/recommendations/content-based-youtube';
          params.video_id = videoId;
          break;
        default:
          return;
      }

      const response = await api.get(endpoint, { params });
      setRecommendations(response.data);
    } catch (err) {
      // YouTube API 할당량 초과 오류 처리
      if (err.response?.status === 429) {
        setError('YouTube API 할당량이 초과되어 콘텐츠 기반 검색이 불가능합니다.');
      } else if (err.response?.status === 404) {
        setError('해당 YouTube 비디오를 찾을 수 없습니다. 올바른 비디오 ID를 입력해주세요.');
      } else if (err.response?.status === 500 && err.response?.data?.detail?.includes('YouTube API')) {
        setError('YouTube API 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
      } else {
        setError('추천 데이터를 불러오는데 실패했습니다.');
      }
      console.error('Recommendation fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (activeTab === 'content' && searchVideoId.trim()) {
      fetchRecommendations(searchVideoId.trim());
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const openYouTube = (videoId) => {
    window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
  };

  return (
    <PageContainer>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Header>
          <Title>
            <FaBrain /> AI 추천 시스템
          </Title>
          <Subtitle>
            다양한 알고리즘으로 맞춤형 영상을 추천받아보세요
          </Subtitle>
        </Header>

        <TabContainer>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <Tab
                key={tab.id}
                active={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon />
                {tab.label}
              </Tab>
            );
          })}
        </TabContainer>

        {activeTab === 'content' && (
          <SearchContainer>
            <SearchInput
              type="text"
              placeholder="YouTube 비디오 ID를 입력하세요 (예: dQw4w9WgXcQ)"
              value={searchVideoId}
              onChange={(e) => setSearchVideoId(e.target.value)}
            />
            <SearchButton onClick={handleSearch} disabled={loading}>
              <FaSearch /> 유사한 영상 찾기
            </SearchButton>
          </SearchContainer>
        )}

        {loading && (
          <LoadingSpinner>
            🤖 AI가 추천을 분석하는 중...
          </LoadingSpinner>
        )}

        {error && (
          <ErrorMessage>{error}</ErrorMessage>
        )}

        {!loading && !error && recommendations.length === 0 && (
          <EmptyState>
            <EmptyIcon>🎬</EmptyIcon>
            <h3>추천할 영상이 없습니다</h3>
            <p>다른 탭을 시도해보거나 검색어를 변경해보세요.</p>
          </EmptyState>
        )}

        {!loading && !error && recommendations.length > 0 && (
          <VideoGrid>
            {recommendations.map((video, index) => (
              <VideoCard
                key={video.video_id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
              >
                <VideoThumbnail>
                  <ThumbnailImg
                    src={getYouTubeThumbnail(video.video_id)}
                    alt={video.title}
                    onError={(e) => {
                      // 썸네일 로드 실패 시 기본 아이콘 표시
                      e.target.style.display = 'none';
                      const parent = e.target.parentElement;
                      const fallback = parent.querySelector('.thumbnail-fallback');
                      if (fallback) fallback.style.display = 'flex';
                    }}
                  />
                  <div 
                    className="thumbnail-fallback"
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      background: 'linear-gradient(45deg, #667eea, #764ba2)',
                      display: 'none',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '2rem',
                      position: 'absolute',
                      top: 0,
                      left: 0
                    }}
                  >
                    🎬
                  </div>
                  <PlayButton onClick={() => openYouTube(video.video_id)}>
                    <FaPlay />
                  </PlayButton>
                </VideoThumbnail>

                <VideoContent>
                  <VideoTitle>{video.title}</VideoTitle>
                  <VideoChannel>{video.channel_name}</VideoChannel>

                  <RecommendationReason>
                    {video.recommendation_reason}
                  </RecommendationReason>

                  <SimilarityScore>
                    유사도: {(video.similarity_score * 100).toFixed(1)}%
                  </SimilarityScore>

                  <VideoStats>
                    <StatItem>
                      <FaEye /> {formatNumber(video.view_count)}
                    </StatItem>
                    <StatItem>
                      <FaThumbsUp /> {formatNumber(video.like_count)}
                    </StatItem>
                  </VideoStats>

                  <ActionButtons>
                    <ActionButton onClick={() => openYouTube(video.video_id)}>
                      <FaPlay /> 재생
                    </ActionButton>
                    <ActionButton primary onClick={() => openYouTube(video.video_id)}>
                      <FaExternalLinkAlt /> YouTube
                    </ActionButton>
                  </ActionButtons>
                </VideoContent>
              </VideoCard>
            ))}
          </VideoGrid>
        )}
      </motion.div>
    </PageContainer>
  );
}

export default RecommendationPage;
