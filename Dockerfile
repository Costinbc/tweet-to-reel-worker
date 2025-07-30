FROM runpod/base:0.6.3-cuda11.8.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        xz-utils \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" && \
    curl -sSL "$FFMPEG_URL" -o /tmp/ffmpeg.tar.xz && \
    mkdir -p /tmp/ffmpeg-static && \
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg-static --strip-components=1 && \
    mv /tmp/ffmpeg-static/ffmpeg /usr/local/bin/ffmpeg && \
    mv /tmp/ffmpeg-static/ffprobe /usr/local/bin/ffprobe && \
    rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-static

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Install dependencies
COPY requirements.txt /requirements.txt
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system

# Add files
COPY . .

ENV PYTHONUNBUFFERED=1

# Run the handler
CMD ["python", "-u", "handler.py"]
