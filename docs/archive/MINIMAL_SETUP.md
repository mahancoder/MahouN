# راه‌اندازی محیط توسعه سبک (برای لپتاپ Core i5 با 8GB RAM)

این راهنما برای راه‌اندازی محیط توسعه **DESKTOP_MINIMAL** طراحی شده که روی لپتاپ‌های محدود کار می‌کنه.

---

## 🎯 استراتژی: سبک، سریع، کارآمد

- ❌ **Neo4j نصب نمی‌کنیم** (خیلی سنگینه - 2-4GB RAM می‌خوره)
- ❌ **Docker نصب نمی‌کنیم** (overhead زیاد داره)
- ❌ **ML Models نصب نمی‌کنیم** (PyTorch, Transformers خیلی سنگینن)
- ✅ **فقط Core Development Tools** نصب می‌کنیم
- ✅ **API رو مستقیم اجرا می‌کنیم** (بدون Docker)
- ✅ **تست‌های سبک رو اجرا می‌کنیم** (بدون integration tests)

---

## مرحله ۱: نصب ابزارهای پایه (حتماً لازمه)

```bash
# ابزارهای بیلد و کامپایل
sudo apt install -y build-essential git curl wget

# Python و ابزارهای توسعه
sudo apt install -y python3 python3-pip python3-venv python3-dev

# کتابخانه‌های امنیتی (برای cryptography)
sudo apt install -y libssl-dev libffi-dev libsodium-dev

# کتابخانه‌های ریاضی سبک (برای NumPy)
sudo apt install -y libopenblas-dev liblapack-dev

# ویرایشگر متن (اگه نداری)
sudo apt install -y vim nano

# ابزار مانیتورینگ سیستم
sudo apt install -y htop
```

**زمان تخمینی:** 5-10 دقیقه  
**فضای دیسک:** ~500MB

---

## مرحله ۲: ساخت محیط مجازی Python

```bash
# رفتن به پوشه پروژه
cd /home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full

# ساخت محیط مجازی
python3 -m venv venv

# فعال‌سازی
source venv/bin/activate

# آپگرید pip (مهمه!)
pip install --upgrade pip setuptools wheel
```

**زمان تخمینی:** 1-2 دقیقه  
**فضای دیسک:** ~100MB

---

## مرحله ۳: تنظیم فایل .env (قبل از نصب پکیج‌ها)

```bash
# کپی فایل نمونه
cp .env.example .env

# ویرایش فایل
nano .env
```

**تنظیمات توصیه شده برای لپتاپ محدود:**

```bash
# حالت اجرا - DESKTOP_MINIMAL
MAHOUN_MODE=DESKTOP_MINIMAL

# Guard Mode - WARN (نه STRICT)
MAHOUN_GUARD_MODE=WARN

# لاگ - INFO (نه DEBUG)
LOG_LEVEL=INFO

# Neo4j - خالی بذار (نصب نمی‌کنیم)
NEO4J_URI=
NEO4J_PASSWORD=

# Redis - خالی بذار (فعلاً نیاز نیست)
REDIS_URL=

# MCP API Key - یه کلید تصادفی بساز
MCP_API_KEY=dev-local-key-$(date +%s)

# پورت API
API_PORT=8000

# تعداد Workers - فقط 1 (مهم!)
UVICORN_WORKERS=1

# Disable heavy features
ENABLE_GRAPH_REASONING=false
ENABLE_ML_MODELS=false
ENABLE_EMBEDDINGS=false
```

**ذخیره و خروج:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## مرحله ۴: نصب پکیج‌های Python (فقط Core)

```bash
# مطمئن شو محیط مجازی فعاله
source venv/bin/activate

# نصب فقط Core Dependencies (بدون extras)
pip install -e .

# نصب ابزارهای توسعه
pip install pytest pytest-cov ruff mypy

# نصب FastAPI و Uvicorn
pip install fastapi uvicorn[standard]

# نصب Pydantic و NumPy
pip install pydantic numpy python-dotenv
```

**⚠️ نصب نکن:**
- ❌ `pip install mahoun[full]` - خیلی سنگینه!
- ❌ `pip install torch transformers` - 2-3GB حجم دارن!
- ❌ `pip install neo4j chromadb` - نیاز نیست

**زمان تخمینی:** 5-10 دقیقه  
**فضای دیسک:** ~500MB (به جای 5-10GB!)

---

## مرحله ۵: بررسی نصب

```bash
# چک کردن Python
python --version

# چک کردن پکیج‌های نصب شده
pip list | grep -E "fastapi|pydantic|numpy|uvicorn"

# چک کردن import
python -c "import fastapi, pydantic, numpy; print('✅ Core packages OK')"

# چک کردن ساختار پروژه
python -c "import mahoun; print('✅ Mahoun package OK')"
```

