# 🎉 TG Subs Bot - Complete Setup Guide

Welcome to your complete Telegram Subscription Bot system! This bot manages Stremio addon subscriptions with payment verification and voucher/gift card automation.

---

## 📁 Project Structure

```
TG Subs/
├── main.py                  # Main bot entry point
├── config.py               # Configuration settings
├── database.py             # MongoDB database handler
├── handlers_subscription.py # User subscription handlers
├── handlers_payment.py      # Payment & code submission handlers
├── handlers_admin.py        # Admin management handlers
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
├── .env                    # Your configuration (create this)
│
├── README.md               # Full documentation
├── QUICKSTART.md           # Quick start guide
├── ADMIN_COMMANDS.md       # Admin commands reference
└── LICENSE                 # License file
```

---

## 🔧 Setup Instructions

### 1️⃣ Prerequisites
- Python 3.7+
- Git
- MongoDB account (free at mongodb.com)
- Telegram account

### 2️⃣ Clone & Setup Repository
```bash
cd "C:\Users\wisewoods399\Documents\Github\TG Subs"
```

### 3️⃣ Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 5️⃣ Get Credentials

#### Telegram Bot Token
- Open Telegram and search for **@BotFather**
- Type `/newbot`
- Follow the steps
- Copy your bot token

#### Telegram API Credentials
- Visit https://my.telegram.org
- Login with your account
- Create an app in "API development tools"
- Copy API_ID and API_HASH

#### Your User ID
- Search for **@userinfobot**
- Type `/start`
- This is your OWNER_ID

#### Group ID
- Add bot to your group
- Send `/start`
- Check logs or use a debug bot to get group ID

#### MongoDB URI
- Go to https://mongodb.com/cloud/atlas
- Create free account
- Create cluster
- Get connection string (MongoDB URI)

### 6️⃣ Configure Bot

1. Create `.env` file:
```bash
copy .env.example .env
```

2. Edit `.env` with your credentials:
```env
BOT_TOKEN=YOUR_TOKEN_HERE
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
OWNER_ID=YOUR_USER_ID
ADMIN_IDS=YOUR_USER_ID,OTHER_ADMINS
SUBSCRIPTION_GROUP_ID=-100YOUR_GROUP_ID
MONGODB_URI=YOUR_MONGODB_URI
```

### 7️⃣ Run the Bot
```bash
python main.py
```

✅ **Bot is running!** You should see:
```
==================================================
🤖 Telegram Subscription Bot Initializing...
==================================================
✅ Database connected successfully!
📋 Initializing default subscription plans...
   ✅ Added 15 days plan (₹30)
   ✅ Added 30 days plan (₹60)
   ✅ Added 60 days plan (₹80)
   ✅ Added 90 days plan (₹100)

==================================================
✅ Bot is ready!
==================================================

🚀 Bot started! Listening for messages...
```

---

## 🎯 First Steps

### Add Bot to Group
1. Find your bot on Telegram by its username
2. Add to your subscription group
3. Make it **admin** (can send messages, invite users)

### Test the Bot
1. Send `/start` to the bot in private chat
2. Select a subscription plan
3. If set AUTO_APPROVE_VOUCHERS=true, use a test voucher code

### Create Admin Vouchers
1. Send `/admin` to the bot (private chat)
2. Click "Generate Vouchers"
3. Send: `/genvouch 5 15` (creates 5 vouchers for 15 days)
4. Bot sends you the codes in DM

### Test Full User Flow
1. Open another Telegram account / ask a friend
2. Find bot and type `/start`
3. Select a plan
4. Submit a voucher code
5. ✅ Subscription activated!

---

## 📊 Features & Capabilities

### For Users 👥
- ✅ Browse subscription plans
- ✅ Pay via screenshot
- ✅ Use voucher codes (instant activation)
- ✅ Use Amazon gift card codes
- ✅ Check subscription status
- ✅ Extend subscription

### For Admins 🎛️
- ✅ Manage subscription plans (add/delete)
- ✅ Generate unlimited voucher codes
- ✅ Manage Amazon gift card inventory
- ✅ Approve/reject payments
- ✅ Extend/revoke user subscriptions
- ✅ View detailed statistics
- ✅ Track revenue and usage

### Payment Methods
1. **Screenshot Upload** - User sends payment proof, admin approves
2. **Voucher Codes** - Auto-approval (configurable)
3. **Gift Card Codes** - Admin approval required

