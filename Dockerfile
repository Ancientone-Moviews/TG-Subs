# Use lightweight Python base image
FROM python:3.9-slim

# Install system dependencies for time sync
RUN apt-get update && apt-get install -y \
    chrony \
    tzdata \
    ntpsec-ntpdate \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configure chrony for IST timezone (prioritize Windows time server)
RUN echo "server time.windows.com iburst prefer" >> /etc/chrony/chrony.conf && \
    echo "server time.nist.gov iburst" >> /etc/chrony/chrony.conf && \
    echo "server pool.ntp.org iburst" >> /etc/chrony/chrony.conf && \
    echo "server asia.pool.ntp.org iburst" >> /etc/chrony/chrony.conf && \
    echo "allow all" >> /etc/chrony/chrony.conf

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

# Remove build tools to keep image slim
RUN apt-get purge -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy environment file and bot source code
COPY .env* ./
COPY bot/ ./bot/

# Set the start command
CMD ["/start.sh"]