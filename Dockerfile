# 파이썬 환경 사용
FROM python:3.9-slim

# 작업 폴더 설정
WORKDIR /app

# 필요 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY app.py .

# 포트 개방
EXPOSE 8080

# 실행 명령
CMD ["python", "app.py"]
