-- YT2 데이터베이스 스키마
-- 수원시 행궁동 관련 YouTube 데이터 수집 시스템

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS yt2;

-- 채널 테이블
CREATE TABLE IF NOT EXISTS yt2.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL DEFAULT 'youtube',
    channel_yid VARCHAR(50) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    custom_url VARCHAR(100),
    country_code VARCHAR(5),
    thumbnails JSONB,
    statistics JSONB,
    tags TEXT[],
    -- 추가된 필드들
    branding_settings JSONB,
    content_details JSONB,
    privacy_status VARCHAR(20),
    is_linked BOOLEAN,
    long_uploads_status VARCHAR(20),
    made_for_kids BOOLEAN,
    self_declared_made_for_kids BOOLEAN,
    localizations JSONB,
    topic_categories TEXT[],
    relevant_topic_ids TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(platform, channel_yid)
);

-- 영상 테이블
CREATE TABLE IF NOT EXISTS yt2.videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL DEFAULT 'youtube',
    video_yid VARCHAR(50) NOT NULL UNIQUE,
    channel_id UUID NOT NULL REFERENCES yt2.channels(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMPTZ,
    duration VARCHAR(20),
    thumbnails JSONB,
    statistics JSONB,
    tags TEXT[],
    category_id INTEGER,
    default_language VARCHAR(10),
    content_rating VARCHAR(20),
    -- 추가된 필드들
    privacy_status VARCHAR(20),
    license VARCHAR(20),
    embeddable BOOLEAN,
    public_stats_viewable BOOLEAN,
    made_for_kids BOOLEAN,
    self_declared_made_for_kids BOOLEAN,
    recording_location JSONB,
    recording_date TIMESTAMPTZ,
    localizations JSONB,
    topic_categories TEXT[],
    relevant_topic_ids TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(platform, video_yid)
);

-- 댓글 테이블
CREATE TABLE IF NOT EXISTS yt2.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES yt2.videos(id) ON DELETE CASCADE,
    comment_yid VARCHAR(50) NOT NULL UNIQUE,
    parent_id UUID REFERENCES yt2.comments(id) ON DELETE CASCADE,
    author_name VARCHAR(255),
    author_channel_id VARCHAR(50),
    text_display TEXT,
    text_original TEXT,
    like_count INTEGER DEFAULT 0,
    published_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 임베딩 테이블
CREATE TABLE IF NOT EXISTS yt2.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES yt2.videos(id) ON DELETE CASCADE,
    embedding_type VARCHAR(50) NOT NULL,
    embedding_vector FLOAT[] NOT NULL,
    embedding_dim INTEGER NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(video_id, embedding_type, model_name)
);

-- 검색 로그 테이블
CREATE TABLE IF NOT EXISTS yt2.search_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    search_type VARCHAR(50),
    results_count INTEGER,
    user_ip INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 재생목록 테이블
CREATE TABLE IF NOT EXISTS yt2.playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL DEFAULT 'youtube',
    playlist_yid VARCHAR(50) NOT NULL UNIQUE,
    channel_id UUID REFERENCES yt2.channels(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    thumbnails JSONB,
    item_count INTEGER DEFAULT 0,
    privacy_status VARCHAR(20),
    localizations JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(platform, playlist_yid)
);

-- 재생목록 아이템 테이블
CREATE TABLE IF NOT EXISTS yt2.playlist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playlist_id UUID NOT NULL REFERENCES yt2.playlists(id) ON DELETE CASCADE,
    video_id UUID REFERENCES yt2.videos(id) ON DELETE CASCADE,
    playlist_item_yid VARCHAR(50) NOT NULL UNIQUE,
    position INTEGER,
    title TEXT,
    description TEXT,
    thumbnails JSONB,
    published_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(playlist_id, playlist_item_yid)
);

-- 자막 테이블
CREATE TABLE IF NOT EXISTS yt2.captions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES yt2.videos(id) ON DELETE CASCADE,
    caption_yid VARCHAR(50) NOT NULL UNIQUE,
    language VARCHAR(10),
    name VARCHAR(255),
    status VARCHAR(20),
    track_kind VARCHAR(20),
    is_auto_synced BOOLEAN,
    is_cc BOOLEAN,
    is_draft BOOLEAN,
    is_served BOOLEAN,
    is_auto_generated BOOLEAN,
    last_updated TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 구독 테이블
CREATE TABLE IF NOT EXISTS yt2.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_channel_id UUID REFERENCES yt2.channels(id) ON DELETE CASCADE,
    subscribed_channel_id UUID REFERENCES yt2.channels(id) ON DELETE CASCADE,
    subscription_yid VARCHAR(50) NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    thumbnails JSONB,
    resource_id VARCHAR(50),
    resource_type VARCHAR(20),
    published_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(subscriber_channel_id, subscribed_channel_id)
);

-- 영상 카테고리 테이블
CREATE TABLE IF NOT EXISTS yt2.video_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_yid INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    assignable BOOLEAN DEFAULT true,
    channel_id VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 채널 섹션 테이블
