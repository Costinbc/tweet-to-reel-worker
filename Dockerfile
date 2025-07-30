FROM jrottenberg/ffmpeg:6.0-nvidia-static as ffmpeg_build
FROM runpod/base:0.6.3-cuda11.8.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ffmpeg_build /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg_build /usr/local/bin/ffprobe /usr/local/bin/ffprobe

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
