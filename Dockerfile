# 파이썬 3.9 버전 사용
FROM python:3.9-slim

# 작업 폴더 생성
WORKDIR /app

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY app.py .

# 포트 8080 개방 (Flask 기본 포트)
EXPOSE 8080

# 실행 명령
CMD ["python", "app.py"]
