# 🚀 Quick Start Guide

## Step 1: Get Your Credentials

### Telegram Bot Token
1. Go to **@BotFather** on Telegram
2. Type `/newbot`
3. Follow the prompts to create your bot
4. Copy the **Bot Token** (example: `123456789:ABCDEfgh...`)

### Telegram API Credentials
1. Visit https://my.telegram.org
2. Log in with your account
3. Go to "API development tools"
4. Create an app
5. Copy **API_ID** and **API_HASH**

### Your User ID
1. Go to **@userinfobot** on Telegram
2. Type `/start`
3. Copy your **User ID** (this will be your OWNER_ID)

### Group ID
1. Add bot to your group
2. Send `/start` in the group
3. Check bot logs for group ID (format: -100123456789)

## Step 2: Setup MongoDB

### Free Option (Recommended):
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a new cluster
4. Get connection string:
   - Click "Connect"
   - Choose "Drivers"
   - Copy the URI
   - Replace `<password>` with your password
5. Add to `.env` as `MONGODB_URI`

### Local Option:
```
MONGODB_URI=mongodb://localhost:27017/?serverSelectionTimeoutMS=5000&connectTimeoutMS=10000
```

## Step 3: Configure Bot

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env`:
```env
BOT_TOKEN=123456789:ABCDEfgh...
API_ID=12345678
API_HASH=abcdef1234567890abcdef
OWNER_ID=987654321
ADMIN_IDS=987654321,111111111
SUBSCRIPTION_GROUP_ID=-100123456789
SUBSCRIPTION_GROUP_NAME=My Stremio Group
MONGODB_URI=mongodb+srv://user:pass@cluster...
```

## Step 4: Install & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

✅ Bot is running!

## Step 5: First Commands

1. **Find your bot on Telegram** by its username (from BotFather)
2. **Start a chat** with your bot
3. **Type `/admin`** to access admin panel
4. **Add default plans**:
   ```
   /addplan 15 30
   /addplan 30 60
   /addplan 60 80
   /addplan 90 100
   ```

## Step 6: Generate Test Vouchers

```
/genvouch 5 15
```

This creates 5 voucher codes for 15-day subscriptions. Bot will DM you the codes.

## Step 7: Test Full Flow

1. **Open another Telegram account** (or ask a friend)
2. **Find your bot** and type `/start`
3. **Select a plan**
4. **Submit a voucher code**
5. **Check if subscription is activated**

## 🎯 Next Steps

### Add Gift Cards:
```
/addgiftcard ABCD1234WXYZ 500
```

### Manage Users:
```
/extend 123456789 30
/revoke 123456789
```

### View Statistics:
```
/admin → Statistics
```

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| "Bot doesn't respond" | Check if bot token is correct |
| "Database error" | Verify MongoDB URI in .env |
| "Bot not in group" | Add bot to group and make admin |
| "No payment received" | Check invoice ID format |

## 📞 Need Help?

1. Check bot logs for error messages
2. Verify all `.env` variables are set
3. Test MongoDB connection: `python -c "import motor.motor_asyncio; print('OK')"`
4. Check Telegram API status

## 🎉 You're All Set!

Your subscription bot is ready to use. Start accepting payments and managing subscriptions! 🚀
