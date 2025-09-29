# YT2 프로젝트 빌드 스크립트
Write-Host "🚀 YT2 프로젝트 빌드 시작..." -ForegroundColor Green

# 1. 공통 베이스 이미지 빌드
Write-Host "📦 공통 베이스 이미지 빌드 중..." -ForegroundColor Yellow
docker build -f Dockerfile.base -t yt2-base:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 베이스 이미지 빌드 완료" -ForegroundColor Green
} else {
    Write-Host "❌ 베이스 이미지 빌드 실패" -ForegroundColor Red
    exit 1
}

# 2. 전체 서비스 빌드
Write-Host "🔨 전체 서비스 빌드 중..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 전체 서비스 빌드 완료" -ForegroundColor Green
} else {
    Write-Host "❌ 전체 서비스 빌드 실패" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 빌드 완료! 'docker-compose up' 명령으로 실행하세요." -ForegroundColor Green
