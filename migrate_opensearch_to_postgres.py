#!/usr/bin/env python3
"""
OpenSearch에서 PostgreSQL로 데이터 마이그레이션 스크립트
"""

import os
import json
import psycopg2
import psycopg2.extras
from opensearchpy import OpenSearch
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'yt2-pg',
    'port': 5432,
    'dbname': 'yt2',
    'user': 'app',
    'password': 'app1234',
}

# OpenSearch 클라이언트
OS_CLIENT = OpenSearch(
    hosts=['http://yt2-opensearch:9200'],
    use_ssl=False,
    verify_certs=False
)

def get_opensearch_data():
    """OpenSearch에서 모든 데이터 가져오기"""
    try:
        # OpenSearch에서 모든 비디오 데이터 가져오기
        response = OS_CLIENT.search(
            index='videos',
            body={
                'query': {'match_all': {}},
                'size': 1000  # 모든 데이터 가져오기
            }
        )
        
        if response['hits']['total']['value'] > 0:
            return [hit['_source'] for hit in response['hits']['hits']]
        else:
            logger.warning("OpenSearch에 데이터가 없습니다.")
            return []
            
    except Exception as e:
        logger.error(f"OpenSearch 데이터 조회 실패: {e}")
        return []

def migrate_to_postgres(data_list):
    """PostgreSQL에 데이터 마이그레이션"""
    success_count = 0
    error_count = 0
    
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                for i, data in enumerate(data_list):
                    try:
                        # 채널 데이터 먼저 저장
                        channel_id = save_channel(cur, data)
                        
                        # 비디오 데이터 저장
                        video_id = save_video(cur, data, channel_id)
                        
                        success_count += 1
                        logger.info(f"[{i+1}/{len(data_list)}] 데이터 마이그레이션 완료: video_id={data['video_id']}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"[{i+1}/{len(data_list)}] 데이터 마이그레이션 실패: video_id={data['video_id']}, 오류: {e}")
                        continue
                
                conn.commit()
                logger.info(f"마이그레이션 완료: 성공 {success_count}개, 실패 {error_count}개")
                return success_count > 0
                
    except Exception as e:
        logger.error(f"PostgreSQL 연결 실패: {e}")
        logger.error(f"오류 타입: {type(e).__name__}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return False

def save_channel(cur, data):
    """채널 데이터 저장"""
    try:
        # 채널이 이미 존재하는지 확인
        cur.execute(
            "SELECT id FROM yt2.channels WHERE channel_yid = %s",
            (data['channel_id'],)
        )
        existing_channel = cur.fetchone()
        
        if existing_channel:
            logger.info(f"채널 이미 존재: {data['channel_id']}")
            return existing_channel[0]
        
        # 새 채널 저장
        cur.execute("""
            INSERT INTO yt2.channels (
                channel_yid, title, platform, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            data['channel_id'],
            data['channel_title'],
            'youtube',
            datetime.now(),
            datetime.now()
        ))
        
        channel_id = cur.fetchone()[0]
        logger.info(f"새 채널 저장: {data['channel_id']}")
        return channel_id
        
    except Exception as e:
        logger.error(f"채널 저장 실패: {e}")
        raise

def save_video(cur, data, channel_id):
    """비디오 데이터 저장"""
    try:
        # 비디오가 이미 존재하는지 확인
        cur.execute(
            "SELECT id FROM yt2.videos WHERE video_yid = %s",
            (data['video_id'],)
        )
        existing_video = cur.fetchone()
        
        if existing_video:
            logger.info(f"비디오 이미 존재: {data['video_id']}")
            return existing_video[0]
        
        # 새 비디오 저장
        cur.execute("""
            INSERT INTO yt2.videos (
                video_yid, channel_id, title, description, published_at,
                statistics, platform, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            data['video_id'],
            channel_id,
            data['title'],
            data['description'],
            data['published_at'],
            json.dumps(data['statistics']),
            'youtube',
            datetime.now(),
            datetime.now()
        ))
        
        video_id = cur.fetchone()[0]
        logger.info(f"새 비디오 저장: {data['video_id']}")
        return video_id
        
    except Exception as e:
        logger.error(f"비디오 저장 실패: {e}")
        raise

def main():
    """메인 함수"""
    logger.info("OpenSearch → PostgreSQL 전체 마이그레이션 시작")
    
    # OpenSearch에서 데이터 가져오기
    data_list = get_opensearch_data()
    if not data_list:
        logger.error("마이그레이션할 데이터가 없습니다.")
        return
    
    logger.info(f"마이그레이션할 데이터: {len(data_list)}개")
    
    # PostgreSQL에 마이그레이션
    success = migrate_to_postgres(data_list)
    
    if success:
        logger.info("전체 마이그레이션 성공!")
    else:
        logger.error("마이그레이션 실패!")

if __name__ == "__main__":
    main()
