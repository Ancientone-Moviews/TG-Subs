#!/bin/bash
set -e

# Keep container timezone on IST for display/logging.
export TZ="${TZ:-Asia/Kolkata}"

echo "Using timezone: $TZ"
echo "Current system time: $(date)"
echo "Starting Telegram bot..."

exec python bot/main.py
