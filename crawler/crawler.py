#!/usr/bin/env python3
"""
YT2 YouTube 크롤러
수원시 행궁동 관련 YouTube 영상 데이터 수집
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import psycopg2
import psycopg2.extras
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from opensearchpy import OpenSearch
import redis
from dotenv import load_dotenv

# 환경변수 로딩
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YT2Crawler:
    """YT2 YouTube 크롤러 클래스"""
    
    def __init__(self):
        """크롤러 초기화"""
        # YouTube API 설정
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        # 데이터베이스 설정
        self.db_config = {
            'host': os.getenv("DB_HOST", "localhost"),
            'port': int(os.getenv("DB_PORT", "5432")),
            'dbname': os.getenv("DB_NAME", "yt2"),
            'user': os.getenv("DB_USER", "app"),
            'password': os.getenv("DB_PASSWORD", "app1234"),
        }
        
        # OpenSearch 설정
        self.os_client = OpenSearch(
            hosts=[os.getenv("OS_HOST", "http://localhost:9200")],
            http_auth=(os.getenv("OS_USER", "admin"), os.getenv("OS_PASSWORD", "App1234!@#")),
            use_ssl=False,
            verify_certs=False
        )
        
        # Redis 설정
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        
        # 수원시 행궁동 관련 키워드
        self.keywords = [
            # 기본 행궁 키워드
            "수원 행궁", "수원시 행궁동", "수원행궁", "화성행궁",
            "수원 화성", "화성", "수원시 화성",
            
            # 관광 및 문화
            "수원행궁 관광", "수원행궁 투어", "수원행궁 나들이",
            "수원행궁 문화재", "수원행궁 역사", "수원행궁 해설",
            "수원행궁 가이드", "수원행궁 체험",
            
            # 데이트 및 가족
            "수원행궁 데이트", "수원행궁 커플", "수원행궁 가족",
            "수원행궁 소풍", "수원행궁 아이와", "수원행궁 어린이",
            
            # 음식 및 맛집
            "수원행궁 맛집", "수원행궁 식당", "수원행궁 카페",
            "수원행궁 주변 맛집", "수원행궁 주변 식당",
            "수원행궁 주변 카페", "수원행궁 음식",
            
            # 교통 및 접근
            "수원행궁 가는법", "수원행궁 교통", "수원행궁 지하철",
            "수원행궁 버스", "수원행궁 주차", "수원행궁 입장료",
            
            # 계절별
            "수원행궁 봄", "수원행궁 여름", "수원행궁 가을", "수원행궁 겨울",
            "수원행궁 벚꽃", "수원행궁 단풍", "수원행궁 눈",
            
            # 특별 행사
            "수원행궁 축제", "수원행궁 행사", "수원행궁 공연",
            "수원행궁 전시", "수원행궁 이벤트",
            
            # 지역명
            "팔달구 행궁동", "수원 팔달구", "수원시 팔달구",
            "행궁동 맛집", "행궁동 카페", "행궁동 데이트"
        ]
        
        # API 할당량 관리
        self.daily_quota = 10000  # 일일 할당량
        self.quota_used = 0
        self.last_reset = datetime.now().date()
    
    def check_quota(self) -> bool:
        """API 할당량 확인"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.quota_used = 0
            self.last_reset = today
        
        return self.quota_used < self.daily_quota
    
    def search_videos(self, keyword: str, max_results: int = 50, days: int = 30) -> List[Dict]:
        """키워드로 영상 검색"""
        if not self.check_quota():
            logger.warning("일일 API 할당량을 초과했습니다.")
            return []
        
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"
            
            search_response = self.youtube.search().list(
                part='snippet',
                q=keyword,
                type='video',
                publishedAfter=since,
                maxResults=max_results,
                order='relevance'
            ).execute()
            
            self.quota_used += 1
            
            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                # 영상 상세 정보 수집
                video_details = self.get_video_details(video_id)
                if video_details:
                    videos.append(video_details)
            
            logger.info(f"키워드 '{keyword}'에서 {len(videos)}개 영상 발견")
            return videos
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"YouTube API 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"영상 검색 실패: {e}")
            return []
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """영상 상세 정보 수집"""
        if not self.check_quota():
            return None
        
        try:
            # 영상 기본 정보 (모든 추가 필드 포함)
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails,status,recordingDetails,localizations,topicDetails',
                id=video_id
            ).execute()
            
            self.quota_used += 1
            
            if not video_response.get('items'):
                return None
            
            video = video_response['items'][0]
            snippet = video['snippet']
            statistics = video.get('statistics', {})
            content_details = video.get('contentDetails', {})
            status = video.get('status', {})
            recording_details = video.get('recordingDetails', {})
            localizations = video.get('localizations', {})
            topic_details = video.get('topicDetails', {})
            
            # 채널 정보
            channel_id = snippet['channelId']
            channel_details = self.get_channel_details(channel_id)
            
            # 댓글 수집
            comments = self.get_video_comments(video_id)
            
            # 자막 정보 수집
            captions = self.get_video_captions(video_id)
            
            return {
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'published_at': snippet['publishedAt'],
                'duration': content_details.get('duration'),
                'thumbnails': snippet.get('thumbnails', {}),
                'statistics': {
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'favorite_count': int(statistics.get('favoriteCount', 0))
                },
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId'),
                'default_language': snippet.get('defaultLanguage'),
                'content_rating': snippet.get('contentRating'),
                # 추가된 필드들
                'privacy_status': status.get('privacyStatus'),
                'license': status.get('license'),
                'embeddable': status.get('embeddable'),
                'public_stats_viewable': status.get('publicStatsViewable'),
                'made_for_kids': status.get('madeForKids'),
                'self_declared_made_for_kids': status.get('selfDeclaredMadeForKids'),
                'recording_location': recording_details.get('location'),
                'recording_date': recording_details.get('recordingDate'),
                'localizations': localizations,
                'topic_categories': topic_details.get('topicCategories', []),
                'relevant_topic_ids': topic_details.get('relevantTopicIds', []),
                'channel': channel_details,
                'comments': comments,
                'captions': captions
            }
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"영상 상세 정보 수집 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"영상 상세 정보 수집 실패: {e}")
            return None
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict]:
        """채널 상세 정보 수집"""
        if not self.check_quota():
            return None
        
        try:
            channel_response = self.youtube.channels().list(
                part='snippet,statistics,brandingSettings,contentDetails,status,topicDetails,localizations',
                id=channel_id
            ).execute()
            
            self.quota_used += 1
            
            if not channel_response.get('items'):
                return None
            
            channel = channel_response['items'][0]
            snippet = channel['snippet']
            statistics = channel.get('statistics', {})
            branding_settings = channel.get('brandingSettings', {})
            content_details = channel.get('contentDetails', {})
            status = channel.get('status', {})
            topic_details = channel.get('topicDetails', {})
            localizations = channel.get('localizations', {})
            
            return {
                'channel_id': channel_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'custom_url': snippet.get('customUrl'),
                'country': snippet.get('country'),
                'thumbnails': snippet.get('thumbnails', {}),
                'statistics': {
                    'subscriber_count': int(statistics.get('subscriberCount', 0)),
                    'video_count': int(statistics.get('videoCount', 0)),
                    'view_count': int(statistics.get('viewCount', 0))
                },
                'tags': snippet.get('tags', []),
                # 추가된 필드들
                'branding_settings': branding_settings,
                'content_details': content_details,
                'privacy_status': status.get('privacyStatus'),
                'is_linked': status.get('isLinked'),
                'long_uploads_status': status.get('longUploadsStatus'),
                'made_for_kids': status.get('madeForKids'),
                'self_declared_made_for_kids': status.get('selfDeclaredMadeForKids'),
                'localizations': localizations,
                'topic_categories': topic_details.get('topicCategories', []),
                'relevant_topic_ids': topic_details.get('relevantTopicIds', [])
            }
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"채널 정보 수집 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"채널 정보 수집 실패: {e}")
            return None
    
    def get_video_comments(self, video_id: str, max_comments: int = 100) -> List[Dict]:
        """영상 댓글 수집"""
        if not self.check_quota():
            return []
        
        try:
            comments_response = self.youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=max_comments,
                order='relevance'
            ).execute()
            
            self.quota_used += 1
            
            comments = []
            for item in comments_response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                
                comments.append({
                    'comment_id': item['id'],
                    'author_name': comment['authorDisplayName'],
                    'author_channel_id': comment.get('authorChannelId', {}).get('value'),
                    'text_display': comment['textDisplay'],
                    'text_original': comment['textOriginal'],
                    'like_count': comment['likeCount'],
                    'published_at': comment['publishedAt'],
                    'updated_at': comment['updatedAt']
                })
                
                # 답글 수집
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        comments.append({
                            'comment_id': reply['id'],
                            'parent_id': item['id'],
                            'author_name': reply_snippet['authorDisplayName'],
                            'author_channel_id': reply_snippet.get('authorChannelId', {}).get('value'),
                            'text_display': reply_snippet['textDisplay'],
                            'text_original': reply_snippet['textOriginal'],
                            'like_count': reply_snippet['likeCount'],
                            'published_at': reply_snippet['publishedAt'],
                            'updated_at': reply_snippet['updatedAt']
                        })
            
            logger.info(f"영상 {video_id}에서 {len(comments)}개 댓글 수집")
            return comments
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"댓글 수집 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"댓글 수집 실패: {e}")
            return []
    
    def get_video_captions(self, video_id: str) -> List[Dict]:
        """영상 자막 정보 수집"""
        if not self.check_quota():
            return []
        
        try:
            captions_response = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()
            
            self.quota_used += 1
            
            captions = []
            for item in captions_response.get('items', []):
                snippet = item['snippet']
                captions.append({
                    'caption_id': item['id'],
                    'language': snippet.get('language'),
                    'name': snippet.get('name'),
                    'status': snippet.get('status'),
                    'track_kind': snippet.get('trackKind'),
                    'is_auto_synced': snippet.get('isAutoSynced'),
                    'is_cc': snippet.get('isCC'),
                    'is_draft': snippet.get('isDraft'),
                    'is_served': snippet.get('isServed'),
                    'is_auto_generated': snippet.get('isAutoGenerated'),
                    'last_updated': snippet.get('lastUpdated')
                })
            
            logger.info(f"영상 {video_id}에서 {len(captions)}개 자막 발견")
            return captions
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"자막 수집 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"자막 수집 실패: {e}")
            return []
    
    def get_channel_playlists(self, channel_id: str, max_results: int = 50) -> List[Dict]:
        """채널 재생목록 수집"""
        if not self.check_quota():
            return []
        
        try:
            playlists_response = self.youtube.playlists().list(
                part='snippet,contentDetails,status,localizations',
                channelId=channel_id,
                maxResults=max_results
            ).execute()
            
            self.quota_used += 1
            
            playlists = []
            for item in playlists_response.get('items', []):
                snippet = item['snippet']
                content_details = item.get('contentDetails', {})
                status = item.get('status', {})
                localizations = item.get('localizations', {})
                
                playlists.append({
                    'playlist_id': item['id'],
                    'title': snippet['title'],
                    'description': snippet.get('description'),
                    'thumbnails': snippet.get('thumbnails', {}),
                    'item_count': content_details.get('itemCount', 0),
                    'privacy_status': status.get('privacyStatus'),
                    'localizations': localizations,
                    'published_at': snippet.get('publishedAt')
                })
            
            logger.info(f"채널 {channel_id}에서 {len(playlists)}개 재생목록 발견")
            return playlists
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"재생목록 수집 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"재생목록 수집 실패: {e}")
            return []
    
    def get_playlist_items(self, playlist_id: str, max_results: int = 50) -> List[Dict]:
        """재생목록 아이템 수집"""
        if not self.check_quota():
            return []
        
        try:
            items_response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=max_results
            ).execute()
            
            self.quota_used += 1
            
            items = []
            for item in items_response.get('items', []):
                snippet = item['snippet']
                content_details = item.get('contentDetails', {})
                
                items.append({
                    'playlist_item_id': item['id'],
                    'video_id': content_details.get('videoId'),
                    'position': snippet.get('position'),
                    'title': snippet.get('title'),
                    'description': snippet.get('description'),
                    'thumbnails': snippet.get('thumbnails', {}),
                    'published_at': snippet.get('publishedAt')
                })
            
            logger.info(f"재생목록 {playlist_id}에서 {len(items)}개 아이템 발견")
            return items
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"재생목록 아이템 수집 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"재생목록 아이템 수집 실패: {e}")
            return []
    
    def get_video_categories(self, region_code: str = 'KR') -> List[Dict]:
        """영상 카테고리 수집"""
        if not self.check_quota():
            return []
        
        try:
            categories_response = self.youtube.videoCategories().list(
                part='snippet',
                regionCode=region_code
            ).execute()
            
            self.quota_used += 1
            
            categories = []
            for item in categories_response.get('items', []):
                snippet = item['snippet']
                categories.append({
                    'category_id': item['id'],
                    'title': snippet['title'],
                    'assignable': snippet.get('assignable', True),
                    'channel_id': snippet.get('channelId')
                })
            
            logger.info(f"영상 카테고리 {len(categories)}개 수집")
            return categories
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("YouTube API 할당량 초과")
            else:
                logger.error(f"영상 카테고리 수집 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"영상 카테고리 수집 실패: {e}")
            return []
    
    def save_to_database(self, video_data: Dict) -> bool:
        """데이터베이스에 저장"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # 채널 저장
                    channel_id = self.upsert_channel(cur, video_data['channel'])
                    
                    # 영상 저장
                    video_db_id = self.upsert_video(cur, video_data, channel_id)
                    
                    # 댓글 저장
                    for comment in video_data.get('comments', []):
                        self.upsert_comment(cur, comment, video_db_id)
                    
                    # 자막 저장
                    for caption in video_data.get('captions', []):
                        self.upsert_caption(cur, caption, video_db_id)
                    
                    # 채널 재생목록 수집 및 저장
                    channel_playlists = self.get_channel_playlists(video_data['channel']['channel_id'])
                    for playlist in channel_playlists:
                        playlist_db_id = self.upsert_playlist(cur, playlist, channel_id)
                        # 재생목록 아이템 수집 및 저장
                        playlist_items = self.get_playlist_items(playlist['playlist_id'])
                        for item in playlist_items:
                            self.upsert_playlist_item(cur, item, playlist_db_id)
                    
                    conn.commit()
                    logger.info(f"데이터베이스 저장 완료: {video_data['video_id']}")
                    return True
                    
        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            return False
    
    def upsert_channel(self, cur, channel_data: Dict) -> str:
        """채널 정보 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.channels (
                channel_yid, title, description, custom_url, country_code,
                thumbnails, statistics, tags, branding_settings, content_details,
                privacy_status, is_linked, long_uploads_status, made_for_kids,
                self_declared_made_for_kids, localizations, topic_categories,
                relevant_topic_ids, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (channel_yid) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                custom_url = EXCLUDED.custom_url,
                country_code = EXCLUDED.country_code,
                thumbnails = EXCLUDED.thumbnails,
                statistics = EXCLUDED.statistics,
                tags = EXCLUDED.tags,
                branding_settings = EXCLUDED.branding_settings,
                content_details = EXCLUDED.content_details,
                privacy_status = EXCLUDED.privacy_status,
                is_linked = EXCLUDED.is_linked,
                long_uploads_status = EXCLUDED.long_uploads_status,
                made_for_kids = EXCLUDED.made_for_kids,
                self_declared_made_for_kids = EXCLUDED.self_declared_made_for_kids,
                localizations = EXCLUDED.localizations,
                topic_categories = EXCLUDED.topic_categories,
                relevant_topic_ids = EXCLUDED.relevant_topic_ids,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id
        """, (
            channel_data['channel_id'],
            channel_data['title'],
            channel_data['description'],
            channel_data.get('custom_url'),
            channel_data.get('country'),
            json.dumps(channel_data.get('thumbnails', {})),
            json.dumps(channel_data.get('statistics', {})),
            channel_data.get('tags', []),
            json.dumps(channel_data.get('branding_settings', {})),
            json.dumps(channel_data.get('content_details', {})),
            channel_data.get('privacy_status'),
            channel_data.get('is_linked'),
            channel_data.get('long_uploads_status'),
            channel_data.get('made_for_kids'),
            channel_data.get('self_declared_made_for_kids'),
            json.dumps(channel_data.get('localizations', {})),
            channel_data.get('topic_categories', []),
            channel_data.get('relevant_topic_ids', []),
            json.dumps({})
        ))
        
        return cur.fetchone()[0]
    
    def upsert_video(self, cur, video_data: Dict, channel_id: str) -> str:
        """영상 정보 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.videos (
                video_yid, channel_id, title, description, published_at,
                duration, thumbnails, statistics, tags, category_id,
                default_language, content_rating, privacy_status, license,
                embeddable, public_stats_viewable, made_for_kids,
                self_declared_made_for_kids, recording_location, recording_date,
                localizations, topic_categories, relevant_topic_ids, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_yid) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                published_at = EXCLUDED.published_at,
                duration = EXCLUDED.duration,
                thumbnails = EXCLUDED.thumbnails,
                statistics = EXCLUDED.statistics,
                tags = EXCLUDED.tags,
                category_id = EXCLUDED.category_id,
                default_language = EXCLUDED.default_language,
                content_rating = EXCLUDED.content_rating,
                privacy_status = EXCLUDED.privacy_status,
                license = EXCLUDED.license,
                embeddable = EXCLUDED.embeddable,
                public_stats_viewable = EXCLUDED.public_stats_viewable,
                made_for_kids = EXCLUDED.made_for_kids,
                self_declared_made_for_kids = EXCLUDED.self_declared_made_for_kids,
                recording_location = EXCLUDED.recording_location,
                recording_date = EXCLUDED.recording_date,
                localizations = EXCLUDED.localizations,
                topic_categories = EXCLUDED.topic_categories,
                relevant_topic_ids = EXCLUDED.relevant_topic_ids,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id
        """, (
            video_data['video_id'],
            channel_id,
            video_data['title'],
            video_data['description'],
            video_data['published_at'],
            video_data.get('duration'),
            json.dumps(video_data.get('thumbnails', {})),
            json.dumps(video_data.get('statistics', {})),
            video_data.get('tags', []),
            video_data.get('category_id'),
            video_data.get('default_language'),
            video_data.get('content_rating'),
            video_data.get('privacy_status'),
            video_data.get('license'),
            video_data.get('embeddable'),
            video_data.get('public_stats_viewable'),
            video_data.get('made_for_kids'),
            video_data.get('self_declared_made_for_kids'),
            json.dumps(video_data.get('recording_location', {})),
            video_data.get('recording_date'),
            json.dumps(video_data.get('localizations', {})),
            video_data.get('topic_categories', []),
            video_data.get('relevant_topic_ids', []),
            json.dumps({})
        ))
        
        return cur.fetchone()[0]
    
    def upsert_comment(self, cur, comment_data: Dict, video_id: str) -> None:
        """댓글 정보 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.comments (
                video_id, comment_yid, parent_id, author_name, author_channel_id,
                text_display, text_original, like_count, published_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (comment_yid) DO UPDATE SET
                text_display = EXCLUDED.text_display,
                text_original = EXCLUDED.text_original,
                like_count = EXCLUDED.like_count,
                updated_at = EXCLUDED.updated_at
        """, (
            video_id,
            comment_data['comment_id'],
            comment_data.get('parent_id'),
            comment_data['author_name'],
            comment_data.get('author_channel_id'),
            comment_data['text_display'],
            comment_data['text_original'],
            comment_data['like_count'],
            comment_data['published_at'],
            comment_data['updated_at']
        ))
    
    def upsert_caption(self, cur, caption_data: Dict, video_id: str) -> None:
        """자막 정보 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.captions (
                video_id, caption_yid, language, name, status, track_kind,
                is_auto_synced, is_cc, is_draft, is_served, is_auto_generated,
                last_updated, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (caption_yid) DO UPDATE SET
                language = EXCLUDED.language,
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                track_kind = EXCLUDED.track_kind,
                is_auto_synced = EXCLUDED.is_auto_synced,
                is_cc = EXCLUDED.is_cc,
                is_draft = EXCLUDED.is_draft,
                is_served = EXCLUDED.is_served,
                is_auto_generated = EXCLUDED.is_auto_generated,
                last_updated = EXCLUDED.last_updated,
                metadata = EXCLUDED.metadata
        """, (
            video_id,
            caption_data['caption_id'],
            caption_data.get('language'),
            caption_data.get('name'),
            caption_data.get('status'),
            caption_data.get('track_kind'),
            caption_data.get('is_auto_synced'),
            caption_data.get('is_cc'),
            caption_data.get('is_draft'),
            caption_data.get('is_served'),
            caption_data.get('is_auto_generated'),
            caption_data.get('last_updated'),
            json.dumps({})
        ))
    
    def upsert_playlist(self, cur, playlist_data: Dict, channel_id: str) -> str:
        """재생목록 정보 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.playlists (
                playlist_yid, channel_id, title, description, thumbnails,
                item_count, privacy_status, localizations, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (playlist_yid) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                thumbnails = EXCLUDED.thumbnails,
                item_count = EXCLUDED.item_count,
                privacy_status = EXCLUDED.privacy_status,
                localizations = EXCLUDED.localizations,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id
        """, (
            playlist_data['playlist_id'],
            channel_id,
            playlist_data['title'],
            playlist_data.get('description'),
            json.dumps(playlist_data.get('thumbnails', {})),
            playlist_data.get('item_count', 0),
            playlist_data.get('privacy_status'),
            json.dumps(playlist_data.get('localizations', {})),
            json.dumps({})
        ))
        
        return cur.fetchone()[0]
    
    def upsert_playlist_item(self, cur, item_data: Dict, playlist_id: str) -> None:
        """재생목록 아이템 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.playlist_items (
                playlist_id, playlist_item_yid, position, title, description,
                thumbnails, published_at, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (playlist_id, playlist_item_yid) DO UPDATE SET
                position = EXCLUDED.position,
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                thumbnails = EXCLUDED.thumbnails,
                published_at = EXCLUDED.published_at,
                metadata = EXCLUDED.metadata
        """, (
            playlist_id,
            item_data['playlist_item_id'],
            item_data.get('position'),
            item_data.get('title'),
            item_data.get('description'),
            json.dumps(item_data.get('thumbnails', {})),
            item_data.get('published_at'),
            json.dumps({})
        ))
    
    def upsert_video_category(self, cur, category_data: Dict) -> None:
        """영상 카테고리 저장/업데이트"""
        cur.execute("""
            INSERT INTO yt2.video_categories (
                category_yid, title, assignable, channel_id, metadata
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (category_yid) DO UPDATE SET
                title = EXCLUDED.title,
                assignable = EXCLUDED.assignable,
                channel_id = EXCLUDED.channel_id,
                metadata = EXCLUDED.metadata
        """, (
            category_data['category_id'],
            category_data['title'],
            category_data.get('assignable', True),
            category_data.get('channel_id'),
            json.dumps({})
        ))
    
    def index_to_opensearch(self, video_data: Dict) -> bool:
        """OpenSearch에 인덱싱"""
        try:
            doc = {
                'video_id': video_data['video_id'],
                'title': video_data['title'],
                'description': video_data['description'],
                'published_at': video_data['published_at'],
                'channel_id': video_data['channel']['channel_id'],
                'channel_title': video_data['channel']['title'],
                'tags': video_data.get('tags', []),
                'statistics': video_data.get('statistics', {}),
                'created_at': datetime.now().isoformat()
            }
            
            self.os_client.index(
                index='videos',
                id=video_data['video_id'],
                body=doc
            )
            
            logger.info(f"OpenSearch 인덱싱 완료: {video_data['video_id']}")
            return True
            
        except Exception as e:
            logger.error(f"OpenSearch 인덱싱 실패: {e}")
            return False
    
    def crawl_all(self, max_results_per_keyword: int = 50, days: int = 30) -> Dict:
        """전체 크롤링 실행"""
        logger.info("YT2 크롤링 시작")
        
        total_videos = 0
        total_comments = 0
        successful_saves = 0
        
        # 영상 카테고리 수집
        logger.info("영상 카테고리 수집 중...")
        categories = self.get_video_categories()
        if categories:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    for category in categories:
                        self.upsert_video_category(cur, category)
                    conn.commit()
            logger.info(f"영상 카테고리 {len(categories)}개 저장 완료")
        
        for keyword in self.keywords:
            logger.info(f"키워드 크롤링: {keyword}")
            
            videos = self.search_videos(keyword, max_results_per_keyword, days)
            
            for video in videos:
                # 데이터베이스 저장
                if self.save_to_database(video):
                    successful_saves += 1
                
                # OpenSearch 인덱싱
                self.index_to_opensearch(video)
                
                total_videos += 1
                total_comments += len(video.get('comments', []))
                
                # API 할당량 확인
                if not self.check_quota():
                    logger.warning("API 할당량 초과로 크롤링 중단")
                    break
            
            # 키워드 간 대기
            time.sleep(1)
        
        result = {
            'total_videos': total_videos,
            'total_comments': total_comments,
            'successful_saves': successful_saves,
            'quota_used': self.quota_used
        }
        
        logger.info(f"크롤링 완료: {result}")
        return result

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YT2 YouTube 크롤러')
    parser.add_argument('--keywords', nargs='+', help='검색할 키워드 목록')
    parser.add_argument('--max-results', type=int, default=50, help='키워드당 최대 결과 수')
    parser.add_argument('--days', type=int, default=30, help='검색할 일수')
    parser.add_argument('--dry-run', action='store_true', help='실제 크롤링 없이 테스트만 실행')
    
    args = parser.parse_args()
    
    try:
        crawler = YT2Crawler()
        
        if args.dry_run:
            logger.info("=== DRY RUN 모드 ===")
            keywords = args.keywords or crawler.keywords[:5]  # 테스트용으로 5개만
            logger.info(f"키워드: {keywords}")
            logger.info(f"키워드당 최대 결과: {args.max_results}")
            logger.info("실제 크롤링은 수행하지 않습니다.")
            return
        
        # 크롤링 실행
        if args.keywords:
            crawler.keywords = args.keywords
        
        result = crawler.crawl_all(args.max_results, args.days)
        
        logger.info("=== 크롤링 결과 ===")
        logger.info(f"총 영상 수: {result['total_videos']}")
        logger.info(f"총 댓글 수: {result['total_comments']}")
        logger.info(f"성공적으로 저장된 영상: {result['successful_saves']}")
        logger.info(f"사용된 API 할당량: {result['quota_used']}")
        
    except Exception as e:
        logger.error(f"크롤링 실패: {e}")
        raise

if __name__ == "__main__":
    main()
