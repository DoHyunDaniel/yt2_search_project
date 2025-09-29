# 공통 베이스 이미지 사용
FROM yt2-base:latest

# 크롤러 전용 의존성 설치
COPY crawler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY crawler/ .
COPY backup/ ./backup

# 애플리케이션 실행
CMD ["python", "crawler.py"]
