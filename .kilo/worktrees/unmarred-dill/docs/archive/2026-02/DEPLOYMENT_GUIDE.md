# راهنمای انتقال و استقرار پروژه MAHOUN
**تاریخ**: 1404/12/04 (2026-02-22)

## 🎯 هدف
انتقال پروژه MAHOUN به سرور جدید یا اکانت دیگه

---

## 📦 مرحله 1: آماده‌سازی پروژه برای انتقال

### چک کردن وضعیت Git
```bash
# ببین چه فایل‌هایی uncommitted هستن
git status

# اگه فایل‌های مهم uncommitted داری، commit کن
git add .
git commit -m "Final changes before deployment"

# ببین روی کدوم branch هستی
git branch
```

### پاک کردن فایل‌های غیرضروری
```bash
# پاک کردن cache و temporary files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name ".DS_Store" -delete

# پاک کردن node_modules (می‌تونی بعداً دوباره نصب کنی)
rm -rf frontend/node_modules

# پاک کردن virtual environment (اختیاری)
rm -rf venv .venv env

# پاک کردن test files موقت
rm -f test_*.py debug_*.py run_*.py write_*.py fix_*.py final_test.py
```

---

## 🚀 مرحله 2: روش‌های انتقال

### روش 1: استفاده از Git (پیشنهادی ⭐)

#### اگه پروژه رو روی GitHub/GitLab داری:
```bash
# فقط clone کن روی سرور جدید
git clone https://github.com/your-username/mahoun-platform.git
cd mahoun-platform
```

#### اگه پروژه رو روی Git نداری:
```bash
# 1. ساخت repo جدید روی GitHub/GitLab
# 2. اضافه کردن remote
git remote add origin https://github.com/your-username/mahoun-platform.git

# 3. Push کردن
git push -u origin main

# 4. روی سرور جدید clone کن
git clone https://github.com/your-username/mahoun-platform.git
```

---

### روش 2: استفاده از rsync (برای انتقال مستقیم)

```bash
# از لپتاپ به سرور
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='.hypothesis' \
  --exclude='.pytest_cache' \
  --exclude='*.log' \
  /path/to/mahoun-platform/ \
  user@server:/path/to/destination/
```

---

### روش 3: استفاده از tar.gz (برای انتقال دستی)

```bash
# 1. ساخت آرشیو (روی لپتاپ)
tar -czf mahoun-platform.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='.hypothesis' \
  --exclude='.pytest_cache' \
  mahoun-platform/

# 2. انتقال فایل (یکی از این روش‌ها)
# با scp:
scp mahoun-platform.tar.gz user@server:/path/to/destination/

# یا با USB/Google Drive/etc

# 3. استخراج روی سرور
ssh user@server
cd /path/to/destination/
tar -xzf mahoun-platform.tar.gz
```

---

## ⚙️ مرحله 3: نصب و راه‌اندازی روی سرور جدید

### 1. نصب Dependencies سیستم
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm git

# یا CentOS/RHEL
sudo yum install -y python3.12 python3-pip nodejs npm git
```

### 2. ساخت Virtual Environment
```bash
cd mahoun-platform

# ساخت venv
python3.12 -m venv venv

# فعال کردن
source venv/bin/activate

# نصب dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. نصب Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. کپی و تنظیم .env
```bash
# کپی کردن .env.example
cp .env.example .env

# ویرایش .env
nano .env
```

**مهم**: حتماً این متغیرها رو تنظیم کن:
```bash
# Environment
MAHOUN_ENV=prod  # یا staging

# Security (حتماً تغییر بده!)
SECURITY_JWT_SECRET=$(openssl rand -hex 32)
DB_POSTGRES_PASSWORD=$(openssl rand -base64 32)
DB_NEO4J_PASSWORD=$(openssl rand -base64 32)

# Database flags (اگه دیتابیس نداری)
ENABLE_POSTGRES=false
ENABLE_NEO4J=false
ENABLE_REDIS=false

# CORS (آدرس سرورت)
MAHOUN_ALLOWED_ORIGINS=https://your-domain.com,http://localhost:5173
```

### 5. تست Backend
```bash
# فعال کردن venv
source venv/bin/activate

# اجرای backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# تست در terminal دیگه
curl http://localhost:8000/health
```

### 6. Build Frontend
```bash
cd frontend

# Development mode
npm run dev

# یا Production build
npm run build
# خروجی در frontend/dist/ می‌ره
```

