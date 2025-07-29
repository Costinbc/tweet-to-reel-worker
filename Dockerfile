FROM runpod/base:0.6.3-cuda11.8.0
FROM jrottenberg/ffmpeg:6.1-ubuntu as ffmpeg
FROM runpod/base:0.6.3-cuda11.8.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*


COPY --from=ffmpeg /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg /usr/local/lib/ /usr/local/lib/

RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/ffmpeg.conf && \
    ldconfig

ENV PATH="/usr/local/bin:${PATH}"

# Set python3.11 as the default python
RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Install dependencies
COPY requirements.txt /requirements.txt
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system

# Add files
COPY handler.py .
COPY assemble_reel.py crop_tweet.py video_dl.py screenshot_ors.py ./

ENV PYTHONUNBUFFERED=1

# Run the handler
CMD python -u /handler.py
