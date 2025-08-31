FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS ffbuild

ARG FFMPEG_REF=release/8.0


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential git pkg-config yasm nasm \
        libssl-dev libxml2-dev zlib1g-dev libpng16-16 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /root
RUN git clone https://github.com/FFmpeg/nv-codec-headers && \
    cd nv-codec-headers && \
    make install

RUN git clone https://git.ffmpeg.org/ffmpeg.git && \
    cd ffmpeg && git checkout "${FFMPEG_REF}"
WORKDIR /root/ffmpeg

RUN ./configure \
        --prefix=/usr/local/ffmpeg \
        --enable-gpl --enable-version3 --enable-nonfree \
        --enable-cuda-nvcc --enable-libnpp --enable-cuda-llvm \
        --enable-nvenc \
        --extra-cflags=-I/usr/local/cuda/include \
        --extra-ldflags=-L/usr/local/cuda/lib64 && \
    make -j"$(nproc)" && make install

FROM runpod/base:0.7.0-ubuntu2204-cuda1241

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpng16-16 zlib1g && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ffbuild /usr/local/ffmpeg /usr/local/ffmpeg
RUN ln -s /usr/local/ffmpeg/bin/* /usr/local/bin/

ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all

COPY nvenc-guard.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/nvenc-guard.sh
ENTRYPOINT ["/usr/local/bin/nvenc-guard.sh"]

COPY requirements.txt .
RUN pip install -U pip uv && \
    uv pip install -r requirements.txt --system

COPY handler.py assemble_reel.py crop_tweet.py video_dl.py screenshot_ors.py probe_video.py ./
COPY test_input.json ./
COPY backgrounds/white_background_1080x1920.png backgrounds/black_background_1080x1920.png ./backgrounds/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "handler.py"]
