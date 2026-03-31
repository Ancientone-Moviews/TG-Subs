"""
Telegram Premium Channel Bot - Main Entry Point
Premium channel access management with anonymous mode and privacy protection
"""

import asyncio
from pyrogram import Client
from config import config, set_client
from database import SubscriptionDB
import handlers_subscription
import handlers_payment
import handlers_admin
import handlers_scheduler
import sys
import signal

# Initialize database
db = SubscriptionDB(config.MONGODB_URI, config.DB_NAME)

# Initialize Telegram app
app = Client(
    "subscription_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workers=4,
)

# Set client for logging
set_client(app)

# Global task reference
scheduler_task = None
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n\n👋 Received signal {signum}. Shutting down gracefully...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def initialize():
    """Initialize bot and database"""
    global scheduler_task
    
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

async def main():
    """Main bot function"""
    global scheduler_task
    
    try:
        async with app:
            await initialize()
            
            # Start scheduler task in background
            print("\n📅 Starting background scheduler...")
            scheduler_task = asyncio.create_task(handlers_scheduler.scheduler_task(app))
            
            print("\n🚀 Bot started! Listening for messages...\n")
            
            # Keep the bot running until shutdown signal
            await shutdown_event.wait()
            
            print("\n\n👋 Bot stopped")
            if scheduler_task:
                scheduler_task.cancel()
                try:
                    await scheduler_task
                except asyncio.CancelledError:
                    pass
                    
    except Exception as e:
        if "msg_id is too low" in str(e) or "BadMsgNotification" in str(e):
            print("❌ Time synchronization error. Please check system time.")
            print("💡 Try: docker exec -it <container> chronyc -a makestep")
            raise
        else:
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
