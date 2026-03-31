"""
Main Subscription Handlers
Handles /start, plan selection, and user interactions
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import RPCError
from config import config
from database import SubscriptionDB
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio

IST = ZoneInfo("Asia/Kolkata")

db = None  # Will be initialized in main.py

def set_database(database: SubscriptionDB):
    """Set database instance"""
    global db
    db = database

@Client.on_message(filters.command('start'), group=10)
async def start_command(client: Client, message: Message):
    """Start command - Show subscription options"""
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        
        # Create or get user
        await db.get_or_create_user(user_id, first_name, username)
        
        # Check if user has active subscription
        is_subscribed = await db.check_subscription_valid(user_id)
        
        if is_subscribed:
            # User already has subscription
            sub = await db.get_subscription(user_id)
            expiry = sub.get("expiry_date").astimezone(IST).strftime("%Y-%m-%d %H:%M IST")
            
            await message.reply_text(
                f"🎉 <b>Welcome back to {config.SUBSCRIPTION_GROUP_NAME}!</b>\n\n"
                f"Your subscription is active until <b>{expiry}</b>.\n\n"
                f"<b>Options:</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Extend Subscription", callback_data="extend_sub")],
                    [InlineKeyboardButton("ℹ️ My Subscription Info", callback_data="sub_info")],
                ]),
                quote=True
            )
        else:
            # Show subscription plans
            await show_subscription_plans(client, message)
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}", quote=True)
        print(f"Error in start_command: {e}")

async def show_subscription_plans(client: Client, message: Message):
    """Display available subscription plans"""
    try:
        plans = await db.get_plans()
        
        if not plans:
            return await message.reply_text(
                "<b>Welcome to Premium Channel Access!</b>\n\n"
                "Currently, no subscription plans are available. Please contact the admin.",
                quote=True
            )
        
        text = (
            "<b>Welcome to Premium Channel Access!</b>\n\n"
            "Access to premium content requires an active subscription.\n"
            "Please select a subscription plan below to continue:\n\n"
        )
        
        keyboard = []
        for plan in plans:
            keyboard.append([
                InlineKeyboardButton(
                    f"📅 {plan['days']} Days - {config.CURRENCY}{plan['price']}",
                    callback_data=f"select_plan_{plan['_id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🎁 Use Voucher Code", callback_data="use_voucher"),
            InlineKeyboardButton("🛍️ Gift Card Code", callback_data="use_giftcard"),
        ])
        
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            quote=True
        )
    
    except Exception as e:
        await message.reply_text(f"❌ Error loading plans: {str(e)}", quote=True)
        print(f"Error in show_subscription_plans: {e}")

@Client.on_callback_query(filters.regex(r"^select_plan_"))
async def select_plan(client: Client, callback_query: CallbackQuery):
    """Handle plan selection"""
    try:
        plan_id = callback_query.matches[0].string.split("_")[2]
        plans = await db.get_plans()
        plan = next((p for p in plans if p["_id"] == plan_id), None)
        
        if not plan:
            return await callback_query.answer("Plan not found", show_alert=True)
        
        user_id = callback_query.from_user.id
        await db.get_or_create_user(user_id, callback_query.from_user.first_name, callback_query.from_user.username)
        
        # Calculate expiry in IST
        now = datetime.now(IST)
        expiry = now + timedelta(days=plan["days"])
        expiry_str = expiry.strftime("%Y-%m-%d %H:%M IST")
        
        text = (
            f"<b>✅ Plan Selected: {plan['days']} Days</b>\n\n"
            f"<b>💰 Price:</b> {config.CURRENCY}{plan['price']}\n"
            f"<b>📅 Expiry (if approved now):</b> {expiry_str}\n\n"
            f"<b>📋 Payment Instructions:</b>\n\n"
            f"<b>Payments accepted only via Amazon Gift Card</b>\n\n"
            f"1. Pay {config.CURRENCY}{plan['price']} via Amazon Gift Card to the admin.\n"
            f"2. Send your payment screenshot or gift card code directly here (in this chat).\n"
            f"   The admin will review and activate your subscription.\n\n"
            f"<i>Your subscription will start immediately after approval.</i>"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ])
        
        # Send DM with payment instructions
        try:
            await client.send_message(user_id, text, reply_markup=keyboard)
            await callback_query.answer("✅ Check your DM for payment instructions!", show_alert=True)
        except RPCError as e:
            await callback_query.message.reply_text(
                text + "\n\n⚠️ <i>Please start a DM with the bot first, then send your payment screenshot there.</i>",
                reply_markup=keyboard,
                quote=True
            )
            await callback_query.answer()
        
        # Store payment request
        await db.create_payment_request(user_id, plan_id, plan["price"], "screenshot")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error in select_plan: {e}")

@Client.on_callback_query(filters.regex(r"^use_voucher$"))
async def use_voucher_request(client: Client, callback_query: CallbackQuery):
    """Request user to enter voucher code"""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    await client.send_message(
        user_id,
        "<b>🎁 Voucher Code Activation</b>\n\n"
        "Send your voucher code below:\n\n"
        "<i>Example: ABC123XYZ456</i>",
    )

@Client.on_callback_query(filters.regex(r"^use_giftcard$"))
async def use_giftcard_request(client: Client, callback_query: CallbackQuery):
    """Request user to enter gift card code"""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    await client.send_message(
        user_id,
        "<b>🛍️ Amazon Gift Card Activation</b>\n\n"
        "Send your Amazon Gift Card code below:\n\n"
        "<i>Example: ABCD1234WXYZ5678</i>",
    )

@Client.on_callback_query(filters.regex(r"^cancel_payment$"))
async def cancel_payment(client: Client, callback_query: CallbackQuery):
    """Cancel payment process"""
    user_id = callback_query.from_user.id
    
    # Clear pending payment
    payments = await db.db["payments"].find_one({"user_id": user_id, "status": "pending"})
    if payments:
        await db.db["payments"].delete_one({"_id": payments["_id"]})
    
    await callback_query.answer("Payment cancelled.", show_alert=True)
    try:
        await callback_query.message.delete()
    except:
        pass

@Client.on_callback_query(filters.regex(r"^extend_sub$"))
async def extend_subscription(client: Client, callback_query: CallbackQuery):
    """Extend existing subscription"""
    await callback_query.answer()
    await show_subscription_plans(client, callback_query.message)

@Client.on_callback_query(filters.regex(r"^sub_info$"))
async def show_sub_info(client: Client, callback_query: CallbackQuery):
    """Show user subscription information"""
    try:
        user_id = callback_query.from_user.id
        sub = await db.get_subscription(user_id)
        
        if not sub:
            return await callback_query.answer("No subscription found", show_alert=True)
        
        expiry = sub.get("expiry_date").astimezone(IST).strftime("%Y-%m-%d %H:%M IST")
        days = sub.get("days")
        
        days_left = (sub.get("expiry_date") - datetime.now(IST)).days
        
        text = (
            f"<b>📋 Your Subscription Info</b>\n\n"
            f"<b>Status:</b> ✅ Active\n"
            f"<b>Plan Duration:</b> {days} Days\n"
            f"<b>Expiry Date:</b> {expiry}\n"
            f"<b>Days Remaining:</b> {days_left}\n"
        )
        
        await callback_query.answer()
        await callback_query.message.edit_text(text)
    
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error in show_sub_info: {e}")

print("DEBUG: Subscription Handlers Loaded Successfully!")
