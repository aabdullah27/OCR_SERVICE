FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install Python 3.13 via uv
RUN uv python install 3.13

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/

# Install dependencies
RUN uv sync --frozen

# Install vLLM
RUN uv add vllm

# Copy deploy configs
COPY deploy/ ./deploy/
RUN chmod +x ./deploy/start.sh

# Environment
ENV OCR_DOLPHIN_VLLM_URL=http://localhost:8000/v1
ENV OCR_DOLPHIN_MODEL_NAME=ByteDance/Dolphin-v2

EXPOSE 8080

CMD ["/usr/bin/supervisord", "-c", "/app/deploy/supervisord.conf"]
