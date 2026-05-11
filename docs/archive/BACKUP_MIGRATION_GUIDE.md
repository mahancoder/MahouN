# راهنمای کامل Backup و Migration سیستم عامل

**تاریخ**: 2026-05-07  
**هدف**: انتقال کامل محیط توسعه به سیستم عامل جدید  
**وضعیت**: آماده برای اجرا

---

## 📋 چک‌لیست Backup

### ✅ چیزهایی که باید backup بگیری:

1. **Repository (MAHOUN Platform)** ✅
2. **Git History کامل** ✅
3. **Virtual Environment** ✅
4. **Kiro Settings & Chats** ✅
5. **Database Files** ✅
6. **Configuration Files** ✅
7. **SSH Keys & Credentials** ✅
8. **IDE Settings** ✅

---

## 🚀 مرحله 1: Backup Repository

### گام 1.1: بررسی وضعیت Git

```bash
cd ~/Desktop/Platform
git status
git log --oneline -10
git remote -v
```

### گام 1.2: Push همه چیز به Remote

```bash
# Push all branches
git push origin --all

# Push all tags
git push origin --tags

# Verify
git branch -a
```

### گام 1.3: Clone تمیز برای تست

```bash
cd ~/Desktop
git clone --mirror https://github.com/YOUR_USERNAME/mahoun-platform.git mahoun-backup.git
```

---

## 💾 مرحله 2: Backup کامل Local

### گام 2.1: ایجاد Backup Directory

```bash
# Create backup directory with timestamp
BACKUP_DIR=~/mahoun-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
echo "Backup directory: $BACKUP_DIR"
```

### گام 2.2: Backup Repository با Git Bundle

```bash
cd ~/Desktop/Platform

# Create git bundle (includes ALL history)
git bundle create $BACKUP_DIR/mahoun-platform.bundle --all

# Verify bundle
git bundle verify $BACKUP_DIR/mahoun-platform.bundle
```

### گام 2.3: Backup کامل Directory

```bash
# Full backup with rsync (preserves permissions, symlinks, etc.)
rsync -avz --progress \
  ~/Desktop/Platform/ \
  $BACKUP_DIR/mahoun-platform-full/

# Verify
ls -lah $BACKUP_DIR/mahoun-platform-full/
```

### گام 2.4: Backup Virtual Environment

```bash
# Export installed packages
cd ~/Desktop/Platform
source venv/bin/activate
pip freeze > $BACKUP_DIR/requirements-frozen.txt

# Also backup requirements.txt
cp requirements.txt $BACKUP_DIR/requirements-original.txt

# Deactivate
deactivate
```

---

## 🎯 مرحله 3: Backup Kiro Settings & Chats

### گام 3.1: پیدا کردن Kiro Data Directory

```bash
# Kiro usually stores data in:
# ~/.kiro/  (user-level settings)
# .kiro/    (workspace-level settings)

# Check if exists
ls -la ~/.kiro/
ls -la ~/Desktop/Platform/.kiro/
```

### گام 3.2: Backup Kiro User Settings

```bash
# Backup user-level Kiro settings
if [ -d ~/.kiro ]; then
  rsync -avz --progress \
    ~/.kiro/ \
    $BACKUP_DIR/kiro-user-settings/
  echo "✅ Kiro user settings backed up"
else
  echo "⚠️  ~/.kiro not found"
fi
```

### گام 3.3: Backup Kiro Workspace Settings

```bash
# Backup workspace-level Kiro settings
if [ -d ~/Desktop/Platform/.kiro ]; then
  rsync -avz --progress \
    ~/Desktop/Platform/.kiro/ \
    $BACKUP_DIR/kiro-workspace-settings/
  echo "✅ Kiro workspace settings backed up"
else
  echo "⚠️  .kiro not found in workspace"
fi
```

### گام 3.4: Backup Kiro Chat History

```bash
# Kiro chat history is usually in:
# ~/.kiro/conversations/
# ~/.kiro/history/

# Backup all Kiro data
if [ -d ~/.kiro ]; then
  # Create detailed backup
  tar -czf $BACKUP_DIR/kiro-complete-backup.tar.gz \
    -C ~ .kiro/
  
  echo "✅ Complete Kiro backup created: kiro-complete-backup.tar.gz"
  
  # List contents
  tar -tzf $BACKUP_DIR/kiro-complete-backup.tar.gz | head -20
fi
```

