FROM nvidia/cuda:11.8.0-devel-ubuntu22.04
FROM runpod/base:0.6.3-cuda11.8.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3-pip \
        ffmpeg \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Install dependencies
RUN pip install uv
COPY requirements.txt /requirements.txt
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system

# Add files
COPY . .

ENV PYTHONUNBUFFERED=1

# Run the handler
CMD ["python", "-u", "handler.py"]
