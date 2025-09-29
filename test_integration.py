#!/usr/bin/env python3
"""
YT2 통합 테스트 스크립트
업그레이드된 시스템의 전체 기능을 테스트합니다.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로딩
load_dotenv()

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """API 헬스 체크 테스트"""
    print("🔍 API 헬스 체크 테스트...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API 헬스 체크 성공: {health_data}")
            return True
        else:
            print(f"❌ API 헬스 체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 헬스 체크 오류: {e}")
        return False

def test_api_stats():
    """API 통계 조회 테스트"""
    print("📊 API 통계 조회 테스트...")
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
            print(f"✅ 통계 조회 성공:")
            print(f"   - 총 채널 수: {stats_data.get('total_channels', 0)}")
            print(f"   - 총 영상 수: {stats_data.get('total_videos', 0)}")
            print(f"   - 총 댓글 수: {stats_data.get('total_comments', 0)}")
            print(f"   - 총 임베딩 수: {stats_data.get('total_embeddings', 0)}")
            print(f"   - 최근 24시간 영상: {stats_data.get('videos_last_24h', 0)}")
            print(f"   - 최근 7일 영상: {stats_data.get('videos_last_7d', 0)}")
            return True
        else:
            print(f"❌ 통계 조회 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 통계 조회 오류: {e}")
        return False

def test_search_api():
    """검색 API 테스트"""
    print("🔍 검색 API 테스트...")
    try:
        # 수원시 행궁동 관련 검색어로 테스트
        test_queries = ["수원 행궁", "수원시 행궁동", "화성행궁"]
        
        for query in test_queries:
            print(f"   검색어: '{query}'")
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"q": query, "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                search_data = response.json()
                print(f"   ✅ 검색 성공: {search_data['total_count']}개 결과")
                
                # 첫 번째 결과의 새로운 필드들 확인
                if search_data['videos']:
                    video = search_data['videos'][0]
                    print(f"   📹 영상 정보:")
                    print(f"      - 제목: {video['title']}")
                    print(f"      - 채널: {video['channel_name']}")
                    print(f"      - 공개 상태: {video.get('privacy_status', 'N/A')}")
                    print(f"      - 라이선스: {video.get('license', 'N/A')}")
                    print(f"      - 임베드 가능: {video.get('embeddable', 'N/A')}")
                    print(f"      - 어린이 대상: {video.get('made_for_kids', 'N/A')}")
                    print(f"      - 주제 카테고리: {video.get('topic_categories', [])}")
                    print(f"      - 관련 주제 ID: {video.get('relevant_topic_ids', [])}")
            else:
                print(f"   ❌ 검색 실패: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 검색 API 오류: {e}")
        return False

def test_new_endpoints():
    """새로운 엔드포인트 테스트"""
    print("🆕 새로운 엔드포인트 테스트...")
    
    endpoints = [
        ("/categories", "영상 카테고리"),
        ("/playlists", "재생목록 목록"),
        ("/channels", "채널 목록")
    ]
    
    for endpoint, description in endpoints:
        try:
            print(f"   {description} 테스트...")
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {description} 성공: {len(data) if isinstance(data, list) else 'OK'}")
            else:
                print(f"   ❌ {description} 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ {description} 오류: {e}")
            return False
    
    return True

def test_crawler_dry_run():
    """크롤러 드라이런 테스트"""
    print("🕷️ 크롤러 드라이런 테스트...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "crawler/crawler.py", "--dry-run", "--max-results", "2"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 크롤러 드라이런 성공")
            print("   출력:")
            for line in result.stdout.split('\n')[-10:]:  # 마지막 10줄만
                if line.strip():
                    print(f"   {line}")
            return True
        else:
            print(f"❌ 크롤러 드라이런 실패: {result.returncode}")
            print(f"   오류: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 크롤러 드라이런 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 YT2 통합 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("API 헬스 체크", test_api_health),
        ("API 통계 조회", test_api_stats),
        ("검색 API", test_search_api),
        ("새로운 엔드포인트", test_new_endpoints),
        ("크롤러 드라이런", test_crawler_dry_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 통과")
            else:
                print(f"❌ {test_name} 실패")
        except Exception as e:
            print(f"❌ {test_name} 오류: {e}")
        
        time.sleep(1)  # 테스트 간 간격
    
    print("\n" + "=" * 50)
    print(f"🎯 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
