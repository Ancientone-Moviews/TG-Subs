"""
Admin Handlers
Handles admin commands and subscription management
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import config, log_payment_approved, log_payment_rejected, log_subscription_renewed
from database import SubscriptionDB
from datetime import datetime, timedelta
import secrets
import string

db = None  # Will be initialized in main.py

def set_database(database: SubscriptionDB):
    """Set database instance"""
    global db
    db = database

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

@Client.on_message(filters.command('admin') & filters.private, group=5)
async def admin_panel(client: Client, message: Message):
    """Admin control panel"""
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ Access Denied", quote=True)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Manage Plans", callback_data="admin_plans")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("🎁 Generate Vouchers", callback_data="admin_vouchers")],
        [InlineKeyboardButton("🛍️ Manage Gift Cards", callback_data="admin_giftcards")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
    ])
    
    await message.reply_text(
        "🎛️ <b>Admin Control Panel</b>\n\nSelect an option below:",
        reply_markup=keyboard,
        quote=True
    )

@Client.on_callback_query(filters.regex(r"^admin_plans$"))
async def admin_plans(client: Client, callback_query: CallbackQuery):
    """Manage subscription plans"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    plans = await db.get_plans()
    
    text = "<b>📋 Subscription Plans</b>\n\n"
    keyboard_buttons = []
    
    if plans:
        for plan in plans:
            text += f"• <b>{plan['days']} Days</b> - {config.CURRENCY}{plan['price']}\n"
    else:
        text += "No plans found.\n"
    
    text += "\n<b>Commands:</b>\n/addplan &lt;days&gt; &lt;price&gt;\n/deleteplan &lt;plan_id&gt;"
    
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex(r"^admin_users$"))
async def admin_users(client: Client, callback_query: CallbackQuery):
    """Manage users"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    subs = await db.get_active_subscriptions()
    stats = await db.get_stats()
    
    text = (
        "<b>👥 User Management</b>\n\n"
        f"<b>Total Users:</b> {stats['total_users']}\n"
        f"<b>Active Subscriptions:</b> {stats['active_subscriptions']}\n"
        f"<b>Total Subscriptions:</b> {stats['total_subscriptions']}\n\n"
        "<b>Commands:</b>\n"
        "/extend &lt;user_id&gt; &lt;days&gt;\n"
        "/revoke &lt;user_id&gt;"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex(r"^admin_vouchers$"))
async def admin_vouchers(client: Client, callback_query: CallbackQuery):
    """Manage vouchers"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    vouchers = await db.get_all_vouchers()
    active = len([v for v in vouchers if v.get("is_active")])
    used = len(vouchers) - active
    
    text = (
        "<b>🎁 Voucher Code Management</b>\n\n"
        f"<b>Total Codes:</b> {len(vouchers)}\n"
        f"<b>Active:</b> {active}\n"
        f"<b>Used:</b> {used}\n\n"
        "<b>Command:</b>\n"
        "/genvouch &lt;count&gt; &lt;days&gt;\n"
        "Example: /genvouch 10 30"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Codes", callback_data="view_vouchers")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex(r"^admin_giftcards$"))
async def admin_giftcards(client: Client, callback_query: CallbackQuery):
    """Manage gift cards"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    giftcards = await db.get_all_giftcards()
    active = len([g for g in giftcards if g.get("is_active")])
    used = len(giftcards) - active
    
    text = (
        "<b>🛍️ Amazon Gift Card Management</b>\n\n"
        f"<b>Total Codes:</b> {len(giftcards)}\n"
        f"<b>Active:</b> {active}\n"
        f"<b>Used:</b> {used}\n\n"
        "<b>Commands:</b>\n"
        "/addgiftcard &lt;code&gt; &lt;amount&gt;\n"
        "/deletegiftcard &lt;code&gt;"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Cards", callback_data="view_giftcards")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex(r"^admin_stats$"))
async def admin_stats(client: Client, callback_query: CallbackQuery):
    """Show statistics"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    stats = await db.get_stats()
    
    text = (
        "<b>📊 Subscription Statistics</b>\n\n"
        f"<b>Total Users:</b> {stats['total_users']}\n"
        f"<b>Active Subscriptions:</b> {stats['active_subscriptions']}\n"
        f"<b>Total Subscriptions:</b> {stats['total_subscriptions']}\n\n"
        f"<b>Voucher Codes:</b>\n"
        f"  Active: {stats['active_vouchers']}\n"
        f"  Used: {stats['used_vouchers']}\n\n"
        f"<b>Gift Cards:</b>\n"
        f"  Active: {stats['active_giftcards']}\n"
        f"  Used: {stats['used_giftcards']}\n"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex(r"^admin_back$"))
async def admin_back(client: Client, callback_query: CallbackQuery):
    """Back to admin panel"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Manage Plans", callback_data="admin_plans")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("🎁 Generate Vouchers", callback_data="admin_vouchers")],
        [InlineKeyboardButton("🛍️ Manage Gift Cards", callback_data="admin_giftcards")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
    ])
    
    await callback_query.message.edit_text(
        "🎛️ <b>Admin Control Panel</b>\n\nSelect an option below:",
        reply_markup=keyboard
    )
    await callback_query.answer()

@Client.on_message(filters.command('addplan') & filters.private, group=5)
async def add_plan(client: Client, message: Message):
    """Add subscription plan: /addplan <days> <price>"""
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ Access Denied", quote=True)
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid format")
        
        days = int(parts[1])
        price = float(parts[2])
        
        if days <= 0 or price <= 0:
            raise ValueError("Days and price must be positive")
        
        await db.add_plan(days, price)
        
        await message.reply_text(
            f"✅ <b>Plan Added</b>\n\n"
            f"<b>Duration:</b> {days} Days\n"
            f"<b>Price:</b> {config.CURRENCY}{price}",
            quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}\n\nUsage: /addplan &lt;days&gt; &lt;price&gt;", quote=True)

@Client.on_message(filters.command('genvouch') & filters.private, group=5)
async def generate_vouchers(client: Client, message: Message):
    """Generate vouchers: /genvouch <count> <days>"""
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ Access Denied", quote=True)
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid format")
        
        count = int(parts[1])
        days = int(parts[2])
        
        if count <= 0 or count > 100:
            raise ValueError("Count must be between 1 and 100")
        if days <= 0:
            raise ValueError("Days must be positive")
        
        status_msg = await message.reply_text(f"🔄 Generating {count} vouchers...", quote=True)
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            await db.create_voucher(code, days)
            codes.append(code)
        
        # Send codes to admin
        codes_text = "\n".join(codes)
        
        await client.send_message(
            message.from_user.id,
            f"✅ <b>Generated {count} Voucher Codes ({days} days each)</b>\n\n"
            f"<code>{codes_text}</code>\n\n"
            f"<i>Share these with users to activate subscriptions</i>"
        )
        
        await status_msg.delete()
        await message.reply_text(f"✅ Generated {count} vouchers!", quote=True)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}\n\nUsage: /genvouch &lt;count&gt; &lt;days&gt;", quote=True)

@Client.on_message(filters.command('extend') & filters.private, group=5)
async def extend_subscription(client: Client, message: Message):
    """Extend subscription: /extend <user_id> <days>"""
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ Access Denied", quote=True)
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid format")
        
        user_id = int(parts[1])
        days = int(parts[2])
        
        sub = await db.extend_subscription(user_id, days)
        
        if sub:
            expiry = sub.get("expiry_date").strftime("%Y-%m-%d")
            await message.reply_text(
                f"✅ <b>Subscription Extended</b>\n\n"
                f"<b>User:</b> {user_id}\n"
                f"<b>Added:</b> {days} days\n"
                f"<b>New Expiry:</b> {expiry}",
                quote=True
            )
            
            try:
                await client.send_message(user_id, f"🎉 Your subscription extended by {days} days until {expiry}!")
            except:
                pass
        else:
            await message.reply_text("❌ User not found", quote=True)
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}\n\nUsage: /extend &lt;user_id&gt; &lt;days&gt;", quote=True)

@Client.on_callback_query(filters.regex(r"^approve_payment_\d+$"))
async def approve_payment(client: Client, callback_query: CallbackQuery):
    """Approve payment"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        user_id = int(callback_query.matches[0].string.split("_")[2])
        
        # Get payment and plan info
        pending = await db.get_pending_payments(user_id)
        if not pending:
            return await callback_query.answer("Payment not found", show_alert=True)
        
        plan_id = pending.get("plan_id")
        plans = await db.get_plans()
        plan = next((p for p in plans if p["_id"] == plan_id), None)
        
        if plan:
            await db.extend_subscription(user_id, plan["days"])
        
        # Mark payment as approved
        await db.db["payments"].delete_one({"user_id": user_id, "status": "pending"})
        
        await callback_query.answer("✅ Payment Approved!", show_alert=True)
        
        # Notify user
        sub = await db.get_subscription(user_id)
        expiry = sub.get("expiry_date").strftime("%Y-%m-%d %H:%M UTC")
        
        await client.send_message(
            user_id,
            f"🎉 <b>Payment Approved!</b>\n\n"
            f"Your subscription is now active until <b>{expiry}</b> ."
        )
        
        # Update message
        await callback_query.message.edit_caption("✅ <b>Approved</b>")
        
        # Log to channel
        plan_info = f"{plan['days']} days - {config.CURRENCY}{plan['price']}" if plan else "Unknown"
        await log_payment_approved(user_id, "Screenshot", plan_info, callback_query.from_user.id)
        if plan:
            expiry_str = sub.get("expiry_date").strftime("%Y-%m-%d %H:%M UTC")
            await log_subscription_renewed(user_id, plan["days"], expiry_str, "screenshot")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        print(f"Error approving payment: {e}")

@Client.on_callback_query(filters.regex(r"^reject_payment_\d+$"))
async def reject_payment(client: Client, callback_query: CallbackQuery):
    """Reject payment"""
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    
    try:
        user_id = int(callback_query.matches[0].string.split("_")[2])
        
        # Remove pending payment
        await db.db["payments"].delete_one({"user_id": user_id, "status": "pending"})
        
        await callback_query.answer("❌ Payment Rejected!", show_alert=True)
        
        # Notify user
        await client.send_message(
            user_id,
            "❌ <b>Payment Rejected</b>\n\n"
            "Your payment submission was rejected. Please contact admin or try again."
        )
        
        # Update message
        await callback_query.message.edit_caption("❌ <b>Rejected</b>")
        
        # Log to channel
        await log_payment_rejected(user_id, "Screenshot", "Rejected by admin", callback_query.from_user.id)
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

print("DEBUG: Admin Handlers Loaded Successfully!")
