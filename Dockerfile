# Use lightweight Python base image
FROM python:3.9-slim

# Install system dependencies for time sync
RUN apt-get update && apt-get install -y \
    ntpdate \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (optional, adjust as needed)
ENV TZ=UTC

# Sync system time
RUN ntpdate -u pool.ntp.org || true

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY bot/ ./bot/

# Set the start command
CMD ["python", "bot/main.py"]