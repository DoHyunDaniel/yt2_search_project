#!/usr/bin/env python3
"""
YT2 API 서버
수원시 행궁동 YouTube 데이터 검색 API
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opensearchpy import OpenSearch
import redis
from dotenv import load_dotenv

# 머신러닝 라이브러리
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# from sentence_transformers import SentenceTransformer  # 의존성 문제로 임시 비활성화

# 환경변수 로딩
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="YT2 API",
    description="수원시 행궁동 YouTube 데이터 검색 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", "5432")),
    'dbname': os.getenv("DB_NAME", "yt2"),
    'user': os.getenv("DB_USER", "app"),
    'password': os.getenv("DB_PASSWORD", "app1234"),
}

# OpenSearch 클라이언트
OS_CLIENT = OpenSearch(
    hosts=[os.getenv("OS_HOST", "http://localhost:9200")],
    http_auth=(os.getenv("OS_USER", "admin"), os.getenv("OS_PASSWORD", "App1234!@#")),
    use_ssl=False,
    verify_certs=False
)

# Redis 클라이언트
REDIS_CLIENT = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)

# Pydantic 모델
class VideoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    published_at: Optional[str]
    channel_name: str
    view_count: int
    like_count: int
    comment_count: int
    tags: List[str]
    thumbnails: Dict
    # 추가된 필드들
    privacy_status: Optional[str]
    license: Optional[str]
    embeddable: Optional[bool]
    made_for_kids: Optional[bool]
    recording_location: Optional[Dict]
    recording_date: Optional[str]
    localizations: Optional[Dict]
    topic_categories: List[str]
    relevant_topic_ids: List[str]

class SearchResponse(BaseModel):
    videos: List[VideoResponse]
    total_count: int
    total_pages: int
    query: str
    search_time: float

class StatsResponse(BaseModel):
    total_channels: int
    total_videos: int
    total_comments: int
    total_embeddings: int
    videos_last_24h: int
    videos_last_7d: int

# 데이터베이스 연결 함수
def get_db_connection():
    """데이터베이스 연결"""
    return psycopg2.connect(**DB_CONFIG)

# =============================================================================
# 🔍 SEARCH ALGORITHMS SECTION
# =============================================================================
# 각 검색 알고리즘은 독립적인 함수로 구현되어 있습니다.
# 새로운 알고리즘 추가 시 이 섹션에 함수를 추가하세요.

# =============================================================================
# 📊 BASIC SEARCH ALGORITHMS
# =============================================================================

def basic_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """기본 ILIKE 검색"""
    search_query = """
        SELECT 
            v.video_yid as id,
            v.title,
            v.description,
            v.published_at,
            c.title as channel_name,
            (v.statistics->>'view_count')::int as view_count,
            (v.statistics->>'like_count')::int as like_count,
            (v.statistics->>'comment_count')::int as comment_count,
            v.tags,
            v.thumbnails,
            v.privacy_status,
            v.license,
            v.embeddable,
            v.made_for_kids,
            v.recording_location,
            v.recording_date,
            v.localizations,
            v.topic_categories,
            v.relevant_topic_ids
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
        WHERE 
            v.title ILIKE %s OR 
            v.description ILIKE %s OR 
            EXISTS (
                SELECT 1 FROM unnest(v.tags) as tag 
                WHERE tag ILIKE %s
            )
        ORDER BY v.published_at DESC
        LIMIT %s OFFSET %s
    """
    
    cur.execute(search_query, (search_term, search_term, search_term, limit, offset))
    videos = cur.fetchall()
    
    # 총 개수 조회
    count_query = """
        SELECT COUNT(*)
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
        WHERE 
            v.title ILIKE %s OR 
            v.description ILIKE %s OR 
            EXISTS (
                SELECT 1 FROM unnest(v.tags) as tag 
                WHERE tag ILIKE %s
            )
    """
    cur.execute(count_query, (search_term, search_term, search_term))
    total_count = cur.fetchone()['count']
    
    return videos, total_count

# =============================================================================
# 🧮 TF-IDF SEARCH ALGORITHMS
# =============================================================================

def tfidf_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """TF-IDF 기반 검색"""
    # 모든 비디오 데이터 가져오기
    all_videos_query = """
        SELECT 
            v.video_yid as id,
            v.title,
            v.description,
            v.published_at,
            c.title as channel_name,
            (v.statistics->>'view_count')::int as view_count,
            (v.statistics->>'like_count')::int as like_count,
            (v.statistics->>'comment_count')::int as comment_count,
            v.tags,
            v.thumbnails,
            v.privacy_status,
            v.license,
            v.embeddable,
            v.made_for_kids,
            v.recording_location,
            v.recording_date,
            v.localizations,
            v.topic_categories,
            v.relevant_topic_ids
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
    """
    
    cur.execute(all_videos_query)
    all_videos = cur.fetchall()
    
    if not all_videos:
        return [], 0
    
    # 텍스트 데이터 준비
    documents = []
    video_ids = []
    
    for video in all_videos:
        # 제목, 설명, 태그를 하나의 문서로 결합
        doc_text = f"{video['title']} {video['description'] or ''} {' '.join(video['tags'] or [])}"
        documents.append(doc_text)
        video_ids.append(video['id'])
    
    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words=None,  # 한국어는 stop words 제거하지 않음
        ngram_range=(1, 2)  # 1-gram과 2-gram 사용
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
        query_vector = vectorizer.transform([search_term])
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # 유사도 순으로 정렬
        similarity_scores = list(enumerate(similarities))
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 결과 필터링 (유사도가 0보다 큰 것만)
        filtered_results = [(idx, score) for idx, score in similarity_scores if score > 0]
        
        # 페이지네이션 적용
        start_idx = offset
        end_idx = offset + limit
        paginated_results = filtered_results[start_idx:end_idx]
        
        # 결과 비디오 데이터 반환
        result_videos = []
        for idx, score in paginated_results:
            video = all_videos[idx]
            result_videos.append(video)
        
        return result_videos, len(filtered_results)
        
    except Exception as e:
        logger.error(f"TF-IDF 검색 실패: {e}")
        # 실패 시 기본 검색으로 fallback
        return basic_search(cur, search_term, limit, offset)

# =============================================================================
# ⚖️ WEIGHTED SEARCH ALGORITHMS
# =============================================================================

def weighted_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """필드별 가중치가 적용된 검색"""
    # 필드별 가중치
    title_weight = 3.0
    tag_weight = 2.0
    description_weight = 1.0
    
    search_query = """
        SELECT 
            v.video_yid as id,
            v.title,
            v.description,
            v.published_at,
            c.title as channel_name,
            (v.statistics->>'view_count')::int as view_count,
            (v.statistics->>'like_count')::int as like_count,
            (v.statistics->>'comment_count')::int as comment_count,
            v.tags,
            v.thumbnails,
            v.privacy_status,
            v.license,
            v.embeddable,
            v.made_for_kids,
            v.recording_location,
            v.recording_date,
            v.localizations,
            v.topic_categories,
            v.relevant_topic_ids,
            -- 가중치 점수 계산
            (
                CASE WHEN v.title ILIKE %s THEN %s ELSE 0 END +
                CASE WHEN v.description ILIKE %s THEN %s ELSE 0 END +
                CASE WHEN EXISTS (
                    SELECT 1 FROM unnest(v.tags) as tag 
                    WHERE tag ILIKE %s
                ) THEN %s ELSE 0 END
            ) as relevance_score
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
        WHERE 
            v.title ILIKE %s OR 
            v.description ILIKE %s OR 
            EXISTS (
                SELECT 1 FROM unnest(v.tags) as tag 
                WHERE tag ILIKE %s
            )
        ORDER BY relevance_score DESC, v.published_at DESC
        LIMIT %s OFFSET %s
    """
    
    cur.execute(search_query, (
        search_term, title_weight,
        search_term, description_weight,
        search_term, tag_weight,
        search_term, search_term, search_term,
        limit, offset
    ))
    videos = cur.fetchall()
    
    # 총 개수 조회
    count_query = """
        SELECT COUNT(*)
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
        WHERE 
            v.title ILIKE %s OR 
            v.description ILIKE %s OR 
            EXISTS (
                SELECT 1 FROM unnest(v.tags) as tag 
                WHERE tag ILIKE %s
            )
    """
    cur.execute(count_query, (search_term, search_term, search_term))
    total_count = cur.fetchone()['count']
    
    return videos, total_count

# =============================================================================
# 🔍 OPENSEARCH BM25 SEARCH ALGORITHMS
# =============================================================================

def opensearch_bm25_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """OpenSearch BM25 전문 검색"""
    try:
        # OpenSearch에서 BM25 검색 실행
        search_body = {
            "query": {
                "multi_match": {
                    "query": search_term,
                    "fields": [
                        "title^3.0",      # 제목에 높은 가중치
                        "description^1.0", # 설명에 기본 가중치
                        "tags^2.0"        # 태그에 중간 가중치
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"   # 오타 허용
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},  # 관련도 순
                {"published_at": {"order": "desc"}}  # 최신순
            ],
            "from": offset,
            "size": limit
        }
        
        # OpenSearch 검색 실행
        response = OS_CLIENT.search(
            index="videos",
            body=search_body
        )
        
        # 결과에서 비디오 ID 추출
        video_ids = [hit["_source"]["video_id"] for hit in response["hits"]["hits"]]
        
        if not video_ids:
            return [], 0
        
        # PostgreSQL에서 상세 정보 조회
        placeholders = ",".join(["%s"] * len(video_ids))
        detail_query = f"""
            SELECT 
                v.video_yid as id,
                v.title,
                v.description,
                v.published_at,
                c.title as channel_name,
                (v.statistics->>'view_count')::int as view_count,
                (v.statistics->>'like_count')::int as like_count,
                (v.statistics->>'comment_count')::int as comment_count,
                v.tags,
                v.thumbnails,
                v.privacy_status,
                v.license,
                v.embeddable,
                v.made_for_kids,
                v.recording_location,
                v.recording_date,
                v.localizations,
                v.topic_categories,
                v.relevant_topic_ids
            FROM yt2.videos v
            JOIN yt2.channels c ON v.channel_id = c.id
            WHERE v.video_yid IN ({placeholders})
            ORDER BY 
                CASE v.video_yid
                    {''.join([f"WHEN %s THEN {i}" for i in range(len(video_ids))])}
                END
        """
        
        cur.execute(detail_query, video_ids + video_ids)
        videos = cur.fetchall()
        
        # 총 개수 조회 (OpenSearch에서)
        total_count = response["hits"]["total"]["value"]
        
        return videos, total_count
        
    except Exception as e:
        logger.error(f"OpenSearch BM25 검색 실패: {e}")
        # 실패 시 기본 검색으로 fallback
        return basic_search(cur, search_term, limit, offset)

# =============================================================================
# 🔗 HYBRID SEARCH ALGORITHMS
# =============================================================================

def hybrid_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """하이브리드 검색 (TF-IDF + BM25)"""
    try:
        # TF-IDF 검색 실행 (별도 커서 사용)
        with get_db_connection() as tfidf_conn:
            with tfidf_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as tfidf_cur:
                tfidf_videos, tfidf_count = tfidf_search(tfidf_cur, search_term, limit * 2, offset)
        
        # OpenSearch BM25 검색 실행 (별도 커서 사용)
        with get_db_connection() as bm25_conn:
            with bm25_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as bm25_cur:
                bm25_videos, bm25_count = opensearch_bm25_search(bm25_cur, search_term, limit * 2, offset)
        
        # 결과 합치기 및 중복 제거
        video_scores = {}
        
        # TF-IDF 결과에 점수 부여 (0.4 가중치)
        for i, video in enumerate(tfidf_videos):
            video_id = video['id']
            score = 0.4 * (1.0 - i / len(tfidf_videos))  # 순위 기반 점수
            video_scores[video_id] = video_scores.get(video_id, 0) + score
        
        # BM25 결과에 점수 부여 (0.6 가중치)
        for i, video in enumerate(bm25_videos):
            video_id = video['id']
            score = 0.6 * (1.0 - i / len(bm25_videos))  # 순위 기반 점수
            video_scores[video_id] = video_scores.get(video_id, 0) + score
        
        # 점수 순으로 정렬
        sorted_videos = sorted(video_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 최종 결과 생성
        final_videos = []
        video_dict = {v['id']: v for v in tfidf_videos + bm25_videos}
        
        for video_id, score in sorted_videos[:limit]:
            if video_id in video_dict:
                final_videos.append(video_dict[video_id])
        
        return final_videos, len(video_scores)
        
    except Exception as e:
        logger.error(f"하이브리드 검색 실패: {e}")
        # 실패 시 기본 검색으로 fallback
        return basic_search(cur, search_term, limit, offset)

# =============================================================================
# 🧠 SEMANTIC SEARCH ALGORITHMS
# =============================================================================

def semantic_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """의미 기반 검색 (임베딩 유사도)"""
    try:
        # 임베딩이 있는 비디오만 검색
        embedding_query = """
            SELECT 
                v.video_yid as id,
                v.title,
                v.description,
                v.published_at,
                c.title as channel_name,
                (v.statistics->>'view_count')::int as view_count,
                (v.statistics->>'like_count')::int as like_count,
                (v.statistics->>'comment_count')::int as comment_count,
                v.tags,
                v.thumbnails,
                v.privacy_status,
                v.license,
                v.embeddable,
                v.made_for_kids,
                v.recording_location,
                v.recording_date,
                v.localizations,
                v.topic_categories,
                v.relevant_topic_ids,
                e.embedding_vector
            FROM yt2.videos v
            JOIN yt2.channels c ON v.channel_id = c.id
            JOIN yt2.embeddings e ON v.id = e.video_id
            WHERE e.embedding_type = 'title'
        """
        
        cur.execute(embedding_query)
        videos_with_embeddings = cur.fetchall()
        
        if not videos_with_embeddings:
            logger.warning("임베딩 데이터가 없습니다. 기본 검색으로 fallback")
            return basic_search(cur, search_term, limit, offset)
        
        # 쿼리 임베딩 생성 (간단한 TF-IDF 기반)
        documents = [f"{v['title']} {v['description'] or ''}" for v in videos_with_embeddings]
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            query_vector = vectorizer.transform([search_term])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # 유사도 순으로 정렬
            similarity_scores = list(enumerate(similarities))
            similarity_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 결과 필터링 및 페이지네이션
            filtered_results = [(idx, score) for idx, score in similarity_scores if score > 0.1]
            paginated_results = filtered_results[offset:offset + limit]
            
            # 결과 비디오 반환
            result_videos = []
            for idx, score in paginated_results:
                video = videos_with_embeddings[idx]
                result_videos.append(video)
            
            return result_videos, len(filtered_results)
            
        except Exception as e:
            logger.error(f"의미 검색 임베딩 처리 실패: {e}")
            return basic_search(cur, search_term, limit, offset)
        
    except Exception as e:
        logger.error(f"의미 기반 검색 실패: {e}")
        return basic_search(cur, search_term, limit, offset)

# =============================================================================
# 😊 SENTIMENT ANALYSIS SEARCH ALGORITHMS
# =============================================================================

def sentiment_search(cur, search_term: str, limit: int, offset: int) -> tuple:
    """감정 분석이 포함된 검색"""
    try:
        # 기본 검색으로 비디오 찾기
        videos, total_count = basic_search(cur, search_term, limit * 2, offset)
        
        if not videos:
            return [], 0
        
        # 각 비디오의 감정 점수 조회
        video_ids = [v['id'] for v in videos]
        placeholders = ",".join(["%s"] * len(video_ids))
        
        sentiment_query = f"""
            SELECT 
                v.video_yid,
                COALESCE(AVG(c.sentiment_score), 0) as avg_sentiment,
                COUNT(c.id) as comment_count
            FROM yt2.videos v
            LEFT JOIN yt2.comments c ON v.id = c.video_id
            WHERE v.video_yid IN ({placeholders})
            GROUP BY v.video_yid
        """
        
        cur.execute(sentiment_query, video_ids)
        sentiment_data = {row['video_yid']: {
            'avg_sentiment': row['avg_sentiment'],
            'comment_count': row['comment_count']
        } for row in cur.fetchall()}
        
        # 감정 점수를 고려한 최종 점수 계산
        scored_videos = []
        for video in videos:
            video_id = video['id']
            sentiment_info = sentiment_data.get(video_id, {'avg_sentiment': 0, 'comment_count': 0})
            
            # 기본 관련도 점수 (순위 기반)
            base_score = 1.0 - videos.index(video) / len(videos)
            
            # 감정 점수 보너스 (긍정적 댓글이 많은 영상에 가점)
            sentiment_bonus = max(0, sentiment_info['avg_sentiment']) * 0.3
            
            # 댓글 수 보너스 (댓글이 많은 영상에 가점)
            comment_bonus = min(0.2, sentiment_info['comment_count'] / 100) * 0.2
            
            final_score = base_score + sentiment_bonus + comment_bonus
            
            scored_videos.append((video, final_score))
        
        # 최종 점수 순으로 정렬
        scored_videos.sort(key=lambda x: x[1], reverse=True)
        
        # 페이지네이션 적용
        final_videos = [video for video, score in scored_videos[:limit]]
        
        return final_videos, len(scored_videos)
        
    except Exception as e:
        logger.error(f"감정 분석 검색 실패: {e}")
        return basic_search(cur, search_term, limit, offset)

# =============================================================================
# 🎯 SEARCH ALGORITHM ROUTER
# =============================================================================

def execute_search_algorithm(algorithm: str, cur, search_term: str, limit: int, offset: int) -> tuple:
    """검색 알고리즘 실행 라우터"""
    algorithm_map = {
        "basic": basic_search,
        "tfidf": tfidf_search,
        "weighted": weighted_search,
        "bm25": opensearch_bm25_search,
        "hybrid": hybrid_search,
        "semantic": semantic_search,
        "sentiment": sentiment_search
    }
    
    search_func = algorithm_map.get(algorithm, basic_search)
    logger.info(f"검색 알고리즘 실행: {algorithm}")
    
    return search_func(cur, search_term, limit, offset)

# =============================================================================
# 🤖 AI STATISTICS & RECOMMENDATION MODELS
# =============================================================================

class VideoStats(BaseModel):
    video_id: str
    title: str
    channel_name: str
    view_count: int
    like_count: int
    comment_count: int
    published_at: str
    engagement_rate: float
    popularity_score: float

class ChannelStats(BaseModel):
    channel_id: str
    channel_name: str
    video_count: int
    total_views: int
    avg_views: float
    total_likes: int
    avg_likes: float
    engagement_rate: float

class TrendData(BaseModel):
    period: str
    video_count: int
    total_views: int
    avg_views: float
    top_keywords: List[str]

class RecommendationResponse(BaseModel):
    video_id: str
    title: str
    channel_name: str
    thumbnail_url: str
    view_count: int
    like_count: int
    published_at: str
    similarity_score: float
    recommendation_reason: str

# =============================================================================
# 📊 STATISTICS FUNCTIONS
# =============================================================================

def get_popular_videos(cur, limit: int = 10) -> List[VideoStats]:
    """인기 비디오 통계 조회"""
    query = """
    SELECT 
        v.video_yid as video_id,
        v.title,
        c.title as channel_name,
        (v.statistics->>'view_count')::int as view_count,
        (v.statistics->>'like_count')::int as like_count,
        (v.statistics->>'comment_count')::int as comment_count,
        v.published_at,
        CASE 
            WHEN (v.statistics->>'view_count')::int > 0 
            THEN ((v.statistics->>'like_count')::int + (v.statistics->>'comment_count')::int)::float / (v.statistics->>'view_count')::int * 100
            ELSE 0 
        END as engagement_rate,
        CASE 
            WHEN (v.statistics->>'view_count')::int > 0 
            THEN LOG((v.statistics->>'view_count')::int + 1) * 
                 (1 + ((v.statistics->>'like_count')::int + (v.statistics->>'comment_count')::int)::float / (v.statistics->>'view_count')::int)
            ELSE 0 
        END as popularity_score
    FROM yt2.videos v
    JOIN yt2.channels c ON v.channel_id = c.id
    WHERE v.statistics->>'view_count' IS NOT NULL
    ORDER BY popularity_score DESC
    LIMIT %s
    """
    
    cur.execute(query, (limit,))
    results = cur.fetchall()
    
    return [
        VideoStats(
            video_id=row[0],
            title=row[1],
            channel_name=row[2],
            view_count=row[3] or 0,
            like_count=row[4] or 0,
            comment_count=row[5] or 0,
            published_at=row[6].isoformat() if row[6] else "",
            engagement_rate=round(row[7], 2),
            popularity_score=round(row[8], 2)
        )
        for row in results
    ]

def get_channel_stats(cur) -> List[ChannelStats]:
    """채널별 통계 조회"""
    query = """
    SELECT 
        c.id as channel_id,
        c.title as channel_name,
        COUNT(v.id) as video_count,
        SUM((v.statistics->>'view_count')::int) as total_views,
        AVG((v.statistics->>'view_count')::int) as avg_views,
        SUM((v.statistics->>'like_count')::int) as total_likes,
        AVG((v.statistics->>'like_count')::int) as avg_likes,
        AVG(
            CASE 
                WHEN (v.statistics->>'view_count')::int > 0 
                THEN ((v.statistics->>'like_count')::int + (v.statistics->>'comment_count')::int)::float / (v.statistics->>'view_count')::int * 100
                ELSE 0 
            END
        ) as engagement_rate
    FROM yt2.channels c
    LEFT JOIN yt2.videos v ON c.id = v.channel_id
    GROUP BY c.id, c.title
    ORDER BY total_views DESC
    """
    
    cur.execute(query)
    results = cur.fetchall()
    
    return [
        ChannelStats(
            channel_id=str(row[0]),
            channel_name=row[1],
            video_count=row[2],
            total_views=row[3] or 0,
            avg_views=round(row[4] or 0, 2),
            total_likes=row[5] or 0,
            avg_likes=round(row[6] or 0, 2),
            engagement_rate=round(row[7] or 0, 2)
        )
        for row in results
    ]

def get_trend_data(cur, period: str = "month") -> List[TrendData]:
    """트렌드 데이터 조회"""
    if period == "month":
        date_format = "YYYY-MM"
        group_by = "DATE_TRUNC('month', published_at)"
    elif period == "week":
        date_format = "YYYY-\"W\"WW"
        group_by = "DATE_TRUNC('week', published_at)"
    else:  # day
        date_format = "YYYY-MM-DD"
        group_by = "DATE_TRUNC('day', published_at)"
    
    query = f"""
    SELECT 
        TO_CHAR({group_by}, '{date_format}') as period,
        COUNT(*) as video_count,
        SUM((statistics->>'view_count')::int) as total_views,
        AVG((statistics->>'view_count')::int) as avg_views
    FROM yt2.videos
    WHERE published_at IS NOT NULL
    GROUP BY {group_by}
    ORDER BY {group_by} DESC
    LIMIT 12
    """
    
    cur.execute(query)
    results = cur.fetchall()
    
    return [
        TrendData(
            period=row[0],
            video_count=row[1],
            total_views=row[2] or 0,
            avg_views=round(row[3] or 0, 2),
            top_keywords=[]  # TODO: 키워드 분석 추가
        )
        for row in results
    ]

# =============================================================================
# 🎯 RECOMMENDATION FUNCTIONS
# =============================================================================

def get_content_based_recommendations(cur, video_id: str, limit: int = 5) -> List[RecommendationResponse]:
    """콘텐츠 기반 추천 (기존 데이터베이스 방식)"""
    # 1. 기준 비디오 정보 조회
    base_query = """
    SELECT title, description, tags
    FROM yt2.videos
    WHERE video_yid = %s
    """
    cur.execute(base_query, (video_id,))
    base_video = cur.fetchone()
    
    if not base_video:
        return []
    
    # 2. 모든 비디오 정보 조회
    all_query = """
    SELECT v.video_yid, v.title, v.description, v.tags, c.title as channel_name,
           v.statistics->>'view_count' as view_count,
           v.statistics->>'like_count' as like_count,
           v.published_at,
           v.thumbnails->'default'->>'url' as thumbnail_url
    FROM yt2.videos v
    JOIN yt2.channels c ON v.channel_id = c.id
    WHERE v.video_yid != %s
    """
    cur.execute(all_query, (video_id,))
    all_videos = cur.fetchall()
    
    if not all_videos:
        return []
    
    # 3. TF-IDF 벡터화
    base_text = f"{base_video[0]} {base_video[1]} {' '.join(base_video[2] or [])}"
    all_texts = [f"{row[1]} {row[2]} {' '.join(row[3] or [])}" for row in all_videos]
    
    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    base_vector = vectorizer.transform([base_text])
    
    # 4. 유사도 계산
    similarities = cosine_similarity(base_vector, tfidf_matrix).flatten()
    
    # 5. 상위 결과 선택
    top_indices = similarities.argsort()[-limit:][::-1]
    
    recommendations = []
    for idx in top_indices:
        if similarities[idx] > 0.1:  # 임계값 설정
            video = all_videos[idx]
            recommendations.append(RecommendationResponse(
                video_id=video[0],
                title=video[1],
                channel_name=video[4],
                thumbnail_url=video[8] or "",
                view_count=int(video[5] or 0),
                like_count=int(video[6] or 0),
                published_at=video[7].isoformat() if video[7] else "",
                similarity_score=round(similarities[idx], 3),
                recommendation_reason="제목과 설명이 유사합니다"
            ))
    
    return recommendations

def get_youtube_video_info(video_id: str) -> dict:
    """YouTube API를 통해 비디오 정보 조회"""
    try:
        from googleapiclient.discovery import build
        
        # YouTube API 클라이언트 생성
        youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
        
        # 비디오 정보 조회
        request = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            return None
            
        video = response['items'][0]
        snippet = video['snippet']
        statistics = video['statistics']
        
        return {
            'video_id': video_id,
            'title': snippet['title'],
            'description': snippet['description'],
            'channel_title': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'thumbnails': snippet['thumbnails'],
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
            'tags': snippet.get('tags', [])
        }
        
    except Exception as e:
        logger.error(f"YouTube API 오류: {e}")
        if "quotaExceeded" in str(e) or "403" in str(e):
            raise HTTPException(status_code=429, detail="YouTube API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
        else:
            raise HTTPException(status_code=500, detail=f"YouTube API 오류: {str(e)}")

def get_content_based_recommendations_with_youtube_api(cur, video_id: str, limit: int = 5) -> List[RecommendationResponse]:
    """YouTube API를 활용한 콘텐츠 기반 추천"""
    try:
        # 1. YouTube API로 비디오 정보 조회
        youtube_video = get_youtube_video_info(video_id)
        if not youtube_video:
            raise HTTPException(status_code=404, detail="해당 YouTube 비디오를 찾을 수 없습니다.")
        
        # 2. 데이터베이스의 모든 비디오 정보 조회
        all_query = """
        SELECT v.video_yid, v.title, v.description, v.tags, c.title as channel_name,
               v.statistics->>'view_count' as view_count,
               v.statistics->>'like_count' as like_count,
               v.published_at,
               v.thumbnails->'default'->>'url' as thumbnail_url
        FROM yt2.videos v
        JOIN yt2.channels c ON v.channel_id = c.id
        """
        cur.execute(all_query)
        all_videos = cur.fetchall()
        
        if not all_videos:
            return []
        
        # 3. YouTube 비디오와 데이터베이스 비디오들을 TF-IDF로 비교
        youtube_text = f"{youtube_video['title']} {youtube_video['description']} {' '.join(youtube_video['tags'])}"
        db_texts = [f"{row[1]} {row[2]} {' '.join(row[3] or [])}" for row in all_videos]
        
        # 4. TF-IDF 벡터화
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        all_texts = [youtube_text] + db_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # 5. 유사도 계산
        youtube_vector = tfidf_matrix[0:1]
        db_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(youtube_vector, db_vectors).flatten()
        
        # 6. 상위 결과 선택
        top_indices = similarities.argsort()[-limit:][::-1]
        
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # 임계값 설정
                video = all_videos[idx]
                recommendations.append(RecommendationResponse(
                    video_id=video[0],
                    title=video[1],
                    channel_name=video[4],
                    thumbnail_url=video[8] or "",
                    view_count=int(video[5] or 0),
                    like_count=int(video[6] or 0),
                    published_at=video[7].isoformat() if video[7] else "",
                    similarity_score=round(similarities[idx], 3),
                    recommendation_reason=f"'{youtube_video['title']}'와 유사한 콘텐츠입니다"
                ))
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"콘텐츠 기반 추천 오류: {e}")
        raise HTTPException(status_code=500, detail=f"추천 생성 중 오류가 발생했습니다: {str(e)}")

def get_popularity_based_recommendations(cur, limit: int = 5) -> List[RecommendationResponse]:
    """인기도 기반 추천"""
    query = """
    SELECT 
        v.video_yid,
        v.title,
        c.title as channel_name,
        v.statistics->>'view_count' as view_count,
        v.statistics->>'like_count' as like_count,
        v.published_at,
        v.thumbnails->'default'->>'url' as thumbnail_url,
        CASE 
            WHEN (v.statistics->>'view_count')::int > 0 
            THEN LOG((v.statistics->>'view_count')::int + 1) * 
                 (1 + ((v.statistics->>'like_count')::int + (v.statistics->>'comment_count')::int)::float / (v.statistics->>'view_count')::int)
            ELSE 0 
        END as popularity_score
    FROM yt2.videos v
    JOIN yt2.channels c ON v.channel_id = c.id
    WHERE v.statistics->>'view_count' IS NOT NULL
    ORDER BY popularity_score DESC
    LIMIT %s
    """
    
    cur.execute(query, (limit,))
    results = cur.fetchall()
    
    return [
        RecommendationResponse(
            video_id=row[0],
            title=row[1],
            channel_name=row[2],
            thumbnail_url=row[6] or "",
            view_count=int(row[3] or 0),
            like_count=int(row[4] or 0),
            published_at=row[5].isoformat() if row[5] else "",
            similarity_score=round(row[7], 3),
            recommendation_reason="높은 인기도를 보입니다"
        )
        for row in results
    ]

def get_trending_recommendations(cur, limit: int = 5) -> List[RecommendationResponse]:
    """최신 트렌드 추천"""
    query = """
    SELECT 
        v.video_yid,
        v.title,
        c.title as channel_name,
        v.statistics->>'view_count' as view_count,
        v.statistics->>'like_count' as like_count,
        v.published_at,
        v.thumbnails->'default'->>'url' as thumbnail_url,
        EXTRACT(EPOCH FROM (NOW() - v.published_at)) / 86400 as days_ago
    FROM yt2.videos v
    JOIN yt2.channels c ON v.channel_id = c.id
    WHERE v.published_at IS NOT NULL
    ORDER BY v.published_at DESC
    LIMIT %s
    """
    
    cur.execute(query, (limit,))
    results = cur.fetchall()
    
    return [
        RecommendationResponse(
            video_id=row[0],
            title=row[1],
            channel_name=row[2],
            thumbnail_url=row[6] or "",
            view_count=int(row[3] or 0),
            like_count=int(row[4] or 0),
            published_at=row[5].isoformat() if row[5] else "",
            similarity_score=round(1.0 / (1.0 + float(row[7] or 0)), 3),  # decimal.Decimal을 float로 변환
            recommendation_reason="최신 콘텐츠입니다"
        )
        for row in results
    ]

# =============================================================================
# 🌐 API ENDPOINTS
# =============================================================================
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "YT2 API 서버",
        "description": "수원시 행궁동 YouTube 데이터 검색 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        # 데이터베이스 연결 확인
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        # OpenSearch 연결 확인
        OS_CLIENT.ping()
        
        # Redis 연결 확인
        REDIS_CLIENT.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "opensearch": "connected",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 상태 불량: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """데이터베이스 통계"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM yt2.channels) as total_channels,
                        (SELECT COUNT(*) FROM yt2.videos) as total_videos,
                        (SELECT COUNT(*) FROM yt2.comments) as total_comments,
                        (SELECT COUNT(*) FROM yt2.embeddings) as total_embeddings,
                        (SELECT COUNT(*) FROM yt2.videos WHERE created_at >= NOW() - INTERVAL '24 hours') as videos_last_24h,
                        (SELECT COUNT(*) FROM yt2.videos WHERE created_at >= NOW() - INTERVAL '7 days') as videos_last_7d
                """)
                
                stats = cur.fetchone()
                
                return StatsResponse(
                    total_channels=stats[0],
                    total_videos=stats[1],
                    total_comments=stats[2],
                    total_embeddings=stats[3],
                    videos_last_24h=stats[4],
                    videos_last_7d=stats[5]
                )
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@app.get("/api/search", response_model=SearchResponse)
async def search_videos(
    q: str = Query(..., description="검색어"),
    limit: int = Query(10, ge=1, le=100, description="결과 수 제한"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    algorithm: str = Query("basic", description="검색 알고리즘"),
    offset: int = Query(0, ge=0, description="결과 오프셋")
):
    """영상 검색"""
    start_time = datetime.now()
    
    # 페이지 기반 오프셋 계산
    actual_offset = (page - 1) * limit if page > 0 else offset
    
    try:
        # 캐시 확인
        cache_key = f"search:{q}:{limit}:{page}:{algorithm}"
        cached_result = REDIS_CLIENT.get(cache_key)
        if cached_result:
            logger.info(f"캐시에서 결과 반환: {q} (알고리즘: {algorithm})")
            return json.loads(cached_result)
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                search_term = f"%{q}%"
                
                # 🎯 검색 알고리즘 실행
                videos, total_count = execute_search_algorithm(algorithm, cur, search_term, limit, actual_offset)
                
                # 결과 변환
                video_responses = []
                for video in videos:
                    video_responses.append(VideoResponse(
                        id=video['id'],
                        title=video['title'],
                        description=video['description'],
                        published_at=video['published_at'].isoformat() if video['published_at'] else None,
                        channel_name=video['channel_name'],
                        view_count=video['view_count'] or 0,
                        like_count=video['like_count'] or 0,
                        comment_count=video['comment_count'] or 0,
                        tags=video['tags'] or [],
                        thumbnails=video['thumbnails'] or {},
                        # 추가된 필드들
                        privacy_status=video.get('privacy_status'),
                        license=video.get('license'),
                        embeddable=video.get('embeddable'),
                        made_for_kids=video.get('made_for_kids'),
                        recording_location=video.get('recording_location'),
                        recording_date=video['recording_date'].isoformat() if video.get('recording_date') else None,
                        localizations=video.get('localizations'),
                        topic_categories=video.get('topic_categories') or [],
                        relevant_topic_ids=video.get('relevant_topic_ids') or []
                    ))
                
                search_time = (datetime.now() - start_time).total_seconds()
                total_pages = (total_count + limit - 1) // limit  # 올림 계산
                
                result = SearchResponse(
                    videos=video_responses,
                    total_count=total_count,
                    total_pages=total_pages,
                    query=q,
                    search_time=search_time
                )
                
                # 캐시 저장 (5분)
                REDIS_CLIENT.setex(cache_key, 300, json.dumps(result.dict(), default=str))
                
                # 검색 로그 저장
                log_search(q, len(video_responses), search_time)
                
                return result
                
    except Exception as e:
        logger.error(f"검색 실패: {e}")
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@app.get("/videos/{video_id}")
async def get_video_detail(video_id: str):
    """영상 상세 정보"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        v.video_yid as id,
                        v.title,
                        v.description,
                        v.published_at,
                        v.duration,
                        v.statistics,
                        v.tags,
                        v.thumbnails,
                        c.title as channel_name,
                        c.description as channel_description,
                        c.statistics as channel_statistics
                    FROM yt2.videos v
                    JOIN yt2.channels c ON v.channel_id = c.id
                    WHERE v.video_yid = %s
                """, (video_id,))
                
                video = cur.fetchone()
                if not video:
                    raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
                
                return {
                    "id": video['id'],
                    "title": video['title'],
                    "description": video['description'],
                    "published_at": video['published_at'].isoformat() if video['published_at'] else None,
                    "duration": video['duration'],
                    "statistics": video['statistics'],
                    "tags": video['tags'],
                    "thumbnails": video['thumbnails'],
                    "channel": {
                        "name": video['channel_name'],
                        "description": video['channel_description'],
                        "statistics": video['channel_statistics']
                    }
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"영상 상세 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영상 상세 정보 조회 실패: {str(e)}")

@app.get("/channels")
async def get_channels(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """채널 목록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        c.channel_yid as id,
                        c.title,
                        c.description,
                        c.statistics,
                        c.thumbnails,
                        COUNT(v.id) as video_count
                    FROM yt2.channels c
                    LEFT JOIN yt2.videos v ON c.id = v.channel_id
                    GROUP BY c.id, c.channel_yid, c.title, c.description, c.statistics, c.thumbnails
                    ORDER BY video_count DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                channels = cur.fetchall()
                
                return [
                    {
                        "id": channel['id'],
                        "title": channel['title'],
                        "description": channel['description'],
                        "statistics": channel['statistics'],
                        "thumbnails": channel['thumbnails'],
                        "video_count": channel['video_count']
                    }
                    for channel in channels
                ]
                
    except Exception as e:
        logger.error(f"채널 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채널 목록 조회 실패: {str(e)}")

