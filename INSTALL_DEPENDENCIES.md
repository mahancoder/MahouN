# نصب وابستگی‌های خارجی Mahoun Platform

این فایل شامل دستورات نصب تک‌تک وابستگی‌های خارجی (سیستمی) هست که قبل از نصب پکیج‌های Python باید نصب بشن.

---

## ۱. ابزارهای پایه توسعه

```bash
# کامپایلر C/C++ و ابزارهای بیلد (برای کامپایل پکیج‌های Python)
sudo apt install -y build-essential

# Git (احتمالاً داری ولی مطمئن بشیم)
sudo apt install -y git

# Curl و Wget (برای دانلود فایل‌ها)
sudo apt install -y curl wget
```

---

## ۲. Python و ابزارهای توسعه Python

```bash
# Python 3 و ابزارهای توسعه
sudo apt install -y python3 python3-pip python3-venv python3-dev

# هدرهای Python برای کامپایل پکیج‌های native
sudo apt install -y python3-setuptools python3-wheel
```

---

## ۳. کتابخانه‌های سیستمی برای NumPy و پکیج‌های علمی

```bash
# کتابخانه‌های ریاضی و BLAS/LAPACK (برای NumPy، SciPy)
sudo apt install -y libopenblas-dev liblapack-dev

# Fortran compiler (برای برخی پکیج‌های علمی)
sudo apt install -y gfortran
```

---

## ۴. کتابخانه‌های سیستمی برای Cryptography و امنیت

```bash
# OpenSSL و کتابخانه‌های رمزنگاری
sudo apt install -y libssl-dev libffi-dev

# برای PyNaCl و cryptography
sudo apt install -y libsodium-dev
```

---

## ۵. Docker و Docker Compose (اختیاری - برای حالت ENTERPRISE_FULL)

```bash
# نصب Docker
sudo apt install -y docker.io

# فعال‌سازی Docker
sudo systemctl enable docker
sudo systemctl start docker

# اضافه کردن کاربر به گروه docker
sudo usermod -aG docker $USER

# نصب Docker Compose
sudo apt install -y docker-compose

# ⚠️ بعد از این دستور باید logout/login کنی یا:
newgrp docker

# بررسی نصب
docker --version
docker-compose --version
```

---

## ۶. PostgreSQL Client Libraries (اختیاری - اگه از PostgreSQL استفاده می‌کنی)

```bash
# کتابخانه‌های PostgreSQL
sudo apt install -y libpq-dev postgresql-client
```

---

## ۷. Redis (اختیاری - برای caching و distributed locks)

```bash
# نصب Redis Server
sudo apt install -y redis-server

# فعال‌سازی Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# بررسی وضعیت
sudo systemctl status redis-server

# تست اتصال
redis-cli ping
# باید جواب PONG بده
```

---

## ۸. Neo4j (اختیاری - برای حالت ENTERPRISE_FULL با Graph Database)

⚠️ **توجه:** Neo4j سنگینه و برای لپتاپ با RAM کم توصیه نمی‌شه!

### روش ۱: نصب از طریق Docker (راحت‌تر)

```bash
# دانلود و اجرای Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest

# بررسی وضعیت
docker ps | grep neo4j

# دسترسی به Web UI
# باز کن: http://localhost:7474
```

### روش ۲: نصب مستقیم (پیچیده‌تر)

```bash
# اضافه کردن مخزن Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# آپدیت و نصب
sudo apt update
sudo apt install -y neo4j

# فعال‌سازی
sudo systemctl enable neo4j
sudo systemctl start neo4j

# بررسی وضعیت
sudo systemctl status neo4j
```

---

## ۹. ابزارهای اضافی (اختیاری ولی مفید)

```bash
# htop برای مانیتورینگ سیستم
sudo apt install -y htop

# jq برای کار با JSON در terminal
sudo apt install -y jq

# tree برای نمایش ساختار پوشه‌ها
sudo apt install -y tree

# ncdu برای بررسی فضای دیسک
sudo apt install -y ncdu
```

---

## ۱۰. بررسی نصب همه چیز

```bash
# بررسی Python
python3 --version

# بررسی pip
pip3 --version

# بررسی Git
git --version

# بررسی Docker (اگه نصب کردی)
docker --version
docker-compose --version

# بررسی Redis (اگه نصب کردی)
redis-cli ping

# بررسی کامپایلر
gcc --version
```

---

## ۱۱. نصب پکیج‌های Python (بعد از نصب وابستگی‌های بالا)

```bash
# رفتن به پوشه پروژه
cd /home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full

# ساخت محیط مجازی
python3 -m venv venv

# فعال‌سازی محیط مجازی
source venv/bin/activate

# آپگرید pip
pip install --upgrade pip setuptools wheel

# نصب وابستگی‌های پروژه
make install

# یا نصب دستی:
pip install -r requirements.txt
pip install -e .
```

---

## چک لیست نهایی

### حداقلی (برای DESKTOP_MINIMAL):
- [ ] `build-essential` نصب شده
- [ ] `python3`, `python3-pip`, `python3-venv`, `python3-dev` نصب شده
- [ ] `libssl-dev`, `libffi-dev` نصب شده
- [ ] `libopenblas-dev`, `liblapack-dev` نصب شده
- [ ] محیط مجازی Python ساخته شده
- [ ] پکیج‌های Python نصب شدن

### کامل (برای ENTERPRISE_FULL):
- [ ] همه موارد بالا ✓
- [ ] Docker و Docker Compose نصب شده
- [ ] Redis نصب و اجرا شده
- [ ] Neo4j نصب و اجرا شده (اختیاری)
- [ ] PostgreSQL نصب شده (اختیاری)

---

## حل مشکلات رایج

### خطای "command not found" بعد از نصب
```bash
# ریلود کردن shell
source ~/.bashrc
# یا
exec bash
```

### خطای permission denied
```bash
# برای Docker
sudo usermod -aG docker $USER
newgrp docker

# برای فایل‌ها
sudo chown -R $USER:$USER /home/haji/Documents/mahoun-backup-20260507-042302/mahoun-platform-full
```

### خطای "No module named 'pip'"
```bash
# نصب دوباره pip
sudo apt install --reinstall python3-pip
```

### خطای کامپایل پکیج‌های Python
```bash
# مطمئن شو این‌ها نصب شدن:
sudo apt install -y build-essential python3-dev libssl-dev libffi-dev
```

---

**موفق باشی داداش! 🚀**

اگه توی هر مرحله خطا خورد، خطا رو بفرست تا کمکت کنم.
