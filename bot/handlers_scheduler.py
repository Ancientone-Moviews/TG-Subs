"""
Scheduler Module - Background Tasks
Handles automated tasks like expiry reminders and user removal
"""

from pyrogram import Client
from config import config, log_user_removed
from database import SubscriptionDB
from datetime import datetime, timedelta
from tz_utils import tz_manager, ist_now, format_ist_time
import asyncio

db = None  # Will be initialized in main.py

def set_database(database: SubscriptionDB):
    """Set database instance"""
    global db
    db = database

async def check_and_remind_expiring(client: Client):
    """Check for subscriptions expiring soon and send reminders"""
    try:
        # Get subscriptions expiring in 24 hours
        expiring_subs = await db.get_expiring_subscriptions(hours=24)
        
        if not expiring_subs:
            print("✓ No subscriptions expiring in next 24 hours")
            return
        
        print(f"📢 Found {len(expiring_subs)} subscriptions expiring soon")
        
        for sub in expiring_subs:
            user_id = sub.get("user_id")
            expiry = sub.get("expiry_date")
            days_left = (expiry - ist_now()).days
            hours_left = ((expiry - ist_now()).total_seconds()) / 3600
            
            expiry_str = expiry.astimezone(tz_manager.get_timezone("IST")).strftime("%Y-%m-%d %H:%M IST")
            
            # Create reminder message
            if days_left > 0:
                time_str = f"{days_left} day(s)"
            else:
                time_str = f"{int(hours_left)} hour(s)"
            
            reminder_text = (
                f"⏰ <b>Subscription Expiring Soon!</b>\n\n"
                f"Your premium channel subscription expires in <b>{time_str}</b>\n\n"
                f"<b>Expiry Date:</b> {expiry_str}\n\n"
                f"<b>Don't lose access!</b> Renew your subscription now:\n"
                f"/start"
            )
            
            try:
                await client.send_message(user_id, reminder_text)
                print(f"✅ Reminder sent to user {user_id}")
                
                # Mark reminder as sent
                await db.mark_reminder_sent(user_id)
                
            except Exception as e:
                print(f"⚠️ Failed to send reminder to {user_id}: {e}")
    
    except Exception as e:
        print(f"❌ Error in check_and_remind_expiring: {e}")

