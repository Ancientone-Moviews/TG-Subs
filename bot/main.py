"""
Telegram Premium Channel Bot - Main Entry Point
Premium channel access management with anonymous mode and privacy protection
"""

import asyncio
from pyrogram import Client, errors
from config import config, set_client, validate_config
from database import SubscriptionDB
import handlers_subscription
import handlers_payment
import handlers_admin
import handlers_scheduler
import sys
import signal

# Initialize database
db = SubscriptionDB(config.MONGODB_URI, config.DB_NAME)

# Global runtime state
scheduler_task = None
shutdown_event = None
running_loop = None
app = None


def build_app():
    """Create the Telegram client after config validation."""
    return Client(
        "subscription_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workers=4,
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n\n👋 Received signal {signum}. Shutting down gracefully...")

    if shutdown_event is None:
        return

    if running_loop and not running_loop.is_closed():
        running_loop.call_soon_threadsafe(shutdown_event.set)
    else:
        shutdown_event.set()


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def initialize():
    """Initialize bot and database."""
    print("=" * 50)
    print("🤖 Telegram Subscription Bot Initializing...")
    print("=" * 50)

    # Connect to database
    db_connected = await db.connect()
    if not db_connected:
        print("❌ Failed to connect to database!")
        sys.exit(1)

    # Set database for handlers
    handlers_subscription.set_database(db)
    handlers_payment.set_database(db)
    handlers_admin.set_database(db)
    handlers_scheduler.set_database(db)

    # Initialize default plans if empty
    plans = await db.get_plans()
    if not plans:
        print("📋 Initializing default subscription plans...")
        for plan in config.DEFAULT_PLANS:
            await db.add_plan(plan["days"], plan["price"])
            print(f"   ✅ Added {plan['days']} days plan (₹{plan['price']})")

    try:
        bot_me = await app.get_me()
    except Exception as e:
        print(
            f"❌ Failed to fetch bot identity. Verify BOT_TOKEN, API credentials, "
            f"and network connectivity: {e}"
        )
        sys.exit(1)

    bot_username = bot_me.username or "N/A"
    admin_ids = config.ADMIN_IDS or []
    if admin_ids:
        admin_ids_display = f"{len(admin_ids)} admin(s)"
    else:
        admin_ids_display = "None"
    config_values = [
        ("BOT_TOKEN", "[REDACTED]"),
        ("API_ID", "[REDACTED]"),
        ("API_HASH", "[REDACTED]"),
        ("OWNER_ID", "[REDACTED]"),
        ("ADMIN_IDS", admin_ids_display),
        ("SUBSCRIPTION_GROUP_ID", "[REDACTED]"),
        ("SUBSCRIPTION_GROUP_NAME", config.SUBSCRIPTION_GROUP_NAME),
        ("LOGS_CHANNEL_ID", "[REDACTED]" if config.LOGS_CHANNEL_ID else "None"),
        ("MONGODB_URI", "[REDACTED]"),
        ("DB_NAME", config.DB_NAME),
        ("CURRENCY", config.CURRENCY),
        ("PAYMENT_PROOF_REQUIRED", config.PAYMENT_PROOF_REQUIRED),
        ("DEFAULT_PLANS", config.DEFAULT_PLANS),
        ("AUTO_APPROVE_VOUCHERS", config.AUTO_APPROVE_VOUCHERS),
        ("AUTO_APPROVE_GIFTCARDS", config.AUTO_APPROVE_GIFTCARDS),
        ("PAYMENT_TIMEOUT", config.PAYMENT_TIMEOUT),
        ("MESSAGE_DELETE_TIMEOUT", config.MESSAGE_DELETE_TIMEOUT),
        ("BASE_URL", config.BASE_URL),
    ]

    print(f"\n✅ Bot configured:")
    print(f"   Bot ID: {bot_me.id}")
    print(f"   Bot Username: {bot_username}")
    for label, value in config_values:
        print(f"   {label}: {value}")
    print(f"   Total Plans: {len(plans)}")

    print("\n" + "=" * 50)
    print("✅ Bot is ready!")
    print("=" * 50)


async def start_bot():
    """Main bot function logic in context manager."""
    global scheduler_task, shutdown_event, running_loop, app

    config_errors = validate_config()
    if config_errors:
        print("❌ Configuration error:")
        for error in config_errors:
            print(f"   - {error}")
        print("   - Fill /app/config.env, /app/.env, or /app/sample_config.env with real BOT_TOKEN, API_ID, and API_HASH, or pass them as environment variables")
        raise RuntimeError("Invalid runtime configuration")

    running_loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    scheduler_task = None

    app = build_app()
    set_client(app)

    async with app:
        await initialize()

        # Start scheduler task in background
        print("\n📅 Starting background scheduler...")
        scheduler_task = asyncio.create_task(handlers_scheduler.scheduler_task(app))

        print("\n🚀 Bot started! Listening for messages...\n")

        # Keep the bot running until shutdown signal
        await shutdown_event.wait()

        print("\n\n👋 Shutting down bot...")

        # Cancel scheduler task
        if scheduler_task and not scheduler_task.done():
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass

    scheduler_task = None
    shutdown_event = None
    running_loop = None
    print("✅ Bot shutdown complete")


async def main():
    """Main bot function."""
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            await start_bot()
            return
        except errors.BadMsgNotification as e:
            print(f"⚠️ BadMsgNotification on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                print("⏳ Waiting 5 seconds before retrying...")
                await asyncio.sleep(5)
                continue
            print("❌ Max retries reached for BadMsgNotification. Exiting.")
            raise
        except Exception as e:
            if "msg_id is too low" in str(e):
                print("⚠️ Time synchronization error detected, but continuing with local IST date arithmetic for subscription expiry.")
                print("💡 Ensure system time is synced (chrony / chronyc -a makestep), but subscription calculation will use IST now.")
                return
            print(f"❌ Bot error: {e}")
            raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
