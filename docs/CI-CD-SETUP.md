# 🚀 CI/CD 설정 가이드

YT2 Search System의 CI/CD 파이프라인 설정 및 사용 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [워크플로우 구성](#워크플로우-구성)
- [GitHub Secrets 설정](#github-secrets-설정)
- [배포 방법](#배포-방법)
- [모니터링](#모니터링)
- [문제 해결](#문제-해결)

## 🎯 개요

이 프로젝트는 GitHub Actions를 사용하여 다음과 같은 CI/CD 기능을 제공합니다:

- **코드 품질 검사**: Black, isort, Flake8, MyPy
- **보안 스캔**: Safety, Bandit, Semgrep, TruffleHog
- **Docker 빌드**: 멀티 서비스 컨테이너 빌드
- **통합 테스트**: PostgreSQL, Redis를 사용한 실제 테스트
- **자동 배포**: 프로덕션 환경 자동 배포

## 🔧 워크플로우 구성

### 1. 메인 CI/CD 파이프라인 (`.github/workflows/ci-cd.yml`)

```yaml
# 트리거 조건
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

# 작업 단계
jobs:
  - code-quality      # 코드 품질 검사
  - docker-build      # Docker 이미지 빌드
  - security-scan     # 보안 스캔
  - integration-test  # 통합 테스트
  - deploy           # 프로덕션 배포
  - performance-test # 성능 테스트
```

### 2. 개발 환경 파이프라인 (`.github/workflows/dev.yml`)

```yaml
# 트리거 조건
on:
  push:
    branches: [ develop, feature/* ]
  pull_request:
    branches: [ develop ]

# 작업 단계
jobs:
  - quick-check    # 빠른 코드 검사
  - dev-build      # 개발용 Docker 빌드
  - pr-review      # PR 자동 리뷰
```

### 3. 보안 스캔 파이프라인 (`.github/workflows/security.yml`)

```yaml
# 트리거 조건
on:
  schedule:
    - cron: '0 2 * * 1'  # 매주 월요일 오전 2시
  push:
    branches: [ main ]
  workflow_dispatch:

# 작업 단계
jobs:
  - security-scan     # 종합 보안 스캔
  - secret-scan       # 시크릿 스캔
  - container-security # 컨테이너 보안
  - security-report   # 보안 리포트 생성
```

## 🔐 GitHub Secrets 설정

다음 환경 변수들을 GitHub Repository > Settings > Secrets and variables > Actions에서 설정하세요:

### 필수 Secrets

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `DB_PASSWORD` | PostgreSQL 비밀번호 | `your_secure_password_here` |
| `OS_PASSWORD` | OpenSearch 비밀번호 | `your_opensearch_password_here` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | `AIzaSy...` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` |

### 선택적 Secrets

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `GRAFANA_PASSWORD` | Grafana 관리자 비밀번호 | `your_grafana_password_here` |

### 설정 방법

1. GitHub 저장소로 이동
2. **Settings** 탭 클릭
3. **Secrets and variables** > **Actions** 클릭
4. **New repository secret** 클릭
5. 이름과 값을 입력하고 **Add secret** 클릭

## 🚀 배포 방법

### 1. 자동 배포 (권장)

```bash
# main 브랜치에 푸시하면 자동으로 배포됩니다
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main
```

### 2. 수동 배포

```bash
# GitHub Actions에서 수동 실행
# Repository > Actions > CI/CD Pipeline > Run workflow
```

### 3. 로컬 배포

#### Linux/macOS
```bash
# 개발 환경
./scripts/deploy.sh dev

# 프로덕션 환경
./scripts/deploy.sh prod
```

#### Windows
```powershell
# 개발 환경
.\scripts\deploy.ps1 -Environment dev

# 프로덕션 환경
.\scripts\deploy.ps1 -Environment prod
```

## 📊 모니터링

### 1. GitHub Actions 대시보드

- **Repository** > **Actions** 탭에서 워크플로우 실행 상태 확인
- 각 단계별 로그 및 결과 확인
- 실패 시 자동 알림 (이메일 설정 필요)

### 2. 서비스 상태 확인

```bash
# API 서버 상태
curl http://localhost:8000/health

# 프론트엔드 상태
curl http://localhost:3000

# Docker 컨테이너 상태
docker-compose ps
```

### 3. 로그 모니터링

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f api
docker-compose logs -f crawler
docker-compose logs -f frontend
```

## 🔧 문제 해결

### 1. 빌드 실패

**문제**: Docker 이미지 빌드 실패
**해결책**:
```bash
# 로컬에서 빌드 테스트
docker build -f Dockerfile.base -t yt2-base:test .
docker build -f api/Dockerfile -t yt2-api:test .
```

### 2. 테스트 실패

**문제**: 통합 테스트 실패
**해결책**:
```bash
# 로컬에서 테스트 실행
python test_integration.py
```

### 3. 보안 스캔 실패

**문제**: 보안 스캔에서 취약점 발견
**해결책**:
1. GitHub Actions 로그에서 상세 정보 확인
2. 취약점 수정 후 재커밋
3. 필요시 보안 스캔 결과를 검토하여 허용

### 4. 배포 실패

**문제**: 프로덕션 배포 실패
**해결책**:
1. GitHub Secrets 확인
2. Docker 이미지 빌드 상태 확인
3. 네트워크 연결 상태 확인

## 📈 성능 최적화

### 1. 빌드 시간 단축

- **캐시 활용**: Docker layer 캐싱 사용
- **병렬 빌드**: matrix strategy로 여러 서비스 동시 빌드
- **선택적 빌드**: 변경된 서비스만 빌드

### 2. 테스트 최적화

- **단계별 테스트**: 빠른 테스트를 먼저 실행
- **병렬 실행**: 독립적인 테스트 병렬 실행
- **캐시 활용**: 의존성 설치 캐싱

### 3. 보안 스캔 최적화

- **스케줄링**: 정기적 스캔으로 부하 분산
- **선택적 스캔**: 변경된 파일만 스캔
- **결과 캐싱**: 중복 스캔 방지

## 🎯 다음 단계

1. **모니터링 도구 추가**: Prometheus, Grafana 연동
2. **알림 시스템**: Slack, Discord 알림 연동
3. **자동 롤백**: 배포 실패 시 자동 롤백
4. **다중 환경**: staging, production 환경 분리
5. **성능 테스트**: 부하 테스트 자동화

## 📚 참고 자료

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Python 보안 도구](https://python-security.readthedocs.io/)
- [CI/CD 모범 사례](https://docs.github.com/en/actions/learn-github-actions)
