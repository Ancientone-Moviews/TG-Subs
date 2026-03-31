# ⏰ Scheduler & Auto-Removal Features

Your bot now includes powerful automatic features for managing subscription lifecycles!

## 🎯 Features Overview

### 1️⃣ **Expiry Reminders**
Automatically remind users 24 hours before their subscription expires

### 2️⃣ **Auto-Removal from Group**
Automatically remove expired users from the subscription group

### 3️⃣ **Renewal Notifications**
Send special "come back" messages to encourage renewal

---

## 🔄 How It Works

### Timeline

```
Day 1-89 of Subscription
├─ Active subscription
└─ User has full access to group

Day 89 (24 hours before expiry)
├─ 📢 Reminder notification sent
├─ Shows expiry date
└─ Prompts to renew (/start)

Day 90 (Expiry Time)
├─ 24-hour period passes
├─ 🗑️ User automatically removed from group
├─ ❌ Expiry notification sent
└─ Unban immediately (can rejoin if renewed)

After Removal (Within 7 days)
├─ 🎉 "Come back & renew" notification sent
└─ Special renewal message with incentive
```

---

## ⚙️ Configuration

### Scheduler Interval
Edit `handlers_scheduler.py` to change check frequency:

```python
interval = 300  # Check every 5 minutes
# Set to:
# 60   = Check every minute
# 300  = Check every 5 minutes (default)
# 600  = Check every 10 minutes
# 3600 = Check every hour
```

### Reminder Hours
Edit `handlers_scheduler.py` to change when reminders are sent:

```python
expiring_subs = await db.get_expiring_subscriptions(hours=24)
# Change 24 to:
# 12  = Remind 12 hours before expiry
# 24  = Remind 24 hours before expiry (default)
# 48  = Remind 48 hours before expiry
```

---

## 📨 Messages Sent

### 24-Hour Expiry Reminder

```
⏰ Subscription Expiring Soon!

Your Stremio subscription expires in 1 day

Expiry Date: 2026-04-30 15:45 UTC

Don't lose access! Renew your subscription now:
/start
```

### Expiry Notification (When Removed)

```
❌ Subscription Expired

Your subscription expired on 2026-05-01 15:45 UTC

You have been removed from Stremio Private Group.

Renew your subscription to regain access:
/start
```

### Renewal Invitation (Within 7 Days)

```
🎉 Come Back & Renew!

Your subscription has expired.

Special: Renew anytime to get the latest plans!

Select from our plans:
/start
```

---

## 🚀 Automatic Processes

### Every 5 Minutes, the Bot:

1. **Checks for expiring subscriptions**
   ```
   Find subscriptions expiring in next 24 hours
   ↓
   Send reminder notification
   ↓
   Mark reminder as sent
   ```

2. **Checks for expired subscriptions**
   ```
   Find subscriptions past expiry date
   ↓
   Ban user from group (1 second)
   ↓
   Unban user (so they can join again)
   ↓
   Send expiry notification
   ↓
   Mark as processed
   ```

3. **Checks for renewal opportunities**
   ```
   Find recently removed users
   ↓
   Send "come back" notification
   ↓
   Mark notification as sent
   ```

---

## 📊 Database Fields

### Subscriptions Collection

New fields added:

| Field | Type | Purpose |
|-------|------|---------|
| `reminder_sent` | Boolean | Tracks if 24hr reminder was sent |
| `processed` | Boolean | Tracks if user was removed |
| `removed_at` | DateTime | When user was removed |
| `renewal_notified` | Boolean | Tracks if renewal message was sent |

### Example Subscription Document

```json
{
  "user_id": 123456789,
  "plan_id": "plan_123",
  "days": 30,
  "expiry_date": "2026-04-30T15:45:00",
  "status": "active",
  "created_at": "2026-03-31T15:45:00",
  "reminder_sent": false,
  "processed": false,
  "removed_at": null,
  "renewal_notified": false
}
```

---

## 🔍 Monitoring the Scheduler

### Check Bot Logs

Watch for scheduler messages:

```
📅 Running scheduled checks at 2026-03-31 16:00:00 UTC
📢 Found 5 subscriptions expiring soon
✅ Reminder sent to user 123456789
...
🔄 Processing 2 expired subscriptions
✅ Removed expired user 987654321 from group
...
✓ Checks completed. Next check in 300 seconds
```

---

## 🎮 Manual Testing

### Test Reminder Manually

Create a test subscription that expires in 1 minute:

```python
# Pseudo code for testing
import asyncio
from datetime import datetime, timedelta

# Create subscription expiring in 1 minute
now = datetime.utcnow()
test_expiry = now + timedelta(minutes=1)

# The scheduler will check in 5 minutes
# You'll see the reminder being sent in logs
```

### Test User Removal Manually

```bash
# Use admin command to revoke
/revoke 123456789

# Or extend with negative days (not recommended)
# The scheduler will process on next check
```

---

## ⚙️ Advanced Configuration

### Adjust Check Frequency by Tier

