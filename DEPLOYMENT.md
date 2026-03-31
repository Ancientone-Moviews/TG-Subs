# 🌐 Deployment Guide

Optional guide for deploying TG Subs bot to cloud platforms for 24/7 uptime.

---

## 📋 Options

| Platform | Cost | Ease | Performance |
|----------|------|------|-------------|
| **Local PC** | Free | ⭐⭐ | Good (Always on) |
| **Heroku** | $7/mo | ⭐⭐⭐ | Good |
| **Railway** | $5/mo | ⭐⭐ | Good |
| **Render** | Free+ | ⭐⭐⭐⭐ | Good |
| **AWS EC2** | $5-15/mo | ⭐ | Excellent |
| **DigitalOcean** | $4/mo | ⭐⭐ | Good |

---

## 🔧 Local Deployment (Recommended for Testing)

### Windows PC
```bash
# In Task Scheduler, create task:
Program: C:\python\python.exe
Arguments: C:\path\to\main.py
Start in: C:\path\to\project

# Run at startup
```

### Mac/Linux
```bash
# Use systemd service or cron

# Create /etc/systemd/system/tg-subs.service:
[Unit]
Description=Telegram Subscription Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/tg-subs
ExecStart=/usr/bin/python3 /home/ubuntu/tg-subs/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable:
sudo systemctl enable tg-subs
sudo systemctl start tg-subs
```

---

## ☁️ Cloud Deployment Options

### Option 1: Render (Recommended - Free Tier)

**Advantages:**
- ✅ Free tier available
- ✅ Auto deploys from GitHub
- ✅ 24/7 uptime
- ✅ Easy setup

**Steps:**

1. Create GitHub repo with your code

2. Push to GitHub:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

3. Go to https://render.com
   - Sign up
   - Click "New +" → "Web Service"
   - Connect GitHub repo
   - Select branch (main)
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python main.py`
   - Add environment variables (your .env contents)
   - Deploy!

**Free tier limits:**
- 750 hours/month (always free)
- 1 instance max
- Restarts weekly

---

### Option 2: Railway

**Steps:**

1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project
4. Click "Deploy from GitHub repo"
5. Select your repo
6. Add environment variables
7. Railway auto-detects and deploys!

**Cost:** Pay as you go (~$5-10/month typical)

---

### Option 3: AWS EC2

**Setup:**

1. Create EC2 instance (t2.micro - Free tier eligible)
2. SSH into instance
3. Install Python:
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

4. Clone repo:
```bash
git clone https://github.com/youruser/tg-subs.git
cd tg-subs
```

5. Install deps:
```bash
pip3 install -r requirements.txt
```

6. Create service file:
```bash
sudo nano /etc/systemd/system/tg-subs.service
```

7. Add content:
```ini
[Unit]
Description=TG Subs Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/tg-subs
ExecStart=/usr/bin/python3 /home/ubuntu/tg-subs/main.py
Restart=always
RestartSec=10
Environment="PATH=/usr/bin"

[Install]
WantedBy=multi-user.target
```

8. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tg-subs
sudo systemctl start tg-subs
```

9. Check status:
```bash
sudo systemctl status tg-subs
```

---

### Option 4: DigitalOcean

**Advantages:**
- 💰 $4-5/month basic droplet
- 🔒 Good security
- 📊 Good performance
- 🎛️ Full control

**Steps:**

1. Create $4 droplet with Ubuntu 20.04
2. SSH: `ssh root@your_ip`
3. Follow AWS EC2 steps above
4. Configure firewall if needed

---

### Option 5: Docker Deployment

**Create Dockerfile:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot code
COPY . .

# Run bot
CMD ["python", "main.py"]
```

**Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - API_ID=${API_ID}
      - API_HASH=${API_HASH}
      - MONGODB_URI=${MONGODB_URI}
    restart: always
```

**Deploy:**
```bash
docker-compose up -d
```

---

## 🚀 GitHub Actions Auto-Deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Render
      run: |
        curl -X POST \
          -H "Authorization: Bearer ${{ secrets.RENDER_DEPLOY_KEY }}" \
          https://api.render.com/deploy/srv-XXXXX
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env file!
echo ".env" >> .gitignore
```

### 2. Use Secrets Manager
- Render: Built-in environment variables
- GitHub: Repository secrets
- AWS: Secrets Manager

### 3. SSL/HTTPS
- Most platforms provide this automatically
- Always use HTTPS webhooks

### 4. Rate Limiting
- Implement in production:
```python
from pyrogram import Client
# Bot automatically throttles
```

### 5. Database Backups
```bash
# MongoDB Atlas auto-backups
# Or manual: mongodump --uri "youruri"
```

---

## 📊 Monitoring

### Uptime Monitoring
- Use uptimerobot.com (free)
- Add monitoring URL to .env

### Logging
```python
# Logs to file
import logging

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO
)
```

### Alert Notifications
```python
# Notify on errors
async def on_error(error):
    await admin_chat.send_message(f"❌ Error: {error}")
```

---

## 💾 Backup Strategy

### MongoDB Backup
```bash
# Once weekly
mongodump --uri "your_uri" -o ./backups/backup_$(date +%Y%m%d)
```

### Code Backup
- Always use GitHub
- Tag releases:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🔧 Maintenance

### Update Dependencies
```bash
pip install --upgrade pyrogram motor pymongo python-dotenv
```

### Monitor Logs
```bash
# Render logs tab
# AWS: tail -f /var/log/your-app.log
# Docker: docker logs -f container_name
```

### Scale if Needed
- Monitor CPU/Memory usage
- Upgrade instance size if >80% usage
- Consider load balancing for high traffic

---

## 📈 Performance Tips

1. **Database Indexing** - Already configured in database.py
2. **Connection Pooling** - Motor handles automatically
3. **Message Caching** - Implement if needed
4. **Rate Limiting** - Telegram SDK handles

---

## 🆘 Troubleshooting Deployment

### Bot crashes on startup
```bash
# Check logs
docker logs container_name
# Or SSH and check systemd
sudo journalctl -u tg-subs -n 50
```

### Database connection timeout
```
→ Check MongoDB URI
→ Add IP to whitelist (MongoDB Atlas)
→ Verify network connectivity
```

### Bot responds slow
```
→ Check database query performance
→ Monitor server CPU/Memory
→ Consider upgrading tier
```

### Can't send messages
```
→ Check bot is still running
→ Verify bot token is valid
→ Check Telegram API status
```

---

## 📱 Mobile Access

For remote access while away:
- SSH app: Termius (iOS/Android)
- Monitor: Grafana Cloud (free tier)
- Bot management: Telegram bot itself

---

## 🎓 Learning Resources

- [Pyrogram Documentation](https://docs.pyrogram.org)
- [MongoDB Docs](https://docs.mongodb.com)
- [Docker Docs](https://docs.docker.com)
- [AWS Tutorial](https://aws.amazon.com/tutorials)

---

## 💡 Recommended Setup

**For Beginners:** Render (free tier)  
**For Growing Business:** DigitalOcean  
**For Scale:** AWS EC2 + Load Balancer  

---

**Last Updated**: March 31, 2025
