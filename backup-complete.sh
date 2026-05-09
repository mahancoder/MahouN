#!/bin/bash
#
# MAHOUN Platform - Complete Backup Script
# =========================================
# 
# این اسکریپت یک backup کامل از repository، Kiro settings، و تمام فایل‌های مهم می‌گیرد
#
# استفاده:
#   chmod +x backup-complete.sh
#   ./backup-complete.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Start
print_header "MAHOUN Platform - Complete Backup"
echo ""

# Create backup directory
BACKUP_DIR=~/mahoun-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"
print_success "Backup directory created: $BACKUP_DIR"
echo ""

# Change to project directory
cd ~/Desktop/Platform || {
    print_error "Project directory not found at ~/Desktop/Platform"
    exit 1
}

# ============================================================================
# 1. Git Status Check
# ============================================================================
print_header "1. Checking Git Status"

if [ -d .git ]; then
    print_info "Git repository found"
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes!"
        git status --short
        echo ""
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Backup cancelled"
            exit 1
        fi
    else
        print_success "No uncommitted changes"
    fi
    
    # Show recent commits
    print_info "Recent commits:"
    git log --oneline -5
    echo ""
else
    print_error "Not a git repository!"
    exit 1
fi

# ============================================================================
# 2. Create Git Bundle
# ============================================================================
print_header "2. Creating Git Bundle"

git bundle create "$BACKUP_DIR/mahoun-platform.bundle" --all
if git bundle verify "$BACKUP_DIR/mahoun-platform.bundle" > /dev/null 2>&1; then
    print_success "Git bundle created and verified"
    BUNDLE_SIZE=$(du -h "$BACKUP_DIR/mahoun-platform.bundle" | cut -f1)
    print_info "Bundle size: $BUNDLE_SIZE"
else
    print_error "Git bundle verification failed!"
    exit 1
fi
echo ""

# ============================================================================
# 3. Full Directory Backup
# ============================================================================
print_header "3. Creating Full Directory Backup"

rsync -az --progress \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    --exclude='.hypothesis/' \
    --exclude='node_modules/' \
    --exclude='.git/' \
    ~/Desktop/Platform/ \
    "$BACKUP_DIR/mahoun-platform-full/"

print_success "Full directory backup completed"
FULL_SIZE=$(du -sh "$BACKUP_DIR/mahoun-platform-full/" | cut -f1)
print_info "Backup size: $FULL_SIZE"
echo ""

# ============================================================================
# 4. Backup Virtual Environment Requirements
# ============================================================================
print_header "4. Backing up Python Environment"

if [ -d venv ] || [ -d .venv ]; then
    # Try venv first, then .venv
    if [ -d venv ]; then
        VENV_PATH="venv"
    else
        VENV_PATH=".venv"
    fi
    
    source "$VENV_PATH/bin/activate"
    pip freeze > "$BACKUP_DIR/requirements-frozen.txt"
    deactivate
    print_success "Python requirements exported from $VENV_PATH"
    
    # Also copy original requirements
    if [ -f requirements.txt ]; then
        cp requirements.txt "$BACKUP_DIR/requirements-original.txt"
        print_success "Original requirements.txt copied"
    fi
else
    print_warning "Virtual environment not found (checked venv/ and .venv/)"
fi
echo ""

# ============================================================================
# 5. Backup Kiro User Settings
# ============================================================================
print_header "5. Backing up Kiro User Settings"

if [ -d ~/.kiro ]; then
    tar -czf "$BACKUP_DIR/kiro-user-settings.tar.gz" -C ~ .kiro/
    print_success "Kiro user settings backed up"
    
    KIRO_SIZE=$(du -h "$BACKUP_DIR/kiro-user-settings.tar.gz" | cut -f1)
    print_info "Kiro backup size: $KIRO_SIZE"
    
    # List contents
    print_info "Kiro backup contents:"
    tar -tzf "$BACKUP_DIR/kiro-user-settings.tar.gz" | head -10
    KIRO_FILES=$(tar -tzf "$BACKUP_DIR/kiro-user-settings.tar.gz" | wc -l)
    print_info "Total files: $KIRO_FILES"
