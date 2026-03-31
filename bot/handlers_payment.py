"""
Payment & Voucher Code Handlers
Handles payment screenshots and voucher/gift card code submissions
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import config, log_payment_approved, log_payment_rejected, log_subscription_renewed
from database import SubscriptionDB
from datetime import datetime, timedelta
from tz_utils import tz_manager, ist_now, format_ist_time
import asyncio
import re

db = None  # Will be initialized in main.py

def set_database(database: SubscriptionDB):
    """Set database instance"""
    global db
    db = database

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

@Client.on_message(filters.photo & filters.private, group=20)
async def handle_payment_screenshot(client: Client, message: Message):
    """Handle payment screenshot uploads"""
    try:
        user_id = message.from_user.id
        
        # Check if user has pending payment
        pending = await db.get_pending_payments(user_id)
        
        if not pending:
            return await message.reply_text(
                "ℹ️ We received your photo, but you don't have an active payment request.\n\n"
                "Please use /start to select a subscription plan first.",
                quote=True
            )
        
        # Store screenshot
        payment_id = pending.get("_id")
        
        # Notify admins
        await notify_admins_payment(client, user_id, pending, message.photo.file_id)
        
        await message.reply_text(
            "✅ <b>Screenshot Received!</b>\n\n"
            "Your payment screenshot has been forwarded to the admin for review.\n"
            "You will be notified once it's approved. Thank you! 🙏",
            quote=True
        )
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}", quote=True)
        print(f"Error in handle_payment_screenshot: {e}")

@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'admin']), group=21)
async def handle_code_submission(client: Client, message: Message):
    """Handle voucher and gift card code submissions"""
    try:
        user_id = message.from_user.id
        code = message.text.strip().upper()
        
        # Check if it looks like a voucher/gift card code
        if not re.match(r'^[A-Z0-9]{8,}$', code):
            return
        
        # Check voucher first
        voucher = await db.get_voucher(code)
        if voucher:
            if not voucher.get("is_active"):
                return await message.reply_text(
                    "❌ <b>Invalid Voucher Code</b>\n\n"
                    "This voucher code has already been used.",
                    quote=True
                )
            
            # For vouchers, require admin approval (manual mode)
            days = voucher.get("days")
            
            # Create payment request
            await db.db["payments"].insert_one({
                "user_id": user_id,
                "amount": 0,  # Vouchers don't have amount
                "method": "voucher",
                "voucher_code": code,
                "days": days,
                "status": "pending",
                "created_at": ist_now(),
            })
            
            await message.reply_text(
                "✅ <b>Voucher Code Received!</b>\n\n"
                f"<b>Plan Duration:</b> {days} Days\n\n"
                "Your voucher code has been forwarded to admin for verification.\n"
                "You will be notified once approved.",
                quote=True
            )
            
            # Notify admins
            await notify_admins_voucher(client, user_id, code, days)
            
            return
        
        # Check gift card
        giftcard = await db.get_giftcard(code)
        if giftcard:
            if not giftcard.get("is_active"):
                return await message.reply_text(
                    "❌ <b>Invalid Gift Card Code</b>\n\n"
                    "This gift card code has already been used.",
                    quote=True
                )
            
            # For gift cards, require admin approval
            # Store as payment request with gift card method
            amount = giftcard.get("amount")
            
            # Create payment request
            await db.db["payments"].insert_one({
                "user_id": user_id,
                "amount": amount,
                "method": "giftcard",
                "giftcard_code": code,
                "status": "pending",
                "created_at": ist_now(),
            })
            
            await message.reply_text(
                "✅ <b>Gift Card Code Received!</b>\n\n"
                f"<b>Amount:</b> {config.CURRENCY}{amount}\n\n"
                "Your code has been forwarded to admin for verification.\n"
                "You will be notified once approved.",
                quote=True
            )
            
            # Notify admins
            await notify_admins_giftcard(client, user_id, code, amount)
            
            return
    
    except Exception as e:
        print(f"Error in handle_code_submission: {e}")

async def notify_admins_payment(client: Client, user_id: int, payment: dict, file_id: str):
    """Send payment notification to admins"""
    try:
        user = await client.get_users(user_id)
        user_mention = user.mention
        username_str = f"@{user.username}" if user.username else "N/A"
        
        plans = await db.get_plans()
        plan_id = payment.get("plan_id")
        plan = next((p for p in plans if p["_id"] == plan_id), None)
        plan_info = f"{plan['days']} days - {config.CURRENCY}{plan['price']}" if plan else "Unknown"
        
        text = (
            f"<b>💰 New Payment Screenshot Received</b>\n\n"
            f"<b>👤 User:</b> {user_mention}\n"
            f"<b>🆔 User ID:</b> <code>{user_id}</code>\n"
            f"<b>🔗 Username:</b> {username_str}\n\n"
            f"<b>📦 Plan:</b> {plan_info}\n\n"
            f"Review the screenshot above and approve or reject."
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{user_id}")
            ]
        ])
        
        for admin_id in config.ADMIN_IDS:
            try:
                await client.send_photo(
                    admin_id,
                    file_id,
                    caption=text,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
    
    except Exception as e:
        print(f"Error in notify_admins_payment: {e}")

async def notify_admins_giftcard(client: Client, user_id: int, code: str, amount: float):
    """Send gift card notification to admins"""
    try:
        user = await client.get_users(user_id)
        user_mention = user.mention
        username_str = f"@{user.username}" if user.username else "N/A"
        
        masked_code = "*" * (len(code) - 4) + code[-4:]
        
        text = (
            f"<b>🛍️ New Gift Card Code Received</b>\n\n"
            f"<b>👤 User:</b> {user_mention}\n"
            f"<b>🆔 User ID:</b> <code>{user_id}</code>\n"
            f"<b>🔗 Username:</b> {username_str}\n\n"
            f"<b>💳 Gift Card:</b> <code>{code}</code>\n"
            f"<b>💰 Amount:</b> {config.CURRENCY}{amount}\n\n"
            f"Verify and approve or reject."
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_giftcard_{user_id}_{code}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_giftcard_{user_id}_{code}")
            ]
        ])
        
        for admin_id in config.ADMIN_IDS:
            try:
                await client.send_message(
                    admin_id,
                    text,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
    
    except Exception as e:
        print(f"Error in notify_admins_giftcard: {e}")

async def notify_admins_voucher(client: Client, user_id: int, code: str, days: int):
    """Send voucher notification to admins"""
    try:
        user = await client.get_users(user_id)
        user_mention = user.mention
        username_str = f"@{user.username}" if user.username else "N/A"
        
        text = (
            f"<b>🎫 New Voucher Code Received</b>\n\n"
            f"<b>👤 User:</b> {user_mention}\n"
            f"<b>🆔 User ID:</b> <code>{user_id}</code>\n"
            f"<b>🔗 Username:</b> {username_str}\n\n"
            f"<b>🎫 Voucher:</b> <code>{code}</code>\n"
            f"<b>📅 Days:</b> {days}\n\n"
            f"Verify and approve or reject."
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_voucher_{user_id}_{code}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_voucher_{user_id}_{code}")
            ]
        ])
        
        for admin_id in config.ADMIN_IDS:
            try:
                await client.send_message(
                    admin_id,
                    text,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
    
    except Exception as e:
        print(f"Error in notify_admins_voucher: {e}")

@Client.on_callback_query(filters.regex(r"^approve_giftcard_\d+_.+$"))
async def approve_giftcard(client: Client, callback_query: CallbackQuery):
    """Approve gift card payment"""
    if not await is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        parts = callback_query.matches[0].string.split("_")
        user_id = int(parts[2])
        code = parts[3]
        
        # Get payment info
        payment = await db.db["payments"].find_one({
            "user_id": user_id,
            "giftcard_code": code,
            "status": "pending"
        })
        
        if not payment:
            return await callback_query.answer("Payment not found", show_alert=True)
        
        amount = payment.get("amount")
        
        # Use gift card and create subscription
        used = await db.use_giftcard(code, user_id)
        
        if used:
            # Calculate days based on amount (assuming $10 = 30 days or similar)
            # You may need to adjust this logic based on your pricing
            days = int(amount / 10) * 30  # Example: $10 = 30 days
            
            await db.extend_subscription(user_id, days)
            
            # Mark payment as approved
            now = ist_now()
            await db.db["payments"].update_one(
                {"_id": payment["_id"]},
                {"$set": {"status": "approved", "approved_at": now}}
            )
            
            await callback_query.answer("✅ Gift Card Approved!", show_alert=True)
            
            # Notify user
            sub = await db.get_subscription(user_id)
            expiry = sub.get("expiry_date").astimezone(tz_manager.get_timezone("IST")).strftime("%Y-%m-%d %H:%M IST")
            
            await client.send_message(
                user_id,
                f"🎉 <b>Gift Card Approved!</b>\n\n"
                f"Your subscription is now active for <b>{days} days</b> until <b>{expiry}</b>.\n\n"
                f"Welcome to {config.SUBSCRIPTION_GROUP_NAME}!"
            )
            
            # Try to add to group
            try:
                invite_link = await client.create_chat_invite_link(
                    chat_id=config.SUBSCRIPTION_GROUP_ID,
                    member_limit=1,
                    expire_date=now + timedelta(hours=1)
                )
                await client.send_message(
                    user_id,
                    f"🔗 <b>Join Group</b>\n\n"
                    f"[Click here to join]({invite_link.invite_link})"
                )
            except:
                pass
            
            # Update message
            await callback_query.message.edit_text("✅ <b>Approved</b>")
            
            # Log to channel
            await log_payment_approved(user_id, "Gift Card", f"{config.CURRENCY}{amount}", callback_query.from_user.id)
            await log_subscription_renewed(user_id, days, expiry, "giftcard")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error approving gift card: {e}")

@Client.on_callback_query(filters.regex(r"^reject_giftcard_\d+_.+$"))
async def reject_giftcard(client: Client, callback_query: CallbackQuery):
    """Reject gift card payment"""
    if not await is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        parts = callback_query.matches[0].string.split("_")
        user_id = int(parts[2])
        code = parts[3]
        
        # Mark payment as rejected
        await db.db["payments"].update_one(
            {"user_id": user_id, "giftcard_code": code, "status": "pending"},
            {"$set": {"status": "rejected", "rejected_at": ist_now()}}
        )
        
        # Mark user for removal (invalid payment)
        await db.mark_user_invalid_payment(user_id)
        
        await callback_query.answer("❌ Gift Card Rejected!", show_alert=True)
        
        # Notify user
        await client.send_message(
            user_id,
            "❌ <b>Gift Card Rejected</b>\n\n"
            "Your gift card code was rejected as invalid. You will be removed from the group."
        )
        
        # Update message
        await callback_query.message.edit_text("❌ <b>Rejected</b>")
        
        # Log to channel
        await log_payment_rejected(user_id, "Gift Card", "Invalid code", callback_query.from_user.id)
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error rejecting gift card: {e}")

@Client.on_callback_query(filters.regex(r"^approve_voucher_\d+_.+$"))
async def approve_voucher(client: Client, callback_query: CallbackQuery):
    """Approve voucher payment"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        parts = callback_query.matches[0].string.split("_")
        user_id = int(parts[2])
        code = parts[3]
        
        # Get payment info
        payment = await db.db["payments"].find_one({
            "user_id": user_id,
            "voucher_code": code,
            "status": "pending"
        })
        
        if not payment:
            return await callback_query.answer("Payment not found", show_alert=True)
        
        days = payment.get("days")
        
        # Use voucher and create subscription
        used = await db.use_voucher(code, user_id)
        
        if used:
            await db.extend_subscription(user_id, days)
            
            # Mark payment as approved
            await db.db["payments"].update_one(
                {"_id": payment["_id"]},
                {"$set": {"status": "approved", "approved_at": ist_now()}}
            )
            
            await callback_query.answer("✅ Voucher Approved!", show_alert=True)
            
            # Notify user
            sub = await db.get_subscription(user_id)
            expiry = format_ist_time(sub.get("expiry_date"))
            
            await client.send_message(
                user_id,
                f"🎉 <b>Voucher Code Approved!</b>\n\n"
                f"Your subscription is now active for <b>{days} days</b> until <b>{expiry}</b>.\n\n"
                f"Welcome to {config.SUBSCRIPTION_GROUP_NAME}!"
            )
            
            # Try to add to group
            try:
                invite_link = await client.create_chat_invite_link(
                    chat_id=config.SUBSCRIPTION_GROUP_ID,
                    member_limit=1,
                    expire_date=ist_now() + timedelta(hours=1)
                )
                await client.send_message(
                    user_id,
                    f"🔗 <b>Join Group</b>\n\n"
                    f"[Click here to join]({invite_link.invite_link})"
                )
            except:
                pass
            
            # Update message
            await callback_query.message.edit_text("✅ <b>Approved</b>")
            
            # Log to channel
            await log_payment_approved(user_id, "Voucher", f"{days} days", callback_query.from_user.id)
            await log_subscription_renewed(user_id, days, expiry, "voucher")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error approving voucher: {e}")

@Client.on_callback_query(filters.regex(r"^reject_voucher_\d+_.+$"))
async def reject_voucher(client: Client, callback_query: CallbackQuery):
    """Reject voucher payment"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        parts = callback_query.matches[0].string.split("_")
        user_id = int(parts[2])
        code = parts[3]
        
        # Mark payment as rejected
        await db.db["payments"].update_one(
            {"user_id": user_id, "voucher_code": code, "status": "pending"},
            {"$set": {"status": "rejected", "rejected_at": ist_now()}}
        )
        
        await callback_query.answer("❌ Voucher Rejected!", show_alert=True)
        
        # Notify user
        await client.send_message(
            user_id,
            "❌ <b>Voucher Code Rejected</b>\n\n"
            "Your voucher code was rejected. Please contact admin for more information."
        )
        
        # Update message
        await callback_query.message.edit_text("❌ <b>Rejected</b>")
        
        # Log to channel
        await log_payment_rejected(user_id, "Voucher", "Invalid or rejected", callback_query.from_user.id)
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error rejecting voucher: {e}")

print("DEBUG: Payment & Voucher Handlers Loaded Successfully!")
