#!/bin/bash

# 프로덕션 배포 스크립트

set -e

echo "🚀 YT2 프로덕션 배포 시작..."

# 환경 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. .env.example을 참고하여 .env 파일을 생성해주세요."
    exit 1
fi

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker-compose build --no-cache

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down

# 프로덕션 서비스 시작
echo "🚀 프로덕션 서비스 시작 중..."
docker-compose --profile production up -d

# 헬스 체크
echo "🔍 서비스 상태 확인 중..."
sleep 10

# API 헬스 체크
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API 서버 정상 작동"
else
    echo "❌ API 서버 연결 실패"
    exit 1
fi

# 프론트엔드 헬스 체크
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ 프론트엔드 서버 정상 작동"
else
    echo "❌ 프론트엔드 서버 연결 실패"
    exit 1
fi

echo "🎉 배포 완료!"
echo "📱 프론트엔드: http://localhost:80"
echo "🔧 API 서버: http://localhost:8000"
echo "📊 OpenSearch: http://localhost:5601"
