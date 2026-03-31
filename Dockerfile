# Use lightweight Python base image
FROM python:3.9-slim

# Install system dependencies for time sync
RUN apt-get update && apt-get install -y \
    chrony \
    tzdata \
    ntpdate \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to IST (Indian Standard Time)
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY bot/ ./bot/

# Set the start command
CMD ["/start.sh"]