else
    print_warning "Kiro user settings not found at ~/.kiro"
fi
echo ""

# ============================================================================
# 6. Backup Kiro Workspace Settings
# ============================================================================
print_header "6. Backing up Kiro Workspace Settings"

if [ -d ~/Desktop/Platform/.kiro ]; then
    rsync -az --progress \
        ~/Desktop/Platform/.kiro/ \
        "$BACKUP_DIR/kiro-workspace-settings/"
    print_success "Kiro workspace settings backed up"
else
    print_warning "Kiro workspace settings not found"
fi
echo ""

# ============================================================================
# 7. Backup SSH Keys
# ============================================================================
print_header "7. Backing up SSH Keys"

if [ -d ~/.ssh ]; then
    mkdir -p "$BACKUP_DIR/ssh-keys"
    
    # Copy keys
    cp ~/.ssh/id_* "$BACKUP_DIR/ssh-keys/" 2>/dev/null || true
    cp ~/.ssh/config "$BACKUP_DIR/ssh-keys/" 2>/dev/null || true
    cp ~/.ssh/known_hosts "$BACKUP_DIR/ssh-keys/" 2>/dev/null || true
    
    # Set restrictive permissions
    chmod 700 "$BACKUP_DIR/ssh-keys"
    chmod 600 "$BACKUP_DIR/ssh-keys"/id_* 2>/dev/null || true
    
    print_success "SSH keys backed up"
    print_warning "SSH keys are sensitive - keep backup secure!"
else
    print_warning "SSH directory not found"
fi
echo ""

# ============================================================================
# 8. Backup Git Configuration
# ============================================================================
print_header "8. Backing up Git Configuration"

if [ -f ~/.gitconfig ]; then
    cp ~/.gitconfig "$BACKUP_DIR/gitconfig"
    print_success "Git global config backed up"
fi

if [ -f ~/Desktop/Platform/.git/config ]; then
    cp ~/Desktop/Platform/.git/config "$BACKUP_DIR/git-repo-config"
    print_success "Git repo config backed up"
fi
echo ""

# ============================================================================
# 9. Backup Environment Files
# ============================================================================
print_header "9. Backing up Environment Files"

if [ -f ~/Desktop/Platform/.env ]; then
    cp ~/Desktop/Platform/.env "$BACKUP_DIR/env-file"
    print_success ".env file backed up"
    print_warning ".env contains secrets - keep backup secure!"
fi

# Backup all .env.* files
cp ~/Desktop/Platform/.env.* "$BACKUP_DIR/" 2>/dev/null || true
echo ""

# ============================================================================
# 10. Backup Database Files
# ============================================================================
print_header "10. Backing up Database Files"

mkdir -p "$BACKUP_DIR/databases"

# Find and copy all database files
DB_COUNT=0
while IFS= read -r -d '' file; do
    cp "$file" "$BACKUP_DIR/databases/"
    ((DB_COUNT++))
done < <(find ~/Desktop/Platform -name "*.db" -o -name "*.sqlite*" -type f -print0 2>/dev/null)

if [ $DB_COUNT -gt 0 ]; then
    print_success "Backed up $DB_COUNT database files"
else
    print_info "No database files found"
fi
echo ""

# ============================================================================
# 11. Backup Data Directory
# ============================================================================
print_header "11. Backing up Data Directory"

if [ -d ~/Desktop/Platform/data ]; then
    rsync -az --progress \
        ~/Desktop/Platform/data/ \
        "$BACKUP_DIR/data-directory/"
    print_success "Data directory backed up"
else
    print_info "No data directory found"
fi
echo ""

# ============================================================================
# 12. Create Final Archive
# ============================================================================
print_header "12. Creating Final Compressed Archive"

cd ~
ARCHIVE_NAME="mahoun-complete-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$ARCHIVE_NAME" "$(basename "$BACKUP_DIR")"

ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
print_success "Final archive created: $ARCHIVE_NAME"
print_info "Archive size: $ARCHIVE_SIZE"
echo ""

