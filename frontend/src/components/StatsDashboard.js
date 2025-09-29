import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaChartLine, FaUsers, FaVideo, FaEye, FaThumbsUp, FaComments, FaTrendingUp } from 'react-icons/fa';
import { api } from '../services/api';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const StatCard = styled(motion.div)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 25px;
  color: white;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
`;

const StatIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 15px;
  opacity: 0.9;
`;

const StatTitle = styled.h3`
  font-size: 1.1rem;
  margin-bottom: 10px;
  opacity: 0.9;
  font-weight: 500;
`;

const StatValue = styled.div`
  font-size: 2.2rem;
  font-weight: bold;
  margin-bottom: 5px;
`;

const StatSubtitle = styled.div`
  font-size: 0.9rem;
  opacity: 0.8;
`;

const SectionTitle = styled.h2`
  font-size: 1.8rem;
  margin: 40px 0 20px 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const VideoList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const VideoCard = styled(motion.div)`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  border: 1px solid #e0e0e0;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  }
`;

const VideoThumbnail = styled.img`
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 15px;
`;

const VideoTitle = styled.h4`
  font-size: 1.1rem;
  margin-bottom: 10px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const VideoChannel = styled.div`
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 10px;
`;

const VideoStats = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: #888;
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
`;

const EngagementRate = styled.div`
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: bold;
  margin-top: 10px;
  display: inline-block;
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

function StatsDashboard() {
  const [overview, setOverview] = useState(null);
  const [popularVideos, setPopularVideos] = useState([]);
  const [channelStats, setChannelStats] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAllStats();
  }, []);

  const fetchAllStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewRes, popularRes, channelsRes, trendsRes] = await Promise.all([
        api.get('/api/stats/overview'),
        api.get('/api/stats/popular-videos?limit=6'),
        api.get('/api/stats/channels'),
        api.get('/api/stats/trends?period=month')
      ]);

      setOverview(overviewRes.data);
      setPopularVideos(popularRes.data);
      setChannelStats(channelsRes.data);
      setTrends(trendsRes.data);
    } catch (err) {
      setError('통계 데이터를 불러오는데 실패했습니다.');
      console.error('Stats fetch error:', err);
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <DashboardContainer>
        <LoadingSpinner>📊 통계 데이터를 불러오는 중...</LoadingSpinner>
      </DashboardContainer>
    );
  }

  if (error) {
    return (
      <DashboardContainer>
        <ErrorMessage>{error}</ErrorMessage>
      </DashboardContainer>
    );
  }

  return (
    <DashboardContainer>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <SectionTitle>
          <FaChartLine /> AI 통계 대시보드
        </SectionTitle>

        {/* 개요 통계 */}
        {overview && (
          <StatsGrid>
            <StatCard
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              <StatIcon><FaVideo /></StatIcon>
              <StatTitle>총 비디오 수</StatTitle>
              <StatValue>{formatNumber(overview.overall.total_videos)}</StatValue>
              <StatSubtitle>전체 수집된 영상</StatSubtitle>
            </StatCard>

            <StatCard
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <StatIcon><FaUsers /></StatIcon>
              <StatTitle>채널 수</StatTitle>
              <StatValue>{overview.overall.total_channels}</StatValue>
              <StatSubtitle>활성 채널</StatSubtitle>
            </StatCard>

            <StatCard
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
            >
              <StatIcon><FaEye /></StatIcon>
              <StatTitle>총 조회수</StatTitle>
              <StatValue>{formatNumber(overview.overall.total_views)}</StatValue>
              <StatSubtitle>누적 조회수</StatSubtitle>
            </StatCard>

            <StatCard
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
            >
              <StatIcon><FaThumbsUp /></StatIcon>
              <StatTitle>총 좋아요</StatTitle>
              <StatValue>{formatNumber(overview.overall.total_likes)}</StatValue>
              <StatSubtitle>누적 좋아요</StatSubtitle>
            </StatCard>
          </StatsGrid>
        )}

        {/* 인기 비디오 */}
        <SectionTitle>
          <FaTrendingUp /> 인기 비디오 TOP 6
        </SectionTitle>
        <VideoList>
          {popularVideos.map((video, index) => (
            <VideoCard
              key={video.video_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
            >
              {video.thumbnail_url && (
                <VideoThumbnail
                  src={video.thumbnail_url}
                  alt={video.title}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
              <VideoTitle>{video.title}</VideoTitle>
              <VideoChannel>{video.channel_name}</VideoChannel>
              <VideoStats>
                <StatItem>
                  <FaEye /> {formatNumber(video.view_count)}
                </StatItem>
                <StatItem>
                  <FaThumbsUp /> {formatNumber(video.like_count)}
                </StatItem>
                <StatItem>
                  <FaComments /> {formatNumber(video.comment_count)}
                </StatItem>
              </VideoStats>
              <EngagementRate>
                참여도: {video.engagement_rate}%
              </EngagementRate>
            </VideoCard>
          ))}
        </VideoList>

        {/* 채널 통계 */}
        <SectionTitle>
          <FaUsers /> 채널별 성과
        </SectionTitle>
        <VideoList>
          {channelStats.slice(0, 6).map((channel, index) => (
            <VideoCard
              key={channel.channel_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <VideoTitle>{channel.channel_name}</VideoTitle>
              <VideoStats>
                <StatItem>
                  <FaVideo /> {channel.video_count}개 영상
                </StatItem>
                <StatItem>
                  <FaEye /> {formatNumber(channel.total_views)} 조회
                </StatItem>
              </VideoStats>
              <EngagementRate>
                참여도: {channel.engagement_rate}%
              </EngagementRate>
            </VideoCard>
          ))}
        </VideoList>
      </motion.div>
    </DashboardContainer>
  );
}

export default StatsDashboard;
