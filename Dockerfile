FROM python:3.14-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

# Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install bgutil PO Token Provider server
RUN git clone --depth 1 --branch 2.0.0 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
    /opt/bgutil-ytdlp-pot-provider

WORKDIR /opt/bgutil-ytdlp-pot-provider/server

# Install provider dependencies
RUN deno install --allow-scripts=npm:canvas --frozen

WORKDIR /app

# Copy application
COPY . .

RUN mkdir -p downloads

# Verify installations
RUN deno --version
RUN ffmpeg -version
RUN python -m yt_dlp --version

# Start both the PO-token provider and FastAPI
CMD ["sh", "-c", "deno run --allow-env --allow-net --allow-ffi=. --allow-read=. /opt/bgutil-ytdlp-pot-provider/server/src/main.ts --host 127.0.0.1 --port 4416 & uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]