---

## 🔐 مرحله 4: Backup Credentials & Keys

### گام 4.1: Backup SSH Keys

```bash
# Backup SSH keys
if [ -d ~/.ssh ]; then
  mkdir -p $BACKUP_DIR/ssh-keys
  
  # Copy keys (CAREFUL - these are sensitive!)
  cp ~/.ssh/id_* $BACKUP_DIR/ssh-keys/ 2>/dev/null || true
  cp ~/.ssh/config $BACKUP_DIR/ssh-keys/ 2>/dev/null || true
  cp ~/.ssh/known_hosts $BACKUP_DIR/ssh-keys/ 2>/dev/null || true
  
  # Set restrictive permissions
  chmod 700 $BACKUP_DIR/ssh-keys
  chmod 600 $BACKUP_DIR/ssh-keys/id_* 2>/dev/null || true
  
  echo "✅ SSH keys backed up"
fi
```

### گام 4.2: Backup Git Config

```bash
# Backup git configuration
cp ~/.gitconfig $BACKUP_DIR/gitconfig 2>/dev/null || true
cp ~/Desktop/Platform/.git/config $BACKUP_DIR/git-repo-config 2>/dev/null || true

echo "✅ Git config backed up"
```

### گام 4.3: Backup Environment Variables

```bash
# Backup .env files
cp ~/Desktop/Platform/.env $BACKUP_DIR/env-file 2>/dev/null || true
cp ~/Desktop/Platform/.env.* $BACKUP_DIR/ 2>/dev/null || true

echo "✅ Environment files backed up"
```

---

## 🗄️ مرحله 5: Backup Database Files

### گام 5.1: Backup SQLite Databases

```bash
# Find and backup all .db files
find ~/Desktop/Platform -name "*.db" -type f \
  -exec cp {} $BACKUP_DIR/databases/ \;

# Find and backup all .sqlite files
find ~/Desktop/Platform -name "*.sqlite*" -type f \
  -exec cp {} $BACKUP_DIR/databases/ \;

echo "✅ Database files backed up"
```

### گام 5.2: Backup Data Directory

```bash
# Backup data directory if exists
if [ -d ~/Desktop/Platform/data ]; then
  rsync -avz --progress \
    ~/Desktop/Platform/data/ \
    $BACKUP_DIR/data-directory/
  echo "✅ Data directory backed up"
fi
```

---

## ⚙️ مرحله 6: Backup IDE Settings

### گام 6.1: Backup VS Code Settings

```bash
# Backup VS Code settings
if [ -d ~/.config/Code ]; then
  mkdir -p $BACKUP_DIR/vscode-settings
  cp -r ~/.config/Code/User $BACKUP_DIR/vscode-settings/
  echo "✅ VS Code settings backed up"
fi
```

### گام 6.2: Backup Cursor Settings

```bash
# Backup Cursor settings (if using Cursor)
if [ -d ~/.cursor ]; then
  rsync -avz --progress \
    ~/.cursor/ \
    $BACKUP_DIR/cursor-settings/
  echo "✅ Cursor settings backed up"
fi
```

---

## 📦 مرحله 7: ایجاد Archive نهایی

### گام 7.1: فشرده‌سازی Backup

```bash
# Create compressed archive
cd ~
tar -czf mahoun-complete-backup-$(date +%Y%m%d).tar.gz \
  $(basename $BACKUP_DIR)

# Get file size
ls -lh mahoun-complete-backup-*.tar.gz

echo "✅ Complete backup archive created"
```

### گام 7.2: ایجاد Checksum

```bash
# Create checksums for verification
cd ~
sha256sum mahoun-complete-backup-*.tar.gz > mahoun-backup-checksums.txt

cat mahoun-backup-checksums.txt
```

### گام 7.3: کپی به External Drive

