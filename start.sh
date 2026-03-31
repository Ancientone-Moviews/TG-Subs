#!/bin/bash

# Sync system time using chrony
echo "Syncing system time with chrony..."
chronyc -a makestep || echo "Chrony sync failed, continuing..."

# Alternative: try ntpdate if chrony fails
if [ $? -ne 0 ]; then
    echo "Trying ntpdate..."
    ntpdate -u pool.ntp.org || echo "NTP sync failed, continuing..."
fi

# Wait a moment for time to settle
sleep 2

# Start the bot
echo "Starting Telegram bot..."
exec python bot/main.py