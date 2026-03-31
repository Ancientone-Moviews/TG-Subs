# 🤖 Telegram Premium Channel Bot

A complete Telegram bot for managing premium channel access with **anonymous mode** and **privacy protection**. Supports payment verification via payment screenshots and Amazon Gift Card/Voucher codes with admin approval required for all activations. Includes automatic expiry management and removal for invalid payments.

## ✨ Features

- ✅ Premium channel subscription management with flexible plans
- 🔒 **Anonymous mode** - User privacy protection
- 👤 **Admin-controlled access** - Manual approval for all subscriptions
- 💳 Payment verification via screenshot uploads (admin approval required)
- 🎁 Voucher code generation and admin approval
- 🛍️ Amazon Gift Card code management with admin verification
- 👥 User management and subscription tracking
- 📊 Admin statistics and reporting
- 🔐 Secure admin-only controls
- 🌍 MongoDB database integration
- 📱 Clean, user-friendly interface
- ⏰ **Automatic expiry reminders** (24 hours before)
- 🗑️ **Automatic group removal** (at expiry + invalid payments)
- 🎉 **Renewal notifications** (within 7 days)
- � **Logs channel** for payment receipts and renewal tracking
- �🔍 **Manual approval mode** for all payments (no auto-activation)
## 🔒 Privacy & Anonymous Mode

This bot is designed for channel administrators who prioritize user privacy:

- **Anonymous Access**: Users can access premium content without revealing personal information
- **Admin-Controlled**: All subscriptions require manual admin approval
- **Secure Payments**: Multiple payment methods with verification
- **Privacy Protection**: User data is handled securely with admin oversight
- **Flexible Management**: Admins have full control over access and subscriptions
## 📋 Subscription Plans

Default plans (customizable):
- **15 Days** - ₹30
- **30 Days** - ₹60
- **60 Days** - ₹80
- **90 Days** - ₹100

## 🚀 Installation

