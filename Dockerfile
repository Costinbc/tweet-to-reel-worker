FROM alpine:3.20 AS ffmpeg_gpu
FROM runpod/base:0.6.3-cuda11.8.0

ARG FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-linux64-gpl.tar.xz"

RUN mkdir -p /opt/ffmpeg && \
    curl -sSL "$FFMPEG_URL" -o /tmp/ffmpeg.tar.xz && \
    tar -xf /tmp/ffmpeg.tar.xz -C /opt/ffmpeg --strip-components=1 && \
    mv /opt/ffmpeg/bin/ffmpeg  /usr/local/bin/ffmpeg && \
    mv /opt/ffmpeg/bin/ffprobe /usr/local/bin/ffprobe && \
    rm -rf /tmp/ffmpeg.tar.xz /opt/ffmpeg

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        ffmpeg python3.11 python3-pip \
        libgl1 libglib2.0-0 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}
ENV PATH="/usr/local/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip uv
COPY requirements.txt .
RUN uv pip install --upgrade -r requirements.txt --no-cache-dir --system

COPY handler.py assemble_reel.py crop_tweet.py video_dl.py screenshot_ors.py ./

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "handler.py"]