# ============================================================================
# 13. Create Checksums
# ============================================================================
print_header "13. Creating Checksums"

sha256sum "$ARCHIVE_NAME" > mahoun-backup-checksums.txt
print_success "Checksums created"
cat mahoun-backup-checksums.txt
echo ""

# ============================================================================
# 14. Create Backup Info File
# ============================================================================
print_header "14. Creating Backup Info File"

cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
MAHOUN Platform Backup Information
===================================

Backup Date: $(date)
Hostname: $(hostname)
User: $(whoami)
OS: $(uname -a)

Git Information:
----------------
Branch: $(cd ~/Desktop/Platform && git branch --show-current)
Last Commit: $(cd ~/Desktop/Platform && git log -1 --oneline)
Remote: $(cd ~/Desktop/Platform && git remote get-url origin 2>/dev/null || echo "No remote")

Backup Contents:
----------------
- Git bundle: mahoun-platform.bundle
- Full directory: mahoun-platform-full/
- Python requirements: requirements-frozen.txt
- Kiro user settings: kiro-user-settings.tar.gz
- Kiro workspace settings: kiro-workspace-settings/
- SSH keys: ssh-keys/
- Git configs: gitconfig, git-repo-config
- Environment files: env-file, .env.*
- Database files: databases/
- Data directory: data-directory/

Archive:
--------
Filename: $ARCHIVE_NAME
Size: $ARCHIVE_SIZE
Checksum: $(sha256sum ~/"$ARCHIVE_NAME" | cut -d' ' -f1)

Restore Instructions:
---------------------
See BACKUP_MIGRATION_GUIDE.md for detailed restore instructions.

Quick restore:
1. Extract archive: tar -xzf $ARCHIVE_NAME
2. Restore from git bundle: git clone mahoun-platform.bundle mahoun-platform
3. Restore Kiro: tar -xzf kiro-user-settings.tar.gz -C ~/
4. Restore SSH keys: cp ssh-keys/* ~/.ssh/
5. Create venv: python3 -m venv venv && source venv/bin/activate
6. Install deps: pip install -r requirements-frozen.txt

EOF

print_success "Backup info file created"
echo ""

# ============================================================================
# Summary
# ============================================================================
print_header "Backup Complete! 🎉"

echo ""
echo "📦 Backup Location:"
echo "   Directory: $BACKUP_DIR"
echo "   Archive:   ~/$ARCHIVE_NAME"
echo "   Checksums: ~/mahoun-backup-checksums.txt"
echo ""
echo "📊 Backup Summary:"
echo "   Archive Size: $ARCHIVE_SIZE"
echo "   Kiro Size:    ${KIRO_SIZE:-N/A}"
echo "   Full Size:    $FULL_SIZE"
echo ""
echo "✅ What was backed up:"
echo "   ✓ Git repository (full history)"
echo "   ✓ All source code"
echo "   ✓ Python requirements"
echo "   ✓ Kiro settings & chat history"
echo "   ✓ SSH keys"
echo "   ✓ Git configuration"
echo "   ✓ Environment files"
echo "   ✓ Database files"
echo "   ✓ Data directory"
echo ""
echo "🔐 Security Notes:"
echo "   ⚠️  Backup contains sensitive data (SSH keys, .env files)"
echo "   ⚠️  Keep backup in a secure location"
echo "   ⚠️  Don't share backup publicly"
echo ""
echo "📝 Next Steps:"
echo "   1. Copy archive to external drive:"
echo "      cp ~/$ARCHIVE_NAME /media/YOUR_EXTERNAL_DRIVE/"
echo ""
echo "   2. Verify checksum on external drive:"
echo "      sha256sum /media/YOUR_EXTERNAL_DRIVE/$ARCHIVE_NAME"
echo "      # Compare with: cat ~/mahoun-backup-checksums.txt"
echo ""
echo "   3. Test restore on new system (see BACKUP_MIGRATION_GUIDE.md)"
echo ""
echo "   4. Keep backup until new system is fully working!"
echo ""
print_success "Backup script completed successfully!"
echo ""
