# 파이썬 3.10 버전이 깔린 가상 컴퓨터 준비
FROM python:3.10-slim-bullseye

# 자바(Lavalink용)와 오디오 처리기(FFmpeg) 설치
RUN apt-get update && apt-get install -y openjdk-17-jre-headless wget ffmpeg

WORKDIR /app

# Lavalink 서버 파일 다운로드
RUN wget https://github.com/lavalink-devs/Lavalink/releases/download/4.0.8/Lavalink.jar

# 필요한 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 모든 코드 복사
COPY . .

# Lavalink와 봇을 동시에 실행

RUN chmod +x run.sh
CMD ["./run.sh"]

