FROM python:3.14-slim

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

# Download bgutil PO token provider
RUN git clone --branch 2.0.0 --depth 1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
    /opt/bgutil-ytdlp-pot-provider

# Install bgutil server dependencies
WORKDIR /opt/bgutil-ytdlp-pot-provider/server

RUN deno install --allow-scripts=npm:canvas --frozen

# Copy Harvester application
WORKDIR /app
COPY . .

RUN mkdir -p downloads

RUN deno --version
RUN ffmpeg -version

# Start bgutil provider + FastAPI
CMD ["sh", "-c", "cd /opt/bgutil-ytdlp-pot-provider/server && deno run --allow-env --allow-net --allow-ffi=/opt/bgutil-ytdlp-pot-provider/server/node_modules --allow-read=/opt/bgutil-ytdlp-pot-provider/server/node_modules /opt/bgutil-ytdlp-pot-provider/server/src/main.ts --host 127.0.0.1 --port 4416 & uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]