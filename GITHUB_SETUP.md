# 🚀 GitHub Setup Guide

Complete guide to push Tradenerves to GitHub safely.

## ⚠️ CRITICAL: Security Check Before Pushing

**Found hardcoded API keys in these files:**
- `tradenerves-backend/backend/data/fetch_data.py`
- `tradenerves-backend/backend/data/fetch_data_five.py`
- `tradenerves-backend/backend/data/intra_day.py`
- `tradenerves-backend/backend/data/fetch_data.py.old`

**These MUST be removed before pushing to GitHub!**

---

## 📋 Pre-Push Checklist

### 1. Verify .gitignore is Working

```bash
cd c:\Users\Victo\OneDrive\Desktop\Codebase\Tradenerves

# Check what will be committed (should NOT include .db files, node_modules, venv, etc.)
git status --ignored
```

**Should be ignored:**
- ✅ `*.db` files (stocks.db)
- ✅ `node_modules/`
- ✅ `venv/`
- ✅ `.env` files
- ✅ `build/` folders

### 2. Remove Hardcoded API Keys

**Option A: Comment out for now (Quick)**

Edit these files and comment out the API_KEY line:

`tradenerves-backend/backend/data/fetch_data.py`:
```python
# API_KEY = 'gNUdx8Rrob9OtDQSGK9EBX7K179qpNjQ'  # REMOVED - use .env file
API_KEY = os.getenv('POLYGON_API_KEY')
```

`tradenerves-backend/backend/data/fetch_data_five.py`:
```python
# API_KEY = 'gNUdx8Rrob9OtDQSGK9EBX7K179qpNjQ'  # REMOVED - use .env file
API_KEY = os.getenv('POLYGON_API_KEY')
```

`tradenerves-backend/backend/data/intra_day.py`:
```python
# Already uses environment variable - just remove fallback
API_KEY = os.getenv('POLYGON_API_KEY')  # Remove the default value
```

**Option B: Delete old files**
```bash
# Delete backup file with exposed key
rm tradenerves-backend/backend/data/fetch_data.py.old
```

### 3. Create Local .env File (NOT committed)

```bash
cd tradenerves-backend/backend
cp .env.example .env

# Edit .env and add your actual API key
# POLYGON_API_KEY=gNUdx8Rrob9OtDQSGK9EBX7K179qpNjQ
```

**Important:** `.env` is in `.gitignore` and will NOT be pushed to GitHub!

---

## 🎯 Push to GitHub - Step by Step

### Step 1: Initialize Git Repository

```bash
cd c:\Users\Victo\OneDrive\Desktop\Codebase\Tradenerves

# Initialize git
git init

# Add all files (respects .gitignore)
git add .

# Check what's being committed (verify no .db, no venv, no API keys)
git status
```

**Expected output:**
```
On branch main
Changes to be committed:
  new file:   .gitignore
  new file:   README.md
  new file:   docker-compose.yml
  new file:   DOCKER_DEPLOYMENT.md
  new file:   DOCKER_QUICKSTART.md
  new file:   tradenerves-backend/Dockerfile
  new file:   tradenerves-backend/.dockerignore
  new file:   tradenerves-backend/backend/app.py
  ...
```

**Should NOT see:**
- ❌ stocks.db
- ❌ venv/
- ❌ node_modules/
- ❌ .env files

### Step 2: Make First Commit

```bash
git commit -m "Initial commit: Tradenerves pattern analysis platform"
```

### Step 3: Create Main Branch

```bash
git branch -M main
```

### Step 4: Add GitHub Remote

```bash
git remote add origin https://github.com/Victoralk/tradenerves_v2.git
```

### Step 5: Push to GitHub

```bash
git push -u origin main
```

**If prompted for credentials:**
- Username: `Victoralk`
- Password: Use a **Personal Access Token** (not your GitHub password)

### Step 6: Verify on GitHub

Visit: https://github.com/Victoralk/tradenerves_v2

**Check:**
- ✅ README.md displays properly
- ✅ No .db files visible
- ✅ No API keys in code
- ✅ .gitignore is present

---

## 🔑 GitHub Personal Access Token (If Needed)

If GitHub asks for authentication:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (full control)
4. Generate and copy the token
5. Use this token as your password when pushing

---

## 🔄 Future Updates

After initial push, to update GitHub:

```bash
cd c:\Users\Victo\OneDrive\Desktop\Codebase\Tradenerves

# Pull latest changes (if working from multiple machines)
git pull origin main

# Make your code changes...

# Stage changes
git add .

# Commit with meaningful message
git commit -m "Add feature: XYZ"

# Push to GitHub
git push origin main
```

---

## 🆘 Common Issues

### "Remote repository not found"
```bash
# Check remote URL
git remote -v

# Should show:
# origin  https://github.com/Victoralk/tradenerves_v2.git (fetch)
# origin  https://github.com/Victoralk/tradenerves_v2.git (push)
```

### "Failed to push - rejected"
```bash
# Someone else made changes, pull first
git pull origin main --rebase
git push origin main
```

### "Too large files"
```bash
# Check what's being committed
git status

# If you see large .db files, add to .gitignore
echo "*.db" >> .gitignore
git rm --cached tradenerves-backend/backend/db/stocks.db
git commit -m "Remove database from tracking"
```

### "API key accidentally committed"
**If you push API keys by mistake:**

1. **Immediately revoke the API key** at Polygon.io
2. Remove from git history:
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch tradenerves-backend/backend/data/fetch_data.py" \
  --prune-empty --tag-name-filter cat -- --all

git push origin main --force
```
3. Generate new API key
4. Add to `.env` file (not committed)

---

## 📝 Complete Command Summary

```bash
# Navigate to project
cd c:\Users\Victo\OneDrive\Desktop\Codebase\Tradenerves

# Initialize and commit
git init
git add .
git status  # VERIFY no .db, no API keys, no venv
git commit -m "Initial commit: Tradenerves pattern analysis platform"

# Connect to GitHub
git branch -M main
git remote add origin https://github.com/Victoralk/tradenerves_v2.git

# Push
git push -u origin main
```

---

## ✅ Final Checklist Before Pushing

- [ ] `.gitignore` created and committed
- [ ] `README.md` created with project documentation
- [ ] API keys removed from code (use .env instead)
- [ ] `.env.example` created (shows what variables are needed)
- [ ] `.env` file created locally (NOT committed)
- [ ] No `*.db` files being committed
- [ ] No `venv/` or `node_modules/` being committed
- [ ] Ran `git status` and verified clean commit
- [ ] GitHub repository created: `tradenerves_v2`

**Once checked, you're ready to push! 🚀**