**Small Bot (< 100 users)**
```python
interval = 600  # Check every 10 minutes
```

**Medium Bot (100-1000 users)**
```python
interval = 300  # Check every 5 minutes (default)
```

**Large Bot (1000+ users)**
```python
interval = 60  # Check every minute
```

### Custom Reminder Times

Edit `handlers_scheduler.py`:

```python
# Current: 24 hours before
expiring_subs = await db.get_expiring_subscriptions(hours=24)

# For multiple reminders, add this function:
async def check_and_remind_expiring(client: Client, hours_before: int):
    expiring_subs = await db.get_expiring_subscriptions(hours=hours_before)
    # ... send different message based on hours_before
```

---

## 🛡️ Error Handling

### Bot Gracefully Handles:

✅ User already removed from group  
✅ User has no messages enabled  
✅ Group no longer exists  
✅ User ID invalid  
✅ Database connection issues  

### Auto-Retry:

If error occurs:
- Logs the error
- Continues with next user
- Retries after 60 seconds
- Never stops the bot

---

## 📈 Statistics Tracking

Monitor scheduler effectiveness:

```
Total Reminders Sent This Week: 50
Total Users Removed This Week: 45
Renewal Rate (Renewed after removal): 28%
Average Time to Renew: 2.3 days
```

To track, add to admin panel:
```
/admin → Statistics → Scheduler Stats
```

---

## 🔔 Notification Customization

### Edit Reminder Message

In `handlers_scheduler.py`, modify:

```python
reminder_text = (
    f"⏰ <b>Subscription Expiring Soon!</b>\n\n"
    f"Your Stremio subscription expires in <b>{time_str}</b>\n\n"
    f"<b>Expiry Date:</b> {expiry_str}\n\n"
    f"<b>Don't lose access!</b> Renew your subscription now:\n"
    f"/start"
)

# Customize as needed:
# - Add special offers
# - Add referral links
# - Change emoji and formatting
# - Add urgency messaging
```

### Edit Removal Message

```python
removal_text = (
    f"❌ <b>Subscription Expired</b>\n\n"
    f"Your subscription expired on <b>{expiry_str}</b>\n\n"
    f"You have been removed from {config.SUBSCRIPTION_GROUP_NAME}.\n\n"
    f"<b>Renew your subscription to regain access:</b>\n"
    f"/start"
)
```

---

## 🚨 Troubleshooting

### Reminders Not Sending

**Check:**
1. Is bot running? (Check console)
2. Are subscriptions actually expiring? (Check DB)
3. Can bot send DMs? (User may have blocked or closed DMs)
4. Is reminder_sent flag stuck? (Check database manually)

**Solution:**
```python
# Reset reminder flag in MongoDB
db.subscriptions.updateMany(
    { reminder_sent: true },
    { $set: { reminder_sent: false } }
)
```

### Users Not Being Removed

**Check:**
1. Is bot admin in group?
2. Is subscriber actually removed? (Check group members)
3. Is bot blocked? (Check error logs)

### Scheduler Stopped

**Check:**
1. Check bot logs for errors
2. Restart bot: `python main.py`
3. Check database connection
4. Monitor task status

---

## 📱 User Experience

### From User's Perspective

**Day 1-89 of Subscription:**
```
✅ Has access to group
✅ Can see all content
✅ Everything normal
```

**Day 90 (Expiry Date - 24 hours):**
```
📢 Receives reminder notification
   "Your subscription expires in 1 day"
   Option to /start and renew
```

**Day 90 (Expiry Time):**
```
❌ Gets removed from group
❌ Receives expiry notification
```

**Day 90-97 (Within 7 days):**
```
🎉 Receives renewal invitation
   "Come back & renew!"
   Special renewal incentive
```

**After Renewal:**
```
✅ Gets new expiry date
✅ Re-added to group
✅ Access restored
```

---

## 💡 Best Practices

1. **Monitor Logs** - Check schedule runs regularly
2. **Test Thoroughly** - Create test accounts to verify flow
3. **Customize Messages** - Make them friendly and compelling
4. **Track Renewals** - Monitor how many users renew
5. **Adjust Timing** - If too many complaints, add more reminders
6. **Backup Database** - Ensure subscriptions aren't lost
7. **Set Proper Checks** - Bigger bots need more frequent checks

---

## 📚 Related Documentation

- [ADMIN_COMMANDS.md](ADMIN_COMMANDS.md) - Admin management
- [README.md](README.md) - Full features
- [SETUP.md](SETUP.md) - Initial setup
- [database.py](database.py) - Database schema

---

## 🎉 You're All Set!

Your bot now has:
- ✅ Automatic expiry reminders (24 hours before)
- ✅ Automatic group removal (at expiry)
- ✅ Renewal notifications (within 7 days)
- ✅ Complete automation (no manual work needed)

**The scheduler runs automatically in the background. No additional setup required!**

---

**Last Updated**: March 31, 2026  
**Feature Status**: ✅ Active & Running
