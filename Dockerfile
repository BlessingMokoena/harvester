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

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create download directory
RUN mkdir -p downloads

# Verify required tools
RUN deno --version
RUN ffmpeg -version

# Verify yt-dlp and PO token provider
RUN python -m yt_dlp --version

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]