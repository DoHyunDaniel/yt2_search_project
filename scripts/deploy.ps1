# =============================================================================
# 🚀 YT2 Search System 배포 스크립트 (PowerShell)
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod", "default")]
    [string]$Environment = "default"
)

# 색상 정의
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

# 로그 함수
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
    exit 1
}

# 환경 확인
function Test-Environment {
    Write-Log "🔍 환경 확인 중..."
    
    # Docker 확인
    try {
        docker --version | Out-Null
    } catch {
        Write-Error "Docker가 설치되지 않았습니다."
    }
    
    # Docker Compose 확인
    try {
        docker-compose --version | Out-Null
    } catch {
        Write-Error "Docker Compose가 설치되지 않았습니다."
    }
    
    # .env 파일 확인
    if (-not (Test-Path ".env")) {
        Write-Warning ".env 파일이 없습니다. env.example을 복사하여 생성합니다."
        Copy-Item "env.example" ".env"
        Write-Warning "⚠️  .env 파일을 수정한 후 다시 실행하세요."
        exit 1
    }
    
    Write-Success "환경 확인 완료"
}

# 이전 컨테이너 정리
function Clear-Containers {
    Write-Log "🧹 이전 컨테이너 정리 중..."
    
    # 실행 중인 컨테이너 중지
    try {
        docker-compose down --remove-orphans 2>$null
    } catch {
        # 무시
    }
    
    # 사용하지 않는 이미지 정리
    docker image prune -f
    
    Write-Success "정리 완료"
}

# 이미지 빌드
function Build-Images {
    Write-Log "🏗️  Docker 이미지 빌드 중..."
    
    # 베이스 이미지 빌드
    Write-Log "베이스 이미지 빌드 중..."
    docker build -f Dockerfile.base -t yt2-base:latest .
    
    # 서비스별 이미지 빌드
    Write-Log "API 서버 이미지 빌드 중..."
    docker build -f api/Dockerfile -t yt2-api:latest .
    
    Write-Log "크롤러 이미지 빌드 중..."
    docker build -f crawler/Dockerfile -t yt2-crawler:latest .
    
    Write-Log "프론트엔드 이미지 빌드 중..."
    docker build -f frontend/Dockerfile -t yt2-frontend:latest .
    
    Write-Success "이미지 빌드 완료"
}

# 서비스 시작
function Start-Services {
    param([string]$Env)
    
    Write-Log "🚀 서비스 시작 중..."
    
    # 개발 환경
    if ($Env -eq "dev") {
        Write-Log "개발 환경으로 시작합니다..."
        docker-compose up -d
    }
    # 프로덕션 환경
    elseif ($Env -eq "prod") {
        Write-Log "프로덕션 환경으로 시작합니다..."
        docker-compose -f docker-compose.prod.yml up -d
    }
    # 기본 환경
    else {
        Write-Log "기본 환경으로 시작합니다..."
        docker-compose up -d
    }
    
    Write-Success "서비스 시작 완료"
}

# 헬스 체크
function Test-Health {
    Write-Log "🏥 서비스 상태 확인 중..."
    
    # API 서버 확인
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "API 서버가 정상적으로 시작되었습니다."
                break
            }
        } catch {
            # 무시
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Error "API 서버가 시작되지 않았습니다."
        }
        
        Write-Log "시도 $attempt/$maxAttempts - 10초 후 재시도..."
        Start-Sleep -Seconds 10
        $attempt++
    }
    
    # 프론트엔드 확인
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "프론트엔드가 정상적으로 시작되었습니다."
        }
    } catch {
        Write-Warning "프론트엔드가 아직 시작되지 않았습니다."
    }
}

# 로그 표시
function Show-Logs {
    Write-Log "📋 서비스 로그를 표시합니다. (Ctrl+C로 종료)"
    docker-compose logs -f
}

# 메인 함수
function Main {
    Write-Host "🚀 YT2 Search System 배포 스크립트" -ForegroundColor $Blue
    Write-Host "==================================" -ForegroundColor $Blue
    
    # 환경 확인
    Test-Environment
    
    # 이전 컨테이너 정리
    Clear-Containers
    
    # 이미지 빌드
    Build-Images
    
    # 서비스 시작
    Start-Services -Env $Environment
    
    # 헬스 체크
    Test-Health
    
    # 성공 메시지
    Write-Host ""
    Write-Success "🎉 배포가 완료되었습니다!"
    Write-Host ""
    Write-Host "📱 접속 정보:" -ForegroundColor $Blue
    Write-Host "  - API 서버: http://localhost:8000" -ForegroundColor $Green
    Write-Host "  - 프론트엔드: http://localhost:3000" -ForegroundColor $Green
    Write-Host "  - API 문서: http://localhost:8000/docs" -ForegroundColor $Green
    Write-Host ""
    Write-Host "🔧 관리 명령어:" -ForegroundColor $Blue
    Write-Host "  - 로그 확인: docker-compose logs -f" -ForegroundColor $Yellow
    Write-Host "  - 서비스 중지: docker-compose down" -ForegroundColor $Yellow
    Write-Host "  - 서비스 재시작: docker-compose restart" -ForegroundColor $Yellow
    Write-Host ""
    
    # 로그 표시 옵션
    $showLogs = Read-Host "로그를 표시하시겠습니까? (y/N)"
    if ($showLogs -eq "y" -or $showLogs -eq "Y") {
        Show-Logs
    }
}

# 스크립트 실행
Main
