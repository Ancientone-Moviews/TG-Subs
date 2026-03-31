# 📋 Admin Commands Reference

## Overview
All admin commands must be sent in a **private message (DM)** to the bot. Only user IDs in `ADMIN_IDS` can use these commands.

---

## 🎛️ Main Admin Panel

### Open Admin Panel
```
/admin
```

Shows main menu with options:
- 📋 Manage Plans
- 👥 Manage Users
- 🎁 Generate Vouchers
- 🛍️ Manage Gift Cards
- 📊 Statistics

---

## 📋 Subscription Plans

### Add New Plan
```
/addplan <days> <price>
```

**Examples:**
```
/addplan 15 30      (15 days for ₹30)
/addplan 30 60      (30 days for ₹60)
/addplan 7 15       (7 days for ₹15 - weekly)
/addplan 90 100     (90 days for ₹100)
```

### Delete Plan
```
/deleteplan <plan_id>
```

**Get plan_id from:**
- Open admin panel → "Manage Plans"
- Hover over plan to see ID

---

## 👥 User Management

### Extend Subscription
```
/extend <user_id> <days>
```

**Example:**
```
/extend 123456789 30
```

This **adds 30 days** to user's subscription (if they have active sub, adds to existing expiry; if expired/none, starts fresh).

### Revoke Subscription
```
/revoke <user_id>
```

**Example:**
```
/revoke 123456789
```

This **removes** the user's subscription completely.

**Get user_id:**
- View their profile
- Copy the ID number
- Or use forward feature to see their ID in logs

---

## 🎁 Voucher Codes

### Generate Voucher Codes
```
/genvouch <count> <days>
```

**Parameters:**
- `count`: Number of codes (1-100)
- `days`: Duration for each code

**Examples:**
```
/genvouch 5 15          (5 codes × 15 days each)
/genvouch 10 30         (10 codes × 30 days each)
/genvouch 50 60         (50 codes × 60 days each)
/genvouch 100 90        (100 codes × 90 days each)
```

**What happens:**
1. Bot generates random codes (e.g., ABC123XYZ456)
2. Codes are sent to your DM
3. Copy and share with users
4. Users can submit codes via bot to auto-activate subscriptions

### View Vouchers
From admin panel: `Manage Vouchers` → `View All Codes`

**Shows:**
- All generated codes
- Active/Used status
- Who used each code

---

## 🛍️ Amazon Gift Cards

### Add Gift Card Code
```
/addgiftcard <code> <amount>
```

**Parameters:**
- `code`: Amazon gift card code
- `amount`: Value in ₹ (e.g., 500 for ₹500)

**Examples:**
```
/addgiftcard ABCD1234WXYZ 500       (₹500 card)
/addgiftcard 1234EFGH5678IJKL 1000  (₹1000 card)
```

### Delete Gift Card Code
```
/deletegiftcard <code>
```

**Example:**
```
/deletegiftcard ABCD1234WXYZ
```

### View Gift Cards
From admin panel: `Manage Gift Cards` → `View All Cards`

**Shows:**
- All added gift card codes (masked for security)
- Amount and status
- Who used each card

---

## 📊 Statistics

Open admin panel and click `📊 Statistics`

**Shows:**
- Total users
- Active subscriptions
- Subscription breakdown by plan
- Voucher code usage
- Gift card usage
- Revenue insights

---

## ✅ Approve/Reject Payments

### Auto-Triggered (No command needed)

**When user submits payment:**
1. Screenshot/Gift card forwarded to admin
2. Admin receives notification
3. Click **✅ Approve** button to activate
4. Click **❌ Reject** button to decline

**Auto happens:**
- ✅ Approval: User subscription activated immediately
- ❌ Rejection: User notified, can retry

---

## 🔍 Common Admin Workflows

### Workflow 1: New User Wants Subscription
```
1. User types /start in bot
2. User selects plan
3. User sends payment screenshot
4. Admin receives notification
5. Admin clicks ✅ Approve
6. User subscription activated ✅
```

### Workflow 2: Bulk Generate Free Trial Vouchers
```
1. /genvouch 20 7     (20 codes for 7-day trial)
2. Copy codes from DM
3. Share in announcement/channel
4. Users submit codes to bot
5. Auto-activated ✅
```

### Workflow 3: Extend Expiring Subscriptions
```
1. /admin → Statistics (see expiring soon)
2. /extend <user_id> 30
3. User notified ✅
```

### Workflow 4: Manage Gift Card Pool
```
1. /addgiftcard CODE1 500
2. /addgiftcard CODE2 1000
3. User submits gift card in chat
4. Admin reviews and approves
5. Subscription activated ✅
```

---

## 📈 Monitoring

### Check Statistics Regularly
```
/admin → Statistics
```

Monitor:
- Active subscriptions trend
- Expiring subscriptions
- Payment success rate
- Popular plans

### View All Codes
```
/admin → Vouchers → View All Codes
```

Track:
- Unused vouchers
- Used vouchers & users
- Revenue per code type

---

## ⚠️ Important Notes

1. **Admin Commands are DM-Only**
   - Send commands in private DM to bot
   - Can't use in groups/channels

2. **User IDs Required**
   - Use numeric IDs (e.g., 123456789)
   - Not usernames or names

3. **Codes Are Case-Insensitive**
   - ABC123xyz = ABC123XYZ (same code)

4. **Deletions Are Permanent**
   - Can't undo /deleteplan or /deletegiftcard
   - Be careful!

5. **Approval is Permanent**
   - Can't unapprove payments
   - Only revoke via /revoke if needed

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Command doesn't work | Check you're in DM with bot |
| "Access Denied" | Admin ID not in .env ADMIN_IDS |
| User not found | Verify user ID is correct |
| Plan not deleted | Check plan_id exists |
| Gift card not added | Code already exists or invalid format |

---

## 💡 Pro Tips

1. **Batch generate vouchers** weekly for promotions
2. **Monitor statistics** for revenue trends
3. **Extend expiring subscriptions** to keep users
4. **Keep gift card codes secure** in password manager
5. **Test commands** with test account first
6. **Document revenue** for accounting

---

Last Updated: March 2025
