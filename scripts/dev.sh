#!/bin/bash

# 개발 환경 실행 스크립트

set -e

echo "🛠️ YT2 개발 환경 시작..."

# 환경 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일이 없습니다. .env.example을 복사합니다..."
    cp .env.example .env
fi

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker-compose build

# 개발 서비스 시작
echo "🚀 개발 서비스 시작 중..."
docker-compose up -d

# 헬스 체크
echo "🔍 서비스 상태 확인 중..."
sleep 15

# API 헬스 체크
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API 서버 정상 작동"
else
    echo "❌ API 서버 연결 실패"
    exit 1
fi

# 프론트엔드 헬스 체크
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 프론트엔드 서버 정상 작동"
else
    echo "❌ 프론트엔드 서버 연결 실패"
    exit 1
fi

echo "🎉 개발 환경 준비 완료!"
echo "📱 프론트엔드: http://localhost:3000"
echo "🔧 API 서버: http://localhost:8000"
echo "📊 OpenSearch: http://localhost:5601"
echo ""
echo "💡 개발 팁:"
echo "   - 프론트엔드 코드 변경 시 자동으로 리로드됩니다"
echo "   - API 서버 로그: docker-compose logs -f api"
echo "   - 프론트엔드 로그: docker-compose logs -f frontend"
