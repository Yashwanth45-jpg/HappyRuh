# Dockerfile.app
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=1200

WORKDIR /app

# System deps for psycopg2, pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libc6-dev libpq-dev \
    libfreetype6-dev libjpeg62-turbo-dev zlib1g-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip/setuptools/wheel first
RUN pip install --upgrade pip setuptools wheel

# Install torch from PyTorch CPU wheels (more reliable in Docker)
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.2.2 --no-cache-dir

# Copy requirements and install remaining packages (exclude torch if present)
COPY requirements.txt /app/requirements.txt
RUN grep -v '^torch==' /app/requirements.txt > /tmp/reqs.txt \
 && pip install --no-cache-dir -r /tmp/reqs.txt

# Copy source code
COPY src/ /app/src/

# Expose the port the app uses
EXPOSE 8080

# Start FastAPI (adjust module path if needed)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