---

## 💾 Database Collections

Your MongoDB will have these collections:

| Collection | Purpose |
|-----------|---------|
| `users` | User profiles and metadata |
| `subscriptions` | Active user subscriptions |
| `plans` | Subscription plan definitions |
| `vouchers` | Voucher codes for distribution |
| `giftcards` | Amazon gift card codes |
| `payments` | Payment requests and history |

---

## 🔐 Security Features

✅ **Admin-Only Commands**
- Only IDs in ADMIN_IDS can use `/admin` commands

✅ **Secure Codes**
- Gift card codes partially masked in logs
- Voucher codes tracked properly

✅ **Payment Verification**
- Screenshots forwarded only to admins
- Each payment request tracked

✅ **User Data**
- Secure MongoDB storage
- No payment data stored in logs

---

## 📱 User Flow Diagram

```
User /start
    ↓
Shows Plans → User selects → Payment Method
    ↓
Screen/Code/GiftCard
    ↓
Admin Notification
    ↓
Admin Approves ✅
    ↓
Subscription Activated ✅
    ↓
User invited to group
    ↓
Access to Stremio addon ✅
```

---

## 🛠️ Common Admin Tasks

### Task 1: Weekly Voucher Promotion
```
/genvouch 50 30
(Create 50 vouchers for 30-day subscriptions)
```

### Task 2: Manage Expiring Users
```
/admin → Statistics
Review expiring subscriptions
/extend <user_id> 30
```

### Task 3: Add Gift Card Codes
```
/addgiftcard ABC1234XYZ 500
/addgiftcard ABCDEF5678 1000
(Admin users can now submit these codes)
```

### Task 4: Check Revenue
```
/admin → Statistics
Monitor plan popularity
Track voucher/gift card usage
```

---

## 🆘 Troubleshooting

### Bot Doesn't Start
```
Error: Database connection failed
→ Check MongoDB URI in .env
→ Test connection: mongodb+srv://user:pass@...
```

### "Access Denied" on /admin
```
Solution: User ID not in ADMIN_IDS
→ Edit .env and add your admin ID
→ Restart bot
```

### Bot Can't Send Group Invites
```
Solution: Bot not admin in group
→ Make bot admin in subscription group
→ Give it permission to invite users
```

### Voucher Code Not Working
```
Solution: Code already used or doesn't exist
→ Check via admin → vouchers
→ Generate new codes if needed
```

### Database Quota Error
```
Solution: MongoDB storage/query limit
→ Upgrade MongoDB tier
→ Or delete old payment records
```

---

## 📈 Monitoring & Maintenance

### Daily
- Check for approval notifications
- Review new payment requests
- Monitor bot logs

### Weekly
- Generate promotion vouchers
- Check statistics for trends
- Extend subscriptions for loyal users

### Monthly
- Database cleanup (archive old payments)
- Security audit
- Backup MongoDB export
- Plan pricing review

---

## 📚 Documentation Guide

| Document | For | Purpose |
|----------|-----|---------|
| **README.md** | Everyone | Full feature documentation |
| **QUICKSTART.md** | New users | Get started in 5 minutes |
| **ADMIN_COMMANDS.md** | Admins | Complete command reference |
| **.env.example** | Setup | Configuration template |
| **LICENSE** | Legal | Usage rights |

---

## 🚀 Advanced Features (Future)

Consider adding:
- ⏳ Subscription auto-renewal reminders
- 💳 Direct payment gateway integration (Razorpay, Stripe)
- 📈 Detailed analytics dashboard
- 🎁 Referral program
- 🔔 Subscription alerts
- 📧 Email notifications

---

## 💬 Support

If you encounter issues:

1. **Check logs**: Look for error messages when bot starts
2. **Review docs**: See README.md and ADMIN_COMMANDS.md
3. **Test manually**: Try commands one by one
4. **Verify credentials**: Double-check all .env variables

---

## 🎉 Ready to Go!

Your Telegram Subscription Bot is now **fully set up and running**! 

You can now:
✅ Accept payments  
✅ Manage subscriptions  
✅ Generate vouchers  
✅ Track revenue  
✅ Grow your subscriber base  

**Happy selling!** 🚀

---

**Version**: 1.0.0  
**Last Updated**: March 31, 2025  
**License**: MIT
