FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="/root/.deno/bin:${PATH}"

# Application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Start FastAPI
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]