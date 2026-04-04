"""
Telegram Premium Channel Bot - Main Entry Point
Premium channel access management with anonymous mode and privacy protection
"""

import asyncio
import os
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
health_server = None
runtime_status = {
    "state": "starting",
    "detail": "Booting process",
}


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


def set_runtime_status(state: str, detail: str):
    """Track current startup/runtime phase for logs and health checks."""
    runtime_status["state"] = state
    runtime_status["detail"] = detail
    print(f"[status] {state}: {detail}")


async def handle_healthcheck(reader, writer):
    """Expose a minimal HTTP endpoint for platforms that require a bound PORT."""
    try:
        request_line = await reader.readline()
        path = "/"
        if request_line:
            parts = request_line.decode("utf-8", errors="ignore").split()
            if len(parts) >= 2:
                path = parts[1]

        while True:
            line = await reader.readline()
            if not line or line in (b"\r\n", b"\n"):
                break

        if path not in ("/", "/health", "/healthz"):
            status_line = "HTTP/1.1 404 Not Found"
            body = "not found\n"
        else:
            status_line = "HTTP/1.1 200 OK"
            body = f"state={runtime_status['state']}\ndetail={runtime_status['detail']}\n"

        response = (
            f"{status_line}\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        )
        writer.write(response.encode("utf-8"))
        await writer.drain()
    except Exception as e:
        print(f"⚠️ Healthcheck server error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_health_server_if_needed():
    """Bind an HTTP port when a platform provides PORT for readiness checks."""
    global health_server

    port = os.getenv("PORT")
    if not port:
        return

    health_server = await asyncio.start_server(handle_healthcheck, host="0.0.0.0", port=int(port))
    sockets = health_server.sockets or []
    bound = sockets[0].getsockname() if sockets else f"0.0.0.0:{port}"
    print(f"🌐 Healthcheck server listening on {bound}")


async def stop_health_server():
    """Shut down the auxiliary HTTP listener."""
    global health_server

    if health_server is None:
        return

    health_server.close()
    await health_server.wait_closed()
    health_server = None


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def initialize():
    """Initialize bot and database."""
    set_runtime_status("initializing", "Connecting to MongoDB")
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

    print(f"\n✅ Bot configured:")
    print(f"   Bot Token: {config.BOT_TOKEN[:20]}...")
    print(f"   Owner ID: {config.OWNER_ID}")
    print(f"   Admin IDs: {config.ADMIN_IDS}")
    print(f"   Group ID: {config.SUBSCRIPTION_GROUP_ID}")
    print(f"   Group Name: {config.SUBSCRIPTION_GROUP_NAME}")
    print(f"   Database: {config.DB_NAME}")
    print(f"   Total Plans: {len(plans)}")

    print("\n" + "=" * 50)
    print("✅ Bot is ready!")
    print("=" * 50)
    set_runtime_status("ready", "Bot initialized successfully")


async def start_bot():
    """Main bot function logic in context manager."""
    global scheduler_task, shutdown_event, running_loop, app

    config_errors = validate_config()
    if config_errors:
        set_runtime_status("error", "Invalid runtime configuration")
        print("❌ Configuration error:")
        for error in config_errors:
            print(f"   - {error}")
        print("   - Fill /app/config.env, /app/.env, or /app/sample_config.env with real BOT_TOKEN, API_ID, and API_HASH, or pass them as environment variables")
        raise RuntimeError("Invalid runtime configuration")

    running_loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    scheduler_task = None

    await start_health_server_if_needed()

    set_runtime_status("starting", "Starting Telegram client")
    app = build_app()
    set_client(app)

    try:
        print("🔌 Connecting to Telegram...")
        async with app:
            try:
                me = await app.get_me()
                print(f"🤖 Logged in as @{me.username} (id={me.id})")
            except Exception as e:
                print(f"⚠️ Failed to fetch bot identity: {e}")

            # Long polling will not receive updates if a webhook is still configured.
            try:
                if hasattr(app, "delete_webhook"):
                    await app.delete_webhook()
                    print("🧹 Cleared existing Telegram webhook for polling mode")
            except Exception as e:
                print(f"⚠️ Failed to clear webhook: {e}")

            set_runtime_status("starting", "Telegram client connected")
            await initialize()

            # Start scheduler task in background
            print("\n📅 Starting background scheduler...")
            scheduler_task = asyncio.create_task(handlers_scheduler.scheduler_task(app))

            print("\n🚀 Bot started! Listening for messages...\n")
            set_runtime_status("running", "Bot polling for updates")

            # Keep the bot running until shutdown signal
            await shutdown_event.wait()

            print("\n\n👋 Shutting down bot...")
            set_runtime_status("stopping", "Shutdown requested")

            # Cancel scheduler task
            if scheduler_task and not scheduler_task.done():
                scheduler_task.cancel()
                try:
                    await scheduler_task
                except asyncio.CancelledError:
                    pass
    finally:
        await stop_health_server()

    scheduler_task = None
    shutdown_event = None
    running_loop = None
    set_runtime_status("stopped", "Bot shutdown complete")
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
                set_runtime_status("warning", "Telegram msg_id clock skew detected")
                print("⚠️ Time synchronization error detected, but continuing with local IST date arithmetic for subscription expiry.")
                print("💡 Ensure system time is synced (chrony / chronyc -a makestep), but subscription calculation will use IST now.")
                return
            set_runtime_status("error", str(e))
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