---

## مرحله ۶: اجرای تست‌های سبک

```bash
# فقط تست‌های unit (بدون integration و slow)
pytest tests/ -v -m "not integration and not slow" --maxfail=3

# یا با Makefile
make test-fast
```

**اگه خطا خورد:** نگران نباش، بعداً درستش می‌کنیم.

---

## مرحله ۷: اجرای API

```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای API با یک worker
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000 --workers 1

# یا اگه Makefile داره:
make run
```

**باز کن در مرورگر:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**برای توقف:** `Ctrl+C`

---

## مرحله ۸: ابزارهای توسعه (اختیاری ولی مفید)

```bash
# Git config (اگه تنظیم نکردی)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Pre-commit hooks (اختیاری)
pip install pre-commit
pre-commit install

# VS Code extensions (اگه VS Code داری)
# - Python
# - Pylance
# - Ruff
# - GitLens
```

---

## 🚀 دستورات روزمره توسعه

### شروع کار روزانه
```bash
cd /home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full
source venv/bin/activate
```

### اجرای API
```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### اجرای تست‌ها
```bash
pytest tests/ -v -m "not integration and not slow"
```

### چک کردن کد
```bash
# Lint
ruff check .

# Type check
mypy mahoun/ api/

# یا با Makefile
make lint
make typecheck
```

### اصلاح خودکار مشکلات
```bash
ruff check --fix .
```

---

## 📊 مانیتورینگ منابع سیستم

```bash
# مشاهده مصرف RAM و CPU
htop

# مشاهده فضای دیسک
df -h

# مشاهده حجم پوشه venv
du -sh venv/

# مشاهده پروسس‌های Python
ps aux | grep python
```

---

## ⚠️ محدودیت‌ها و توجهات

### چیزهایی که روی لپتاپت کار نمی‌کنه:
1. ❌ **Graph Reasoning با Neo4j** - خیلی سنگینه
2. ❌ **ML Model Training** - نیاز به GPU داره
3. ❌ **Embedding Generation** - خیلی کنده
4. ❌ **Integration Tests** - نیاز به سرویس‌های خارجی دارن
5. ❌ **Docker Compose Stack** - overhead زیاد داره

### چیزهایی که خوب کار می‌کنه:
1. ✅ **API Development** - FastAPI خیلی سبکه
2. ✅ **Unit Tests** - سریع و سبک
3. ✅ **Code Linting/Formatting** - ruff خیلی سریعه
4. ✅ **Type Checking** - mypy سبکه
5. ✅ **Git Operations** - مشکلی نداره
6. ✅ **Documentation** - راحته

---

## 🔧 حل مشکلات رایج

### سیستم کنده
```bash
# بستن برنامه‌های اضافی
# چک کردن مصرف RAM
free -h

# اگه RAM کمه، swap رو افزایش بده
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### خطای Out of Memory
```bash
# کم کردن تعداد workers
UVICORN_WORKERS=1 uvicorn api.main:app

# محدود کردن تست‌ها
pytest tests/ -v --maxfail=1 -x
```

### API کند راه‌اندازی می‌شه
```bash
# نرمال! اولین بار کنده
# بار دوم سریع‌تر می‌شه
```

---

## 📝 چک لیست نهایی

- [ ] Python 3.13 نصب شده
- [ ] ابزارهای بیلد نصب شدن (`build-essential`)
- [ ] کتابخانه‌های امنیتی نصب شدن (`libssl-dev`, `libffi-dev`)
- [ ] محیط مجازی ساخته شده (`venv/`)
- [ ] فایل `.env` تنظیم شده (با `MAHOUN_MODE=DESKTOP_MINIMAL`)
- [ ] پکیج‌های Core نصب شدن (بدون `[full]`)
- [ ] تست‌های سبک پاس می‌شن
- [ ] API اجرا می‌شه و `/health` جواب میده

---

## 🎓 مرحله بعدی

بعد از راه‌اندازی موفق:

1. **یاد بگیر چطور API endpoint اضافه کنی**
2. **تست بنویس برای کدهات**
3. **با Git کار کن** (branch, commit, push)
4. **کد رو lint و format کن** قبل از commit
5. **مستندات بخون** توی `docs/`

---

## 💡 نکته طلایی

**برای DevOps و تست‌های سنگین:**
- از یه سرور ابری استفاده کن (AWS EC2, DigitalOcean, etc.)
- یا از GitHub Actions برای CI/CD
- لپتاپت فقط برای توسعه کد باشه، نه اجرای production!

---

**موفق باشی داداش! 💪**

با این تنظیمات، لپتاپت راحت کار می‌کنه و گیر نمی‌کنه.