@app.get("/playlists")
async def get_playlists(
    channel_id: Optional[str] = Query(None, description="채널 ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """재생목록 목록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if channel_id:
                    cur.execute("""
                        SELECT 
                            p.playlist_yid as id,
                            p.title,
                            p.description,
                            p.thumbnails,
                            p.item_count,
                            p.privacy_status,
                            p.localizations,
                            c.title as channel_name
                        FROM yt2.playlists p
                        JOIN yt2.channels c ON p.channel_id = c.id
                        WHERE c.channel_yid = %s
                        ORDER BY p.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (channel_id, limit, offset))
                else:
                    cur.execute("""
                        SELECT 
                            p.playlist_yid as id,
                            p.title,
                            p.description,
                            p.thumbnails,
                            p.item_count,
                            p.privacy_status,
                            p.localizations,
                            c.title as channel_name
                        FROM yt2.playlists p
                        JOIN yt2.channels c ON p.channel_id = c.id
                        ORDER BY p.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                
                playlists = cur.fetchall()
                
                return [
                    {
                        "id": playlist['id'],
                        "title": playlist['title'],
                        "description": playlist['description'],
                        "thumbnails": playlist['thumbnails'],
                        "item_count": playlist['item_count'],
                        "privacy_status": playlist['privacy_status'],
                        "localizations": playlist['localizations'],
                        "channel_name": playlist['channel_name']
                    }
                    for playlist in playlists
                ]
                
    except Exception as e:
        logger.error(f"재생목록 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"재생목록 목록 조회 실패: {str(e)}")

@app.get("/playlists/{playlist_id}/items")
async def get_playlist_items(
    playlist_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """재생목록 아이템 목록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        pi.playlist_item_yid as id,
                        pi.position,
                        pi.title,
                        pi.description,
                        pi.thumbnails,
                        pi.published_at,
                        v.video_yid as video_id,
                        v.title as video_title,
                        v.duration,
                        v.statistics
                    FROM yt2.playlist_items pi
                    LEFT JOIN yt2.videos v ON pi.video_id = v.id
                    WHERE pi.playlist_id = (
                        SELECT id FROM yt2.playlists WHERE playlist_yid = %s
                    )
                    ORDER BY pi.position
                    LIMIT %s OFFSET %s
                """, (playlist_id, limit, offset))
                
                items = cur.fetchall()
                
                return [
                    {
                        "id": item['id'],
                        "position": item['position'],
                        "title": item['title'],
                        "description": item['description'],
                        "thumbnails": item['thumbnails'],
                        "published_at": item['published_at'].isoformat() if item['published_at'] else None,
                        "video_id": item['video_id'],
                        "video_title": item['video_title'],
                        "duration": item['duration'],
                        "statistics": item['statistics']
                    }
                    for item in items
                ]
                
    except Exception as e:
        logger.error(f"재생목록 아이템 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"재생목록 아이템 조회 실패: {str(e)}")

@app.get("/videos/{video_id}/captions")
async def get_video_captions(video_id: str):
    """영상 자막 목록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        caption_yid as id,
                        language,
                        name,
                        status,
                        track_kind,
                        is_auto_synced,
                        is_cc,
                        is_draft,
                        is_served,
                        is_auto_generated,
                        last_updated
                    FROM yt2.captions
                    WHERE video_id = (
                        SELECT id FROM yt2.videos WHERE video_yid = %s
                    )
                    ORDER BY language
                """, (video_id,))
                
                captions = cur.fetchall()
                
                return [
                    {
                        "id": caption['id'],
                        "language": caption['language'],
                        "name": caption['name'],
                        "status": caption['status'],
                        "track_kind": caption['track_kind'],
                        "is_auto_synced": caption['is_auto_synced'],
                        "is_cc": caption['is_cc'],
                        "is_draft": caption['is_draft'],
                        "is_served": caption['is_served'],
                        "is_auto_generated": caption['is_auto_generated'],
                        "last_updated": caption['last_updated'].isoformat() if caption['last_updated'] else None
                    }
                    for caption in captions
                ]
                
    except Exception as e:
        logger.error(f"영상 자막 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영상 자막 조회 실패: {str(e)}")

@app.get("/categories")
async def get_video_categories():
    """영상 카테고리 목록"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        category_yid as id,
                        title,
                        assignable,
                        channel_id
                    FROM yt2.video_categories
                    ORDER BY category_yid
                """)
                
                categories = cur.fetchall()
                
                return [
                    {
                        "id": category['id'],
                        "title": category['title'],
                        "assignable": category['assignable'],
                        "channel_id": category['channel_id']
                    }
                    for category in categories
                ]
                
    except Exception as e:
        logger.error(f"영상 카테고리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영상 카테고리 조회 실패: {str(e)}")

def log_search(query: str, result_count: int, search_time: float):
    """검색 로그 저장"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO yt2.search_logs (query, results_count, response_time_ms)
                    VALUES (%s, %s, %s)
                """, (query, result_count, int(search_time * 1000)))
                conn.commit()
    except Exception as e:
        logger.error(f"검색 로그 저장 실패: {e}")

# =============================================================================
# 🤖 AI STATISTICS & RECOMMENDATION API ENDPOINTS
# =============================================================================

@app.get("/api/stats/popular-videos", response_model=List[VideoStats])
async def get_popular_videos_api(limit: int = Query(10, ge=1, le=50, description="결과 수 제한")):
    """인기 비디오 통계 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_popular_videos(cur, limit)
    except Exception as e:
        logger.error(f"인기 비디오 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인기 비디오 조회 실패: {str(e)}")

@app.get("/api/stats/channels", response_model=List[ChannelStats])
async def get_channel_stats_api():
    """채널별 통계 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_channel_stats(cur)
    except Exception as e:
        logger.error(f"채널 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채널 통계 조회 실패: {str(e)}")

@app.get("/api/stats/trends", response_model=List[TrendData])
async def get_trend_data_api(period: str = Query("month", description="기간 (day, week, month)")):
    """트렌드 데이터 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_trend_data(cur, period)
    except Exception as e:
        logger.error(f"트렌드 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"트렌드 데이터 조회 실패: {str(e)}")

@app.get("/api/recommendations/content-based", response_model=List[RecommendationResponse])
async def get_content_based_recommendations_api(
    video_id: str = Query(..., description="기준 비디오 ID"),
    limit: int = Query(5, ge=1, le=20, description="추천 수 제한")
):
    """콘텐츠 기반 추천 (기존 데이터베이스 방식)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_content_based_recommendations(cur, video_id, limit)
    except Exception as e:
        logger.error(f"콘텐츠 기반 추천 실패: {e}")
        raise HTTPException(status_code=500, detail=f"콘텐츠 기반 추천 실패: {str(e)}")

@app.get("/api/recommendations/content-based-youtube", response_model=List[RecommendationResponse])
async def get_content_based_recommendations_youtube_api(
    video_id: str = Query(..., description="YouTube 비디오 ID"),
    limit: int = Query(5, ge=1, le=20, description="추천 수 제한")
):
    """YouTube API를 활용한 콘텐츠 기반 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_content_based_recommendations_with_youtube_api(cur, video_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube API 콘텐츠 기반 추천 실패: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube API 콘텐츠 기반 추천 실패: {str(e)}")

@app.get("/api/recommendations/popularity", response_model=List[RecommendationResponse])
async def get_popularity_recommendations_api(
    limit: int = Query(5, ge=1, le=20, description="추천 수 제한")
):
    """인기도 기반 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_popularity_based_recommendations(cur, limit)
    except Exception as e:
        logger.error(f"인기도 기반 추천 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인기도 기반 추천 실패: {str(e)}")

@app.get("/api/recommendations/trending", response_model=List[RecommendationResponse])
async def get_trending_recommendations_api(
    limit: int = Query(5, ge=1, le=20, description="추천 수 제한")
):
    """최신 트렌드 추천"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return get_trending_recommendations(cur, limit)
    except Exception as e:
        logger.error(f"트렌드 추천 실패: {e}")
        raise HTTPException(status_code=500, detail=f"트렌드 추천 실패: {str(e)}")

@app.get("/api/stats/overview")
async def get_stats_overview():
    """통계 개요 조회"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 전체 통계
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_videos,
                        COUNT(DISTINCT channel_id) as total_channels,
                        SUM((statistics->>'view_count')::int) as total_views,
                        AVG((statistics->>'view_count')::int) as avg_views,
                        SUM((statistics->>'like_count')::int) as total_likes,
                        AVG((statistics->>'like_count')::int) as avg_likes
                    FROM yt2.videos
                    WHERE statistics->>'view_count' IS NOT NULL
                """)
                overall_stats = cur.fetchone()
                
                # 최근 7일 통계
                cur.execute("""
                    SELECT 
                        COUNT(*) as recent_videos,
                        SUM((statistics->>'view_count')::int) as recent_views
                    FROM yt2.videos
                    WHERE published_at >= NOW() - INTERVAL '7 days'
                    AND statistics->>'view_count' IS NOT NULL
                """)
                recent_stats = cur.fetchone()
                
                return {
                    "overall": {
                        "total_videos": overall_stats[0] or 0,
                        "total_channels": overall_stats[1] or 0,
                        "total_views": overall_stats[2] or 0,
                        "avg_views": round(overall_stats[3] or 0, 2),
                        "total_likes": overall_stats[4] or 0,
                        "avg_likes": round(overall_stats[5] or 0, 2)
                    },
                    "recent_7_days": {
                        "new_videos": recent_stats[0] or 0,
                        "new_views": recent_stats[1] or 0
                    }
                }
    except Exception as e:
        logger.error(f"통계 개요 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 개요 조회 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
