# 🔍 YT2 - 행궁 검색 시스템

수원시 행궁동 관련 YouTube 데이터를 수집하고 다양한 검색 알고리즘으로 검색하는 고성능 시스템입니다.

## ✨ 주요 기능

### 🔍 **7가지 검색 알고리즘**
- **기본 검색 (ILIKE)**: 단순 텍스트 매칭
- **TF-IDF 검색**: 단어 중요도 기반 의미적 검색
- **가중치 검색**: 제목, 태그, 설명에 다른 가중치 적용
- **BM25 검색**: OpenSearch 전문 검색 엔진
- **하이브리드 검색**: TF-IDF와 BM25를 결합한 고급 검색
- **의미 기반 검색**: 임베딩 유사도 기반 검색
- **감정 분석 검색**: 댓글 감정 점수를 고려한 검색

### 🚀 **고성능 아키텍처**
- **멀티스테이지 Docker 빌드**: 최적화된 이미지 크기
- **Nginx 리버스 프록시**: 정적 파일 캐싱 및 Gzip 압축
- **Redis 캐싱**: 검색 결과 캐싱으로 응답 속도 향상
- **PostgreSQL**: 관계형 데이터 저장
- **OpenSearch**: 전문 검색 및 BM25 알고리즘

### 🎨 **현대적 UI/UX**
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **애니메이션**: Framer Motion 기반 부드러운 전환
- **에러 처리**: 사용자 친화적 에러 메시지
- **로딩 상태**: 스켈레톤 UI 및 로딩 스피너
- **접근성**: 키보드 네비게이션 및 스크린 리더 지원

## 🛠️ 기술 스택

### **Backend**
- **Python 3.11**: 메인 프로그래밍 언어
- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL 15**: 관계형 데이터베이스
- **OpenSearch 2.13**: 전문 검색 엔진
- **Redis 7**: 인메모리 캐시
- **psycopg2**: PostgreSQL 어댑터
- **scikit-learn**: 머신러닝 라이브러리

### **Frontend**
- **React 18**: 사용자 인터페이스 라이브러리
- **Styled Components**: CSS-in-JS 스타일링
- **Framer Motion**: 애니메이션 라이브러리
- **React Query**: 서버 상태 관리
- **Axios**: HTTP 클라이언트
- **React Icons**: 아이콘 라이브러리

### **Infrastructure**
- **Docker & Docker Compose**: 컨테이너화
- **Nginx**: 웹 서버 및 리버스 프록시
- **Multi-stage Build**: 최적화된 이미지 빌드

## 🚀 빠른 시작

### **개발 환경**

```bash
# 1. 저장소 클론
git clone <repository-url>
cd yt2

# 2. 환경 변수 설정
cp env.example .env
# .env 파일에서 YouTube API 키 등을 설정하세요

# 3. 개발 서비스 시작
chmod +x scripts/dev.sh
./scripts/dev.sh
```

### **프로덕션 배포**

```bash
# 1. 프로덕션 배포
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### **수동 실행**

```bash
# 개발 환경
docker-compose up -d

# 프로덕션 환경
docker-compose --profile production up -d
```

## 🌐 서비스 접속

| 서비스 | 개발 환경 | 프로덕션 환경 | 설명 |
|--------|-----------|---------------|------|
| **프론트엔드** | http://localhost:3000 | http://localhost:80 | React 애플리케이션 |
| **API 서버** | http://localhost:8000 | http://localhost:8000 | FastAPI REST API |
| **API 문서** | http://localhost:8000/docs | http://localhost:8000/docs | Swagger UI |
| **OpenSearch** | http://localhost:5601 | http://localhost:5601 | 검색 엔진 대시보드 |

## 📊 성능 최적화

### **Docker 최적화**
- 공통 베이스 이미지 사용
- 멀티스테이지 빌드
- .dockerignore로 빌드 컨텍스트 최소화
- 의존성 분리 (common, service-specific)

### **프론트엔드 최적화**
- 코드 스플리팅
- 이미지 최적화
- Gzip 압축
- 브라우저 캐싱
- React.memo 및 useMemo 활용

### **백엔드 최적화**
- Redis 캐싱
- 데이터베이스 인덱싱
- 비동기 처리
- 연결 풀링

## 🔧 개발 가이드

### **프로젝트 구조**
```
yt2/
├── api/                    # FastAPI 백엔드
├── crawler/               # YouTube 데이터 수집
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/    # 재사용 가능한 컴포넌트
│   │   ├── hooks/         # 커스텀 훅
│   │   ├── services/      # API 서비스
│   │   ├── utils/         # 유틸리티 함수
│   │   └── contexts/      # React 컨텍스트
├── database/              # 데이터베이스 스키마
├── scripts/               # 배포 및 개발 스크립트
└── docker-compose.yml     # Docker Compose 설정
```

### **검색 알고리즘 추가**
1. `api/main.py`에 새로운 알고리즘 함수 추가
2. `frontend/src/utils/constants.js`에 알고리즘 옵션 추가
3. `frontend/src/hooks/useSearch.js`에 알고리즘 처리 로직 추가

### **컴포넌트 개발**
1. `frontend/src/components/`에 새 컴포넌트 생성
2. Styled Components로 스타일링
3. Framer Motion으로 애니메이션 추가
4. PropTypes 또는 TypeScript로 타입 검증

## 🧪 테스트

```bash
# 프론트엔드 테스트
cd frontend
npm test

# API 테스트
curl http://localhost:8000/health

# 통합 테스트
python test_integration.py
```

## 📈 모니터링

### **로그 확인**
```bash
# API 서버 로그
docker-compose logs -f api

# 프론트엔드 로그
docker-compose logs -f frontend

# 모든 서비스 로그
docker-compose logs -f
```

### **성능 모니터링**
- OpenSearch 대시보드에서 검색 성능 확인
- Redis 메모리 사용량 모니터링
- PostgreSQL 쿼리 성능 분석

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 [Issues](https://github.com/your-repo/issues)를 통해 문의해주세요.

---

**🎉 행궁 검색으로 수원시의 숨겨진 보물을 찾아보세요!**