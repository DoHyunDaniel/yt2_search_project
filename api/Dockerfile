# 공통 베이스 이미지 사용
FROM yt2-base:latest

# API 전용 의존성 설치
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api/ .
COPY crawler/ ./crawler
COPY backup/ ./backup

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
