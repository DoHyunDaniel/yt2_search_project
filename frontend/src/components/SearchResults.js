import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaYoutube, FaEye, FaThumbsUp, FaComment, FaCalendarAlt } from 'react-icons/fa';
import { formatNumber, formatDate, truncateText, getYouTubeThumbnail, getYouTubeUrl } from '../utils/formatters';
import { SEARCH_ALGORITHMS, THEME_COLORS, ANIMATION } from '../utils/constants';

const ResultsContainer = styled(motion.div)`
  margin-top: 30px;
`;

const ResultsHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e5e9;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
`;

const ResultsCount = styled.div`
  font-size: 1.1rem;
  color: ${THEME_COLORS.text.secondary};
  font-weight: 500;
`;

const AlgorithmInfo = styled.div`
  background: linear-gradient(135deg, ${THEME_COLORS.primary} 0%, ${THEME_COLORS.secondary} 100%);
  color: white;
  padding: 12px 20px;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
`;

const VideoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 25px;
  margin-bottom: 30px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 20px;
  }
`;

const VideoCard = styled(motion.div)`
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  }
`;

const VideoThumbnail = styled.div`
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f8f9fa;
`;

const ThumbnailImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform ${ANIMATION.DURATION}ms ${ANIMATION.EASING};

  ${VideoCard}:hover & {
    transform: scale(1.05);
  }
`;

const PlayButton = styled(motion.button)`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};

  &:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: translate(-50%, -50%) scale(1.1);
  }
`;

const VideoContent = styled.div`
  padding: 25px;
`;

const VideoHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  gap: 15px;
`;

const VideoTitle = styled.h3`
  font-size: 1.2rem;
  font-weight: 600;
  color: ${THEME_COLORS.text.primary};
  margin: 0;
  line-height: 1.4;
  flex: 1;
`;

const YouTubeLink = styled.a`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 15px;
  background: #ff0000;
  color: white;
  text-decoration: none;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all ${ANIMATION.DURATION}ms ${ANIMATION.EASING};
  white-space: nowrap;

  &:hover {
    background: #cc0000;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
  }
`;

const VideoDescription = styled.p`
  color: ${THEME_COLORS.text.secondary};
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0 0 20px 0;
`;

const VideoMeta = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 20px;

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${THEME_COLORS.text.secondary};
  font-size: 0.9rem;
  font-weight: 500;
`;

const ChannelInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 10px;
  font-size: 0.9rem;
  color: ${THEME_COLORS.text.secondary};
`;

const LoadingSpinner = styled(motion.div)`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  font-size: 1.1rem;
  color: ${THEME_COLORS.text.secondary};
`;

const EmptyState = styled(motion.div)`
  text-align: center;
  padding: 60px 20px;
  color: ${THEME_COLORS.text.secondary};
`;

const SearchResults = ({ 
  results, 
  loading, 
  totalResults, 
  currentPage, 
  totalPages, 
  selectedAlgorithm, 
  searchTime 
}) => {
  const selectedAlgo = SEARCH_ALGORITHMS.find(algo => algo.value === selectedAlgorithm);

  if (loading) {
    return (
      <LoadingSpinner
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        🔍 검색 중...
      </LoadingSpinner>
    );
  }

  if (!results || results.length === 0) {
    return (
      <EmptyState
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h3>검색 결과가 없습니다</h3>
        <p>다른 검색어나 알고리즘을 시도해보세요.</p>
      </EmptyState>
    );
  }

  return (
    <ResultsContainer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <ResultsHeader>
        <ResultsCount>
          총 {formatNumber(totalResults)}개의 결과 중 {((currentPage - 1) * 5) + 1}-{Math.min(currentPage * 5, totalResults)}번째
          {searchTime > 0 && ` (${searchTime.toFixed(2)}초)`}
        </ResultsCount>
        <AlgorithmInfo>
          {selectedAlgo?.icon} {selectedAlgo?.label}
        </AlgorithmInfo>
      </ResultsHeader>

      <VideoGrid>
        {results.map((video, index) => (
          <VideoCard
            key={video.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -5 }}
          >
            <VideoThumbnail>
              <ThumbnailImage
                src={getYouTubeThumbnail(video.id)}
                alt={video.title}
                onError={(e) => {
                  e.target.src = getYouTubeThumbnail(video.id, 'hqdefault');
                }}
              />
              <PlayButton
                onClick={() => window.open(getYouTubeUrl(video.id), '_blank')}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                ▶
              </PlayButton>
            </VideoThumbnail>
            
            <VideoContent>
              <VideoHeader>
                <VideoTitle>{video.title}</VideoTitle>
                <YouTubeLink
                  href={getYouTubeUrl(video.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <FaYoutube />
                  YouTube
                </YouTubeLink>
              </VideoHeader>
              
              <VideoDescription>
                {truncateText(video.description, 150)}
              </VideoDescription>
              
              <VideoMeta>
                <MetaItem>
                  <FaEye />
                  {formatNumber(video.view_count || 0)}
                </MetaItem>
                <MetaItem>
                  <FaThumbsUp />
                  {formatNumber(video.like_count || 0)}
                </MetaItem>
                <MetaItem>
                  <FaComment />
                  {formatNumber(video.comment_count || 0)}
                </MetaItem>
                <MetaItem>
                  <FaCalendarAlt />
                  {formatDate(video.published_at)}
                </MetaItem>
              </VideoMeta>

              <ChannelInfo>
                <strong>채널:</strong> {video.channel_name}
              </ChannelInfo>
            </VideoContent>
          </VideoCard>
        ))}
      </VideoGrid>
    </ResultsContainer>
  );
};

export default SearchResults;
