"""
Configuration file for Telegram Subscription Bot
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_CANDIDATES = [
    os.path.join(BASE_DIR, '.env'),
    os.path.join(BASE_DIR, 'sample_config.env'),
]

loaded_config_path = None
for config_path in CONFIG_CANDIDATES:
    if os.path.exists(config_path):
        load_dotenv(config_path, override=False)
        loaded_config_path = config_path
        break

if loaded_config_path:
    print(f"Loaded configuration from: {loaded_config_path}")
else:
    print(
        "Warning: No config file found. Expected one of: "
        + ", ".join(CONFIG_CANDIDATES)
        + ". Using environment variables/default values."
    )


class Config:
    # Telegram Bot Settings
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    API_ID = os.getenv("API_ID", "29868868")
    API_HASH = os.getenv("API_HASH", "6b7bd10846ff6d7e8f50a4bfe13c9fd4")

    # Admin Settings
    OWNER_ID = int(os.getenv("OWNER_ID", "5884953489"))
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5884953489").split(",")))

    # Group Settings
    SUBSCRIPTION_GROUP_ID = int(os.getenv("SUBSCRIPTION_GROUP_ID", "-1002605917246"))
    SUBSCRIPTION_GROUP_NAME = os.getenv("SUBSCRIPTION_GROUP_NAME", "Stremio Private Group")

    # Logs Channel (for payment receipts and renewal logs)
    LOGS_CHANNEL_ID = os.getenv("LOGS_CHANNEL_ID", None)
    if LOGS_CHANNEL_ID:
        LOGS_CHANNEL_ID = int(LOGS_CHANNEL_ID)

    # Database Settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
    DB_NAME = os.getenv("DB_NAME", "tg_subs")

    # Payment Settings
    CURRENCY = os.getenv("CURRENCY", "₹")  # Rupees
    PAYMENT_PROOF_REQUIRED = os.getenv("PAYMENT_PROOF_REQUIRED", "true").lower() == "true"

    # Subscription Plans (Default) - Can be modified via admin
    DEFAULT_PLANS = [
        {"days": 15, "price": 30},
        {"days": 30, "price": 60},
        {"days": 60, "price": 80},
        {"days": 90, "price": 100},
    ]

    # Auto-approval settings
    AUTO_APPROVE_VOUCHERS = os.getenv("AUTO_APPROVE_VOUCHERS", "true").lower() == "true"
    AUTO_APPROVE_GIFTCARDS = os.getenv("AUTO_APPROVE_GIFTCARDS", "true").lower() == "true"

    # Bot Behavior
    PAYMENT_TIMEOUT = int(os.getenv("PAYMENT_TIMEOUT", "300"))  # 5 minutes
    MESSAGE_DELETE_TIMEOUT = int(os.getenv("MESSAGE_DELETE_TIMEOUT", "120"))  # 2 minutes

    # Base URLs
    BASE_URL = os.getenv("BASE_URL", "https://example.com")


def validate_config():
    """Validate required runtime configuration before bot startup."""
    errors = []

    if loaded_config_path is None and not any(
        os.getenv(key) for key in ("BOT_TOKEN", "API_ID", "API_HASH")
    ):
        errors.append(
            "Missing config file. Expected .env or sample_config.env in the project root, "
            "or BOT_TOKEN/API_ID/API_HASH in the environment"
        )

    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("BOT_TOKEN is missing or still set to the sample placeholder")

    if not Config.API_ID or Config.API_ID == "29868868":
        errors.append("API_ID is missing or still set to the sample value")

    if not Config.API_HASH or Config.API_HASH == "6b7bd10846ff6d7e8f50a4bfe13c9fd4":
        errors.append("API_HASH is missing or still set to the sample value")

    return errors


# Global client instance for logging (will be set in main.py)
client = None


def set_client(bot_client: Client):
    """Set the global client for logging"""
    global client
    client = bot_client


async def log_to_channel(message: str):
    """Send log message to logs channel if configured"""
    if client and Config.LOGS_CHANNEL_ID:
        try:
            await client.send_message(Config.LOGS_CHANNEL_ID, message)
        except Exception as e:
            print(f"Failed to send log to channel: {e}")


async def log_payment_approved(user_id: int, payment_type: str, amount: str, admin_id: int):
    """Log payment approval to channel"""
    message = (
        f"💰 <b>Payment Approved</b>\n\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Type:</b> {payment_type}\n"
        f"<b>Amount:</b> {amount}\n"
        f"<b>Approved by:</b> <code>{admin_id}</code>\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    await log_to_channel(message)


async def log_payment_rejected(user_id: int, payment_type: str, reason: str, admin_id: int):
    """Log payment rejection to channel"""
    message = (
        f"❌ <b>Payment Rejected</b>\n\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Type:</b> {payment_type}\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>Rejected by:</b> <code>{admin_id}</code>\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    await log_to_channel(message)


async def log_subscription_renewed(user_id: int, days: int, expiry_date: str, method: str = "manual"):
    """Log subscription renewal to channel"""
    message = (
        f"🔄 <b>Subscription Renewed</b>\n\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Days Added:</b> {days}\n"
        f"<b>New Expiry:</b> {expiry_date}\n"
        f"<b>Method:</b> {method}\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    await log_to_channel(message)


async def log_user_removed(user_id: int, reason: str):
    """Log user removal to channel"""
    message = (
        f"🚫 <b>User Removed</b>\n\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    await log_to_channel(message)


config = Config()
