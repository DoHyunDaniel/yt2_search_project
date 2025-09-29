#!/bin/bash

# YT2 프로젝트 빌드 스크립트
echo "🚀 YT2 프로젝트 빌드 시작..."

# 1. 공통 베이스 이미지 빌드
echo "📦 공통 베이스 이미지 빌드 중..."
docker build -f Dockerfile.base -t yt2-base:latest .

if [ $? -eq 0 ]; then
    echo "✅ 베이스 이미지 빌드 완료"
else
    echo "❌ 베이스 이미지 빌드 실패"
    exit 1
fi

# 2. 전체 서비스 빌드
echo "🔨 전체 서비스 빌드 중..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ 전체 서비스 빌드 완료"
else
    echo "❌ 전체 서비스 빌드 실패"
    exit 1
fi

echo "🎉 빌드 완료! 'docker-compose up' 명령으로 실행하세요."
