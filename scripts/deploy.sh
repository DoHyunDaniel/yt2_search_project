#!/bin/bash

# =============================================================================
# 🚀 YT2 Search System 배포 스크립트
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# 환경 확인
check_environment() {
    log "🔍 환경 확인 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        error "Docker가 설치되지 않았습니다."
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose가 설치되지 않았습니다."
    fi
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        warning ".env 파일이 없습니다. env.example을 복사하여 생성합니다."
        cp env.example .env
        warning "⚠️  .env 파일을 수정한 후 다시 실행하세요."
        exit 1
    fi
    
    success "환경 확인 완료"
}

# 이전 컨테이너 정리
cleanup() {
    log "🧹 이전 컨테이너 정리 중..."
    
    # 실행 중인 컨테이너 중지
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 사용하지 않는 이미지 정리
    docker image prune -f
    
    success "정리 완료"
}

# 이미지 빌드
build_images() {
    log "🏗️  Docker 이미지 빌드 중..."
    
    # 베이스 이미지 빌드
    log "베이스 이미지 빌드 중..."
    docker build -f Dockerfile.base -t yt2-base:latest .
    
    # 서비스별 이미지 빌드
    log "API 서버 이미지 빌드 중..."
    docker build -f api/Dockerfile -t yt2-api:latest .
    
    log "크롤러 이미지 빌드 중..."
    docker build -f crawler/Dockerfile -t yt2-crawler:latest .
    
    log "프론트엔드 이미지 빌드 중..."
    docker build -f frontend/Dockerfile -t yt2-frontend:latest .
    
    success "이미지 빌드 완료"
}

# 서비스 시작
start_services() {
    log "🚀 서비스 시작 중..."
    
    # 개발 환경
    if [ "$1" = "dev" ]; then
        log "개발 환경으로 시작합니다..."
        docker-compose up -d
    # 프로덕션 환경
    elif [ "$1" = "prod" ]; then
        log "프로덕션 환경으로 시작합니다..."
        docker-compose -f docker-compose.prod.yml up -d
    else
        log "기본 환경으로 시작합니다..."
        docker-compose up -d
    fi
    
    success "서비스 시작 완료"
}

# 헬스 체크
health_check() {
    log "🏥 서비스 상태 확인 중..."
    
    # API 서버 확인
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            success "API 서버가 정상적으로 시작되었습니다."
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "API 서버가 시작되지 않았습니다."
        fi
        
        log "시도 $attempt/$max_attempts - 10초 후 재시도..."
        sleep 10
        ((attempt++))
    done
    
    # 프론트엔드 확인
    if curl -f http://localhost:3000 &>/dev/null; then
        success "프론트엔드가 정상적으로 시작되었습니다."
    else
        warning "프론트엔드가 아직 시작되지 않았습니다."
    fi
}

# 로그 표시
show_logs() {
    log "📋 서비스 로그를 표시합니다. (Ctrl+C로 종료)"
    docker-compose logs -f
}

# 메인 함수
main() {
    echo "🚀 YT2 Search System 배포 스크립트"
    echo "=================================="
    
    # 환경 확인
    check_environment
    
    # 이전 컨테이너 정리
    cleanup
    
    # 이미지 빌드
    build_images
    
    # 서비스 시작
    start_services "$1"
    
    # 헬스 체크
    health_check
    
    # 성공 메시지
    echo ""
    success "🎉 배포가 완료되었습니다!"
    echo ""
    echo "📱 접속 정보:"
    echo "  - API 서버: http://localhost:8000"
    echo "  - 프론트엔드: http://localhost:3000"
    echo "  - API 문서: http://localhost:8000/docs"
    echo ""
    echo "🔧 관리 명령어:"
    echo "  - 로그 확인: docker-compose logs -f"
    echo "  - 서비스 중지: docker-compose down"
    echo "  - 서비스 재시작: docker-compose restart"
    echo ""
    
    # 로그 표시 옵션
    read -p "로그를 표시하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# 스크립트 실행
main "$@"