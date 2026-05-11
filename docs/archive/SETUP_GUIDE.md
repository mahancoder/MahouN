# راهنمای راه‌اندازی محیط توسعه Mahoun Platform

## ۱. بررسی Python (قبلاً نصب شده!)

```bash
# بررسی ورژن Python (باید 3.13 باشه)
python3 --version

# نصب ابزارهای توسعه Python (اگه نداری)
sudo apt install -y python3-venv python3-pip python3-dev

# ⚠️ نکته: پروژه Python 3.12+ نیاز داره، Python 3.13 که داری کاملاً سازگاره!
```

## ۲. نصب Docker و Docker Compose

```bash
# نصب Docker
sudo apt install -y docker.io

# فعال‌سازی و استارت Docker
sudo systemctl enable docker
sudo systemctl start docker

# اضافه کردن کاربر به گروه docker (برای اجرا بدون sudo)
sudo usermod -aG docker $USER

# نصب Docker Compose


# بررسی نصب
docker --version
docker-compose --version

# ⚠️ بعد از اضافه شدن به گروه docker، باید logout/login کنی یا این دستور رو بزن:
newgrp docker
```

## ۳. ساخت محیط مجازی Python

```bash
# رفتن به پوشه پروژه
cd /home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full

# ساخت محیط مجازی با Python 3.13 (که داری)
python3 -m venv venv

# فعال‌سازی محیط مجازی
source venv/bin/activate

# آپگرید pip
pip install --upgrade pip setuptools wheel
```

## ۴. نصب وابستگی‌های پروژه

```bash
# مطمئن شو که محیط مجازی فعاله (باید (venv) رو اول خط ببینی)
source venv/bin/activate

# نصب از طریق Makefile (روش توصیه شده)
make install

# یا نصب مستقیم
pip install -r requirements.txt
pip install -e .
```

## ۵. تنظیم فایل Environment

```bash
# کپی کردن فایل نمونه
cp .env.example .env

# ویرایش فایل .env و تنظیم متغیرها
nano .env
# یا
vim .env
```

**متغیرهای مهم در .env:**
```bash
# API Key برای MCP
MCP_API_KEY=your-secret-key-here

# تنظیمات Neo4j (اختیاری برای حالت DESKTOP_MINIMAL)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your-neo4j-password

# حالت اجرا (DESKTOP_MINIMAL برای لپتاپ)
MAHOUN_GUARD_MODE=WARN

# سطح لاگ
LOG_LEVEL=INFO
```

## ۶. نصب ابزارهای توسعه (اختیاری اما توصیه می‌شه)

```bash
# نصب pre-commit برای git hooks
pip install pre-commit

# نصب pre-commit hooks
pre-commit install

# نصب ابزارهای لینت و تایپ چک
pip install ruff mypy pytest pytest-cov
```

## ۷. بررسی نصب

```bash
# چک کردن لینت
make lint

# چک کردن تایپ
make typecheck

# اجرای تست‌های سریع (بدون نیاز به Docker)
make test-fast

# یا
pytest tests/ -v -m "not slow and not integration"
```

## ۸. راه‌اندازی با Docker (برای حالت ENTERPRISE_FULL)

```bash
# بیلد و استارت تمام سرویس‌ها
make docker-up

# یا
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# مشاهده لاگ‌ها
docker-compose logs -f

# تست smoke
make docker-test

# خاموش کردن
make docker-down
```

## ۹. اجرای API به صورت مستقیم (بدون Docker)

```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# یا با Makefile (اگر تعریف شده باشه)
make run
```

## ۱۰. دستورات مفید Makefile

```bash
make install          # نصب وابستگی‌ها
make lint             # چک لینت
make lint-fix         # اصلاح خودکار مشکلات لینت
make typecheck        # چک تایپ با mypy
make test-fast        # تست‌های سریع
make ci-first-step    # اجرای تمام گیت‌های CI
make docker-up        # استارت Docker
make docker-down      # خاموش کردن Docker
make docker-test      # تست Docker
```

## ۱۱. حل مشکلات رایج

### مشکل دسترسی Docker
```bash
# اگر خطای permission denied گرفتی:
sudo usermod -aG docker $USER
newgrp docker
# یا logout/login کن
```

### مشکل پورت اشغال
```bash
# پیدا کردن پروسسی که پورت 8000 رو گرفته
sudo lsof -i :8000

# کشتن پروسس
sudo kill -9 <PID>
```

### مشکل وابستگی‌ها
```bash
# پاک کردن محیط مجازی و ساخت دوباره
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
make install
```

### مشکل Neo4j
```bash
# اگر Neo4j نداری و نمی‌خوای نصب کنی، در .env بذار:
NEO4J_URI=
NEO4J_PASSWORD=

# سیستم در حالت DESKTOP_MINIMAL بدون Neo4j کار می‌کنه
```

## ۱۲. چک لیست نهایی

- [ ] Python 3.12 نصب شده
- [ ] Docker و Docker Compose نصب شده
- [ ] محیط مجازی ساخته و فعال شده
- [ ] وابستگی‌ها نصب شدن (`make install`)
- [ ] فایل `.env` تنظیم شده
- [ ] تست‌ها پاس می‌شن (`make test-fast`)
- [ ] لینت و تایپ چک مشکلی نداره (`make lint && make typecheck`)

## ۱۳. مستندات بیشتر

- **ساختار پروژه**: `.kiro/steering/structure.md`
- **تکنولوژی‌ها**: `.kiro/steering/tech.md`
- **محصول**: `.kiro/steering/product.md`
- **قوانین معماری**: `.kiro/steering/kirorules.md`

---

## نکات مهم برای حالت DESKTOP_MINIMAL

اگر لپتاپ با RAM محدود داری (مثلاً 8GB):

1. **Neo4j رو نصب نکن** - سیستم بدون اون کار می‌کنه
2. **از Docker استفاده نکن** - API رو مستقیم اجرا کن
3. **تست‌های سنگین رو اجرا نکن**:
   ```bash
   # فقط تست‌های سبک
   pytest tests/ -v -m "not slow and not integration"
   ```
4. **در .env تنظیم کن**:
   ```bash
   MAHOUN_GUARD_MODE=WARN
   LOG_LEVEL=INFO
   ```

---

**موفق باشی داداش! 🚀**

اگر هر جا گیر کردی بگو تا کمکت کنم.
