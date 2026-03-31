#!/bin/bash

# Sync system time with IST (Indian NTP servers)
echo "Syncing system time with Indian NTP servers..."

# Try multiple NTP servers with retries
NTP_SERVERS=("time.nist.gov" "pool.ntp.org" "asia.pool.ntp.org")

for server in "${NTP_SERVERS[@]}"; do
    echo "Trying NTP server: $server"
    for attempt in {1..3}; do
        if ntpdate -u "$server" 2>/dev/null; then
            echo "✅ Time sync successful with $server (attempt $attempt)"
            SYNC_SUCCESS=true
            break 2
        fi
        echo "Attempt $attempt failed, retrying..."
        sleep 1
    done
done

if [ "$SYNC_SUCCESS" != true ]; then
    echo "❌ All NTP sync attempts failed, continuing with current time..."
fi

# Wait a moment for time to settle
sleep 2

# Display current time
echo "Current system time: $(date)"
echo "Timezone: $TZ"

# Start the bot
echo "Starting Telegram bot..."
exec python bot/main.py