```bash
# Copy to external drive (replace /media/backup with your path)
EXTERNAL_DRIVE="/media/backup"

if [ -d "$EXTERNAL_DRIVE" ]; then
  cp mahoun-complete-backup-*.tar.gz $EXTERNAL_DRIVE/
  cp mahoun-backup-checksums.txt $EXTERNAL_DRIVE/
  echo "✅ Backup copied to external drive"
else
  echo "⚠️  External drive not found at $EXTERNAL_DRIVE"
  echo "Please copy manually:"
  echo "  - mahoun-complete-backup-*.tar.gz"
  echo "  - mahoun-backup-checksums.txt"
fi
```

---

## 🔄 مرحله 8: Restore در سیستم جدید

### گام 8.1: نصب Dependencies

```bash
# Install git
sudo apt update
sudo apt install git python3 python3-pip python3-venv

# Install Kiro (if needed)
# Follow Kiro installation instructions
```

### گام 8.2: Restore از Git Bundle

```bash
# Copy backup to new system first
# Then restore from bundle:

cd ~/Desktop
git clone mahoun-platform.bundle mahoun-platform
cd mahoun-platform

# Verify
git log --oneline -10
git remote -v
```

### گام 8.3: Restore Virtual Environment

```bash
cd ~/Desktop/mahoun-platform

# Create new venv
python3 -m venv venv
source venv/bin/activate

# Install exact versions
pip install -r requirements-frozen.txt

# Verify
pip list
```

### گام 8.4: Restore Kiro Settings

```bash
# Extract Kiro backup
tar -xzf kiro-complete-backup.tar.gz -C ~/

# Verify
ls -la ~/.kiro/
```

### گام 8.5: Restore SSH Keys

```bash
# Copy SSH keys
mkdir -p ~/.ssh
cp ssh-keys/* ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*

# Test
ssh -T git@github.com
```

### گام 8.6: Restore Git Config

```bash
# Restore git config
cp gitconfig ~/.gitconfig

# Configure git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### گام 8.7: Restore Environment Files

```bash
cd ~/Desktop/mahoun-platform
cp env-file .env

# Edit if needed
nano .env
```

---

## ✅ مرحله 9: Verification

### گام 9.1: بررسی Repository

```bash
cd ~/Desktop/mahoun-platform

# Check git status
git status
git log --oneline -10

# Check branches
git branch -a

# Check remotes
git remote -v
```

### گام 9.2: بررسی Virtual Environment

```bash
source venv/bin/activate
python --version
pip list | head -20
```

### گام 9.3: اجرای تست‌ها

```bash
# Run tests to verify everything works
pytest tests/ -v --tb=short -x

# If tests pass, you're good! ✅
```

### گام 9.4: بررسی Kiro

```bash
# Check Kiro settings
ls -la ~/.kiro/

# Start Kiro and verify chat history is there
```

---

## 📝 Checklist نهایی

قبل از پاک کردن سیستم قدیم، مطمئن شو:

- [ ] ✅ Git bundle ساخته شد و verify شد
- [ ] ✅ Complete backup archive ساخته شد
- [ ] ✅ Checksum فایل‌ها ساخته شد
- [ ] ✅ Backup روی external drive کپی شد
- [ ] ✅ Kiro settings backup شد
- [ ] ✅ SSH keys backup شد
- [ ] ✅ Database files backup شد
- [ ] ✅ .env files backup شد
- [ ] ✅ همه چیز push شد به remote repository
- [ ] ✅ Backup در سیستم جدید test شد

---

## 🆘 در صورت مشکل

### اگر Git Bundle کار نکرد:

```bash
# Use full directory backup
rsync -avz mahoun-platform-full/ ~/Desktop/mahoun-platform/
```

### اگر Kiro Chat History پیدا نشد:

```bash
# Search for Kiro data
find ~ -name "*kiro*" -type d 2>/dev/null
find ~ -name "*conversation*" -type d 2>/dev/null
```

### اگر Virtual Environment مشکل داشت:

```bash
# Recreate from scratch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 پشتیبانی

اگر مشکلی پیش اومد:
1. Backup files رو نگه دار
2. Log errors رو save کن
3. از من کمک بگیر!

---

**موفق باشی! 🚀**