CREATE TABLE IF NOT EXISTS yt2.channel_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES yt2.channels(id) ON DELETE CASCADE,
    section_yid VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(50),
    style VARCHAR(50),
    title TEXT,
    position INTEGER,
    localized_title TEXT,
    content_details JSONB,
    target_id VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_channels_platform_yid ON yt2.channels(platform, channel_yid);
CREATE INDEX IF NOT EXISTS idx_channels_title ON yt2.channels USING gin(to_tsvector('korean', title));
CREATE INDEX IF NOT EXISTS idx_channels_created_at ON yt2.channels(created_at);

CREATE INDEX IF NOT EXISTS idx_videos_platform_yid ON yt2.videos(platform, video_yid);
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON yt2.videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_title ON yt2.videos USING gin(to_tsvector('korean', title));
CREATE INDEX IF NOT EXISTS idx_videos_description ON yt2.videos USING gin(to_tsvector('korean', description));
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON yt2.videos(published_at);
CREATE INDEX IF NOT EXISTS idx_videos_tags ON yt2.videos USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_comments_video_id ON yt2.comments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON yt2.comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_comments_published_at ON yt2.comments(published_at);
CREATE INDEX IF NOT EXISTS idx_comments_sentiment ON yt2.comments(sentiment_score);

CREATE INDEX IF NOT EXISTS idx_embeddings_video_id ON yt2.embeddings(video_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON yt2.embeddings(embedding_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON yt2.embeddings(model_name);

CREATE INDEX IF NOT EXISTS idx_search_logs_query ON yt2.search_logs USING gin(to_tsvector('korean', query));
CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON yt2.search_logs(created_at);

-- 새로운 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_playlists_channel_id ON yt2.playlists(channel_id);
CREATE INDEX IF NOT EXISTS idx_playlists_platform_yid ON yt2.playlists(platform, playlist_yid);
CREATE INDEX IF NOT EXISTS idx_playlists_title ON yt2.playlists USING gin(to_tsvector('korean', title));

CREATE INDEX IF NOT EXISTS idx_playlist_items_playlist_id ON yt2.playlist_items(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_items_video_id ON yt2.playlist_items(video_id);
CREATE INDEX IF NOT EXISTS idx_playlist_items_position ON yt2.playlist_items(position);

CREATE INDEX IF NOT EXISTS idx_captions_video_id ON yt2.captions(video_id);
CREATE INDEX IF NOT EXISTS idx_captions_language ON yt2.captions(language);
CREATE INDEX IF NOT EXISTS idx_captions_status ON yt2.captions(status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_subscriber ON yt2.subscriptions(subscriber_channel_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_subscribed ON yt2.subscriptions(subscribed_channel_id);

CREATE INDEX IF NOT EXISTS idx_video_categories_yid ON yt2.video_categories(category_yid);
CREATE INDEX IF NOT EXISTS idx_video_categories_assignable ON yt2.video_categories(assignable);

CREATE INDEX IF NOT EXISTS idx_channel_sections_channel_id ON yt2.channel_sections(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_sections_type ON yt2.channel_sections(type);

-- 통계 뷰
CREATE OR REPLACE VIEW yt2.stats AS
SELECT 
    (SELECT COUNT(*) FROM yt2.channels) as total_channels,
    (SELECT COUNT(*) FROM yt2.videos) as total_videos,
    (SELECT COUNT(*) FROM yt2.comments) as total_comments,
    (SELECT COUNT(*) FROM yt2.embeddings) as total_embeddings,
    (SELECT COUNT(*) FROM yt2.search_logs) as total_searches,
    (SELECT COUNT(*) FROM yt2.videos WHERE created_at >= NOW() - INTERVAL '24 hours') as videos_last_24h,
    (SELECT COUNT(*) FROM yt2.videos WHERE created_at >= NOW() - INTERVAL '7 days') as videos_last_7d;

-- 코사인 유사도 함수
CREATE OR REPLACE FUNCTION yt2.cosine_similarity(vec1 FLOAT[], vec2 FLOAT[])
RETURNS FLOAT AS $$
BEGIN
    RETURN (
        SELECT (vec1 <#> vec2) * -1 / (norm(vec1) * norm(vec2))
    );
END;
$$ LANGUAGE plpgsql;

-- 유사 영상 검색 함수
CREATE OR REPLACE FUNCTION yt2.find_similar_videos(
    query_embedding FLOAT[],
    embedding_type VARCHAR(50) DEFAULT 'title',
    similarity_threshold FLOAT DEFAULT 0.7,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    video_id UUID,
    title TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.title,
        yt2.cosine_similarity(query_embedding, e.embedding_vector) as similarity_score
    FROM yt2.videos v
    JOIN yt2.embeddings e ON v.id = e.video_id
    WHERE e.embedding_type = embedding_type
    AND yt2.cosine_similarity(query_embedding, e.embedding_vector) > similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
