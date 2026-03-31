"""
Timezone Utilities for Telegram Bot
Provides comprehensive timezone handling with IST as default
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import pytz  # Fallback for older systems

# Default timezone configurations
DEFAULT_TIMEZONE = "Asia/Kolkata"  # IST
SUPPORTED_TIMEZONES = {
    "IST": "Asia/Kolkata",
    "UTC": "UTC",
    "EST": "US/Eastern",
    "PST": "US/Pacific",
    "GMT": "GMT",
    "CET": "Europe/Berlin",
    "JST": "Asia/Tokyo",
}

class TimeZoneManager:
    """Comprehensive timezone management for the bot"""

    def __init__(self, default_tz: str = DEFAULT_TIMEZONE):
        self.default_tz = default_tz
        self._tz_cache = {}

    def get_timezone(self, tz_name: str = None) -> ZoneInfo:
        """Get timezone object, with caching"""
        tz_name = tz_name or self.default_tz
        tz_key = tz_name.lower()

        if tz_key not in self._tz_cache:
            try:
                # Try ZoneInfo first (Python 3.9+)
                self._tz_cache[tz_key] = ZoneInfo(tz_name)
            except Exception:
                try:
                    # Fallback to pytz
                    self._tz_cache[tz_key] = pytz.timezone(tz_name)
                except Exception:
                    # Ultimate fallback to default
                    self._tz_cache[tz_key] = ZoneInfo(self.default_tz)

        return self._tz_cache[tz_key]

    def now(self, tz_name: str = None) -> datetime:
        """Get current time in specified timezone"""
        tz = self.get_timezone(tz_name)
        return datetime.now(tz)

    def convert_time(self, dt: datetime, to_tz: str) -> datetime:
        """Convert datetime to different timezone"""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        target_tz = self.get_timezone(to_tz)
        return dt.astimezone(target_tz)

    def format_time(self, dt: datetime, tz_name: str = None, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """Format datetime with timezone"""
        if dt.tzinfo is None:
            dt = self.convert_time(dt, tz_name or self.default_tz)

        return dt.strftime(format_str)

    def parse_time(self, time_str: str, tz_name: str = None) -> datetime:
        """Parse time string in specified timezone"""
        tz = self.get_timezone(tz_name)
        # Simple parsing - can be enhanced
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            return dt
        except:
            # Fallback parsing
            return datetime.now(tz)

    def get_time_diff(self, tz1: str, tz2: str) -> timedelta:
        """Get time difference between two timezones"""
        now = datetime.now(ZoneInfo("UTC"))
        tz1_time = now.astimezone(self.get_timezone(tz1))
        tz2_time = now.astimezone(self.get_timezone(tz2))
        return tz1_time - tz2_time

    def is_valid_timezone(self, tz_name: str) -> bool:
        """Check if timezone is valid"""
        try:
            self.get_timezone(tz_name)
            return True
        except:
            return False

# Global timezone manager instance
tz_manager = TimeZoneManager()

# Convenience functions
def ist_now() -> datetime:
    """Get current IST time"""
    return tz_manager.now("IST")

def utc_now() -> datetime:
    """Get current UTC time"""
    return tz_manager.now("UTC")

def format_ist_time(dt: datetime = None) -> str:
    """Format time in IST"""
    if dt is None:
        dt = ist_now()
    return tz_manager.format_time(dt, "IST", "%Y-%m-%d %H:%M:%S IST")

def convert_to_ist(dt: datetime) -> datetime:
    """Convert any datetime to IST"""
    return tz_manager.convert_time(dt, "IST")

def get_supported_timezones() -> Dict[str, str]:
    """Get list of supported timezones"""
    return SUPPORTED_TIMEZONES.copy()

# Environment-based timezone detection
def get_system_timezone() -> str:
    """Get system timezone or fallback to IST"""
    try:
        # Try to get from environment
        tz = os.environ.get('TZ', DEFAULT_TIMEZONE)
        if tz_manager.is_valid_timezone(tz):
            return tz
    except:
        pass
    return DEFAULT_TIMEZONE

# Initialize with system timezone if available
try:
    system_tz = get_system_timezone()
    if system_tz != DEFAULT_TIMEZONE:
        tz_manager = TimeZoneManager(system_tz)
except:
    pass