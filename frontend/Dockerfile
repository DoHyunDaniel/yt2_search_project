# 멀티스테이지 빌드
FROM node:18-alpine AS builder

WORKDIR /app

# package.json과 package-lock.json 복사
COPY frontend/package*.json ./

# 의존성 설치
RUN npm install --production && npm cache clean --force

# 소스 코드 복사
COPY frontend/ .

# 환경 변수 설정
ENV NODE_ENV=production
ENV REACT_APP_API_URL=http://localhost:8000

# 프로덕션 빌드
RUN npm run build

# 프로덕션 서버
FROM nginx:alpine AS production

# nginx 설정 복사
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# 빌드된 파일 복사
COPY --from=builder /app/build /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]