async def check_and_remove_expired(client: Client):
    """Check for expired subscriptions and remove users from group"""
    try:
        # Get all expired subscriptions
        expired_subs = await db.get_expired_subscriptions()
        
        if not expired_subs:
            print("✓ No expired subscriptions to process")
        else:
            print(f"🔄 Processing {len(expired_subs)} expired subscriptions")
            
            for sub in expired_subs:
                user_id = sub.get("user_id")
                expiry = sub.get("expiry_date")
                expiry_str = expiry.strftime("%Y-%m-%d %H:%M UTC")
                
                # Try to remove user from group
                try:
                    await client.ban_chat_member(
                        chat_id=config.SUBSCRIPTION_GROUP_ID,
                        user_id=user_id
                    )
                    
                    # Unban immediately so they can rejoin if they renew
                    await asyncio.sleep(1)
                    await client.unban_chat_member(
                        chat_id=config.SUBSCRIPTION_GROUP_ID,
                        user_id=user_id
                    )
                    
                    print(f"✅ Removed expired user {user_id} from group")
                    
                    # Send user notification
                    try:
                        removal_text = (
                            f"❌ <b>Subscription Expired</b>\n\n"
                            f"Your subscription expired on <b>{expiry_str}</b>\n\n"
                            f"You have been removed from {config.SUBSCRIPTION_GROUP_NAME}.\n\n"
                            f"<b>Renew your subscription to regain access:</b>\n"
                            f"/start"
                        )
                        await client.send_message(user_id, removal_text)
                    except:
                        pass
                    
                    # Mark subscription as processed
                    await db.mark_subscription_processed(user_id)
                    
                    # Log to channel
                    await log_user_removed(user_id, f"Subscription expired on {expiry_str}")
                    
                except Exception as e:
                    print(f"⚠️ Failed to remove user {user_id}: {e}")
        
        # Check for users with invalid payments (rejected Amazon Gift cards)
        invalid_users = await db.get_users_with_invalid_payment()
        
        if not invalid_users:
            print("✓ No users with invalid payments to process")
        else:
            print(f"🔄 Processing {len(invalid_users)} users with invalid payments")
            
            for user in invalid_users:
                user_id = user.get("_id")
                
                # Try to remove user from group
                try:
                    await client.ban_chat_member(
                        chat_id=config.SUBSCRIPTION_GROUP_ID,
                        user_id=user_id
                    )
                    
                    # Unban immediately
                    await asyncio.sleep(1)
                    await client.unban_chat_member(
                        chat_id=config.SUBSCRIPTION_GROUP_ID,
                        user_id=user_id
                    )
                    
                    print(f"✅ Removed user {user_id} for invalid payment from group")
                    
                    # Send user notification
                    try:
                        removal_text = (
                            f"❌ <b>Access Revoked</b>\n\n"
                            f"Your Amazon Gift card was verified as invalid by admin.\n\n"
                            f"You have been removed from {config.SUBSCRIPTION_GROUP_NAME}.\n\n"
                            f"Please submit a valid payment to regain access."
                        )
                        await client.send_message(user_id, removal_text)
                    except:
                        pass
                    
                    # Mark as removed
                    await db.mark_user_removed_for_invalid(user_id)
                    
                    # Log to channel
                    await log_user_removed(user_id, "Invalid Amazon Gift card payment")
                    
                except Exception as e:
                    print(f"⚠️ Failed to remove user {user_id} for invalid payment: {e}")
    
    except Exception as e:
        print(f"❌ Error in check_and_remove_expired: {e}")

async def notify_renewal_available(client: Client):
    """Notify users who have been removed but can renew"""
    try:
        # Get users with processed/expired subscriptions
        expired_users = await db.get_processed_expired_users()
        
        if not expired_users:
            return
        
        print(f"📧 Notifying {len(expired_users)} expired users about renewal")
        
        for user in expired_users:
            if not user:
                continue
                
            user_id = user.get("_id")
            
            try:
                renewal_text = (
                    f"🎉 <b>Come Back & Renew!</b>\n\n"
                    f"Your subscription has expired.\n\n"
                    f"<b>Special: Renew anytime to get the latest plans!</b>\n\n"
                    f"Select from our plans:\n"
                    f"/start"
                )
                await client.send_message(user_id, renewal_text)
                print(f"✅ Renewal notification sent to {user_id}")
                
                # Mark notification as sent
                await db.mark_renewal_notified(user_id)
            except:
                pass
    
    except Exception as e:
        print(f"⚠️ Error in notify_renewal_available: {e}")

async def scheduler_task(client: Client):
    """Main scheduler task - runs periodically"""
    interval = 300  # Check every 5 minutes
    
    print("🕐 Scheduler started - checking every 5 minutes")
    
    while True:
        try:
            print(f"\n📅 Running scheduled checks at {format_ist_time()}")
            
            # Check for subscriptions expiring soon (24 hours)
            await check_and_remind_expiring(client)
            
            await asyncio.sleep(5)
            
            # Check for expired subscriptions and remove from group
            await check_and_remove_expired(client)
            
            await asyncio.sleep(5)
            
            # Notify users about renewal
            await notify_renewal_available(client)
            
            # Wait for next check
            print(f"✓ Checks completed. Next check in {interval} seconds\n")
            await asyncio.sleep(interval)
            
        except asyncio.CancelledError:
            print("🛑 Scheduler stopped")
            break
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)  # Wait before retrying

print("DEBUG: Scheduler Module LOADED SUCCESSFULLY!")
