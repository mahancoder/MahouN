# 🚀 راهنمای سریع Backup

## دستور سریع (یک خط!)

```bash
cd ~/Desktop/Platform && ./backup-complete.sh
```

این اسکریپت **همه چیز** رو backup می‌گیره:
- ✅ Repository کامل با تمام history
- ✅ Kiro settings و chat history
- ✅ SSH keys
- ✅ Database files
- ✅ Environment files
- ✅ Git configuration
- ✅ Python requirements

---

## مراحل کامل

### 1️⃣ اجرای Backup

```bash
cd ~/Desktop/Platform
./backup-complete.sh
```

**زمان تقریبی**: 2-5 دقیقه (بسته به حجم)

### 2️⃣ کپی به External Drive

```bash
# پیدا کردن external drive
lsblk

# Mount کردن (اگر mount نیست)
# مثال: sudo mount /dev/sdb1 /media/backup

# کپی فایل backup
cp ~/mahoun-complete-backup-*.tar.gz /media/YOUR_DRIVE/
cp ~/mahoun-backup-checksums.txt /media/YOUR_DRIVE/
```

### 3️⃣ Verify کردن

```bash
# بررسی checksum
cd /media/YOUR_DRIVE/
sha256sum mahoun-complete-backup-*.tar.gz

# مقایسه با checksum اصلی
cat ~/mahoun-backup-checksums.txt

# باید یکسان باشند! ✅
```

---

## Restore در سیستم جدید

### 1️⃣ کپی Backup

```bash
# کپی از external drive
cp /media/YOUR_DRIVE/mahoun-complete-backup-*.tar.gz ~/
cd ~
```

### 2️⃣ Extract کردن

```bash
tar -xzf mahoun-complete-backup-*.tar.gz
cd mahoun-backup-*/
```

### 3️⃣ Restore Repository

```bash
# از git bundle
git clone mahoun-platform.bundle ~/Desktop/mahoun-platform
cd ~/Desktop/mahoun-platform
```

### 4️⃣ Restore Kiro

```bash
# Extract Kiro settings
cd ~/mahoun-backup-*/
tar -xzf kiro-user-settings.tar.gz -C ~/

# بررسی
ls -la ~/.kiro/
```

### 5️⃣ Restore SSH Keys

```bash
# کپی SSH keys
mkdir -p ~/.ssh
cp ssh-keys/* ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*

# تست
ssh -T git@github.com
```

### 6️⃣ Setup Python Environment

```bash
cd ~/Desktop/mahoun-platform

# ایجاد venv
python3 -m venv venv
source venv/bin/activate

# نصب dependencies
pip install -r ~/mahoun-backup-*/requirements-frozen.txt
```

### 7️⃣ Restore Environment Files

```bash
cp ~/mahoun-backup-*/env-file ~/Desktop/mahoun-platform/.env
```

### 8️⃣ Test کردن

```bash
cd ~/Desktop/mahoun-platform
source venv/bin/activate

# اجرای تست
pytest tests/ -v -x

# اگر تست‌ها pass شدند، همه چیز OK است! ✅
```

---

## ❓ سوالات متداول

### چقدر فضا نیاز دارم؟

معمولاً 500MB - 2GB (بسته به حجم repository و Kiro history)

### Backup چقدر طول می‌کشه؟

2-5 دقیقه (بسته به حجم و سرعت دیسک)

### آیا می‌تونم backup رو فشرده‌تر کنم؟

بله! می‌تونی از `xz` به جای `gzip` استفاده کنی:

```bash
tar -cJf backup.tar.xz mahoun-backup-*/
```

### اگر Kiro chat history پیدا نشد؟

```bash
# جستجو در تمام سیستم
find ~ -name "*kiro*" -type d 2>/dev/null
find ~ -name "*conversation*" -type d 2>/dev/null
```

### اگر Git bundle کار نکرد؟

از full directory backup استفاده کن:

```bash
rsync -avz mahoun-platform-full/ ~/Desktop/mahoun-platform/
```

---

## 🆘 کمک

اگر مشکلی پیش اومد:

1. **Log errors رو save کن**
2. **Backup files رو نگه دار**
3. **از من کمک بگیر!**

---

## ✅ Checklist قبل از پاک کردن سیستم قدیم

- [ ] Backup اجرا شد بدون error
- [ ] Archive روی external drive کپی شد
- [ ] Checksum verify شد
- [ ] Backup در سیستم جدید test شد
- [ ] تست‌ها در سیستم جدید pass شدند
- [ ] Kiro chat history در سیستم جدید هست
- [ ] SSH keys کار می‌کنند
- [ ] Git push/pull کار می‌کند

**فقط بعد از این checklist سیستم قدیم رو پاک کن!** ⚠️

---

**موفق باشی! 🎉**