### Prerequisites
- Python 3.7+
- MongoDB database (free tier at mongodb.com)
- Telegram Bot Token (@BotFather)
- Telegram API credentials (https://my.telegram.org)

### Step 1: Clone the repository
```bash
git clone https://github.com/yourusername/tg-subs.git
cd tg-subs
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure the bot
1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
OWNER_ID=YOUR_USER_ID
# Logs Channel (for payment receipts and renewal logs)
LOGS_CHANNEL_ID=-1001234567890
```

### Step 4: Run the bot
```bash
cd bot
python main.py
```

### Step 5: Docker Deployment (Optional)
For containerized deployment:

```bash
# Build the Docker image
docker build -t tg-premium-bot .

# Run the container
docker run -d --name tg-bot \
  -e BOT_TOKEN=your_bot_token \
  -e API_ID=your_api_id \
  -e API_HASH=your_api_hash \
  tg-premium-bot
```

**Environment Variables**: Pass all `.env` variables as `-e` flags or use `--env-file .env`

### Docker Troubleshooting

**Time Synchronization Error:**
If you get `msg_id is too low` error, the container's system time is out of sync. The Dockerfile includes automatic time sync, but you can also run:

```bash
# Manual time sync in running container
docker exec -it tg-bot ntpdate -u pool.ntp.org

# Or rebuild with fresh time sync
docker build --no-cache -t tg-premium-bot .
```

**Environment File:**
Create a `.env` file in the project root with your bot credentials before building.

## 📖 Usage Guide

### For Users

#### Starting the bot
```
/start
```

**First-time users** will see available subscription plans:
- Select a plan
- Follow payment instructions
- Send Amazon Gift Card screenshot or voucher code
- Wait for admin approval

**Existing subscribers** can:
- View subscription status
- Extend subscription
- Manage account

#### Payment Methods

1. **Screenshot**: Send payment screenshot for manual verification
2. **Voucher Code**: Use voucher codes for automatic activation
3. **Gift Card Code**: Submit Amazon Gift Card codes for activation

### For Admins

#### Admin Panel
```
/admin
```

Menu options:
- 📋 **Manage Plans** - Add/remove subscription plans
- 👥 **Manage Users** - View and manage user subscriptions
- 🎁 **Generate Vouchers** - Generate voucher codes
- 🛍️ **Manage Gift Cards** - Add/remove gift card codes
- 📊 **Statistics** - View bot statistics

#### Admin Commands

##### Plan Management
```bash
/addplan <days> <price>
# Example: /addplan 15 30 (15 days for ₹30)

/deleteplan <plan_id>
```

##### User Management
```bash
/extend <user_id> <days>
# Example: /extend 123456789 30 (Add 30 days to user)

/revoke <user_id>
# Revoke user subscription
```

##### Voucher Management
```bash
/genvouch <count> <days>
# Example: /genvouch 10 30 (Generate 10 vouchers for 30-day plans)
```

##### Gift Card Management
```bash
/addgiftcard <code> <amount>
# Example: /addgiftcard ABCD1234WXYZ 500 (Add ₹500 gift card)

/deletegiftcard <code>
# Remove gift card code
```

#### Payment Approval
When users submit payment screenshots:
1. Admin receives notification with screenshot
2. Click **✅ Approve** to activate subscription
3. Click **❌ Reject** to reject payment

## 📊 Data Structure

### Collections (MongoDB)

**users** - User profiles
- `_id`: User ID
- `first_name`, `username`
- `created_at`, `last_interaction`

**subscriptions** - Active subscriptions
- `user_id`: Linked user
- `plan_id`: Plan ID
- `days`: Duration in days
- `expiry_date`: Expiration date
- `status`: active/expired
- `created_at`, `updated_at`

**plans** - Subscription plans
- `days`: Plan duration
- `price`: Price in INR
- `created_at`

**vouchers** - Voucher codes
- `code`: Unique voucher code
- `days`: Subscription days
- `is_active`: Available for use
- `used_by`: User ID (if used)
- `used_at`: Usage timestamp

**giftcards** - Gift card codes
- `code`: Amazon gift card code
- `amount`: Card value in INR
- `is_active`: Available for use
- `used_by`: User ID (if used)
- `used_at`: Usage timestamp

**payments** - Payment requests
- `user_id`: User making payment
- `amount`: Payment amount
- `method`: screenshot/voucher/giftcard
- `status`: pending/approved/rejected
- `created_at`

## ⚙️ Configuration

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | - |
| `API_ID` | Telegram API ID | - |
| `API_HASH` | Telegram API Hash | - |
| `OWNER_ID` | Bot owner user ID | - |
| `ADMIN_IDS` | Admin user IDs (comma-separated) | - |
| `SUBSCRIPTION_GROUP_ID` | Group ID for subscriptions | - |
| `SUBSCRIPTION_GROUP_NAME` | Display name of subscription group | - |
| `MONGODB_URI` | MongoDB connection string | - |
| `CURRENCY` | Currency symbol | ₹ |
| `AUTO_APPROVE_VOUCHERS` | Auto-approve voucher codes | true |
| `AUTO_APPROVE_GIFTCARDS` | Auto-approve gift cards | true |

## ⏰ Automatic Subscription Management

The bot includes a powerful **Scheduler** that runs in the background to manage subscription lifecycles automatically:

### What the Scheduler Does:

1. **Expiry Reminders** - Sends reminder 24 hours before subscription expires
2. **Automatic Removal** - Removes users from group when subscription expires
3. **Renewal Notifications** - Sends "come back & renew" messages within 7 days

**No configuration needed!** The scheduler automatically runs every 5 minutes and manages everything.

For detailed information, see [SCHEDULER.md](SCHEDULER.md)

---

## 🔒 Security Notes

- Only admins can access `/admin` commands
- Voucher and gift card codes are encrypted in MongoDB
- Payment screenshots are forwarded only to admins
- All user data is stored securely

## 🐛 Troubleshooting

### Bot doesn't start
- Check MongoDB connection string
- Verify bot token is valid
- Ensure API ID and hash are correct

### Messages not sending
- Check if bot is admin in the group
- Verify group ID is correct
- Check Telegram service status

### Database errors
- Verify MongoDB URI
- Check network connectivity
- Ensure database exists

### Scheduler Issues
- Check bot logs for error messages
- Verify bot can send DMs to users
- Ensure group ID is correct for removals
- See [SCHEDULER.md](SCHEDULER.md) for troubleshooting

## 📝 License

MIT License - Feel free to modify and distribute

## 👥 Support

For issues and feature requests, create an issue on GitHub


**Made by**: **Ancient One** ([@Moview_S](https://t.me/moview_s))
**Last Updated**: March 2026
