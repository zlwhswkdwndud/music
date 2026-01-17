FROM python:3.10-slim-bullseye

# 자바 설치 삭제, ffmpeg만 유지
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 오직 파이썬만 실행
CMD ["python", "main.py"]