---

## 🔒 مرحله 4: تنظیمات امنیتی (مهم!)

### 1. تغییر Passwords
```bash
# تولید password های قوی
openssl rand -base64 32  # برای PostgreSQL
openssl rand -base64 32  # برای Neo4j
openssl rand -hex 32     # برای JWT Secret
```

### 2. تنظیم Firewall
```bash
# فقط پورت‌های لازم رو باز کن
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Backend (موقت، بعداً با Nginx reverse proxy)
sudo ufw enable
```

### 3. تنظیم SSL (برای production)
```bash
# نصب Certbot
sudo apt install certbot python3-certbot-nginx

# دریافت SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🐳 مرحله 5: استقرار با Docker (اختیاری)

اگه می‌خوای با Docker deploy کنی:

```bash
# Build و اجرا
docker-compose up -d

# چک کردن logs
docker-compose logs -f

# متوقف کردن
docker-compose down
```

---

## 📊 مرحله 6: Monitoring و Logging

### 1. راه‌اندازی Systemd Service (برای production)

```bash
# ساخت service file
sudo nano /etc/systemd/system/mahoun-backend.service
```

محتوای فایل:
```ini
[Unit]
Description=MAHOUN Backend API
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/mahoun-platform
Environment="PATH=/path/to/mahoun-platform/venv/bin"
ExecStart=/path/to/mahoun-platform/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# فعال کردن service
sudo systemctl daemon-reload
sudo systemctl enable mahoun-backend
sudo systemctl start mahoun-backend

# چک کردن status
sudo systemctl status mahoun-backend

# دیدن logs
sudo journalctl -u mahoun-backend -f
```

### 2. راه‌اندازی Nginx Reverse Proxy

```bash
# نصب Nginx
sudo apt install nginx

# ساخت config
sudo nano /etc/nginx/sites-available/mahoun
```

محتوای فایل:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/mahoun-platform/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Metrics
    location /metrics {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
# فعال کردن site
sudo ln -s /etc/nginx/sites-available/mahoun /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ✅ مرحله 7: چک‌لیست نهایی

### قبل از انتقال:
- [ ] همه تغییرات commit شدن
- [ ] `.env` فایل رو کپی نکن (فقط `.env.example`)
- [ ] فایل‌های غیرضروری پاک شدن
- [ ] مستندات به‌روز هستن

### بعد از انتقال:
- [ ] Virtual environment ساخته شد
- [ ] Dependencies نصب شدن
- [ ] `.env` فایل تنظیم شد
- [ ] Passwords تغییر کردن
- [ ] Backend بالا میاد و کار می‌کنه
- [ ] Frontend build می‌شه
- [ ] Health check پاس می‌شه
- [ ] Firewall تنظیم شد
- [ ] SSL نصب شد (برای production)
- [ ] Monitoring راه افتاد

---

## 🆘 عیب‌یابی مشکلات رایج

### مشکل 1: Permission Denied
```bash
# اضافه کردن user به group
sudo usermod -aG docker $USER
sudo chown -R $USER:$USER /path/to/mahoun-platform
```

### مشکل 2: Port Already in Use
```bash
# پیدا کردن process
sudo lsof -i :8000
# یا
sudo netstat -tulpn | grep 8000

# کشتن process
sudo kill -9 <PID>
```

### مشکل 3: Module Not Found
```bash
# مطمئن شو venv فعاله
source venv/bin/activate

# نصب مجدد dependencies
pip install -r requirements.txt
```

### مشکل 4: Database Connection Failed
```bash
# چک کردن .env
cat .env | grep ENABLE

# اگه دیتابیس نداری، disable کن
ENABLE_POSTGRES=false
ENABLE_NEO4J=false
ENABLE_REDIS=false
```

---

## 📞 پشتیبانی

اگه مشکلی پیش اومد:
1. چک کن logs رو: `sudo journalctl -u mahoun-backend -f`
2. تست کن health endpoint رو: `curl http://localhost:8000/health`
3. ببین همه dependencies نصب شدن: `pip list`

---

## 🎉 تمام!

حالا پروژه‌ت آماده‌ست! می‌تونی:
- Backend: `http://your-domain.com/api`
- Frontend: `http://your-domain.com`
- Metrics: `http://your-domain.com/metrics/prometheus`
- Health: `http://your-domain.com/health`

**موفق باشی! 🚀**
