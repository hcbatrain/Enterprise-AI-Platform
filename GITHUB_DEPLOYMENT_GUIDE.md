# Enterprise AI Platform - Complete GitHub Deployment Guide

Deploy your Enterprise AI Platform to the cloud using GitHub and Render.com (FREE).

---

## Prerequisites

- GitHub account (free): https://github.com/signup
- Render.com account (free): https://render.com
- Git installed on your computer: https://git-scm.com/downloads

---

## Step 1: Create GitHub Repository

### Option A: Using GitHub Website (Recommended)

1. Go to https://github.com/new
2. Enter repository name: `enterprise-ai-platform`
3. Select "Public" or "Private"
4. Click **"Create repository"**

### Option B: Using Command Line

```bash
# Create a new repository via GitHub CLI
curl -u YOUR_USERNAME https://api.github.com/user/repos -d '{"name":"enterprise-ai-platform"}'
```

---

## Step 2: Push Code to GitHub

### 2.1 Open Terminal/Command Prompt

Navigate to the project folder:

```bash
cd /mnt/okcomputer/output/enterprise-ai-platform
```

### 2.2 Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit - Enterprise AI Platform"
```

### 2.3 Connect to GitHub

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/enterprise-ai-platform.git

# Push to GitHub
git push -u origin main
```

### 2.4 Verify Upload

Go to `https://github.com/YOUR_USERNAME/enterprise-ai-platform` and confirm all files are uploaded.

---

## Step 3: Sign Up for Render.com

1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (easiest option)
4. Authorize Render to access your GitHub repositories

---

## Step 4: Deploy to Render.com

### 4.1 Create New Web Service

1. In Render dashboard, click **"New +"** button
2. Select **"Blueprint"**
3. Find and click your `enterprise-ai-platform` repository

### 4.2 Configure Deployment

Render will automatically detect the `render-simple.yaml` file and configure:
- **Service Name**: `enterprise-ai-platform`
- **Environment**: Docker
- **Dockerfile Path**: `Dockerfile.simple`
- **Health Check**: `/api/health`

### 4.3 Environment Variables

Add these environment variables in Render dashboard:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (Generate random string) |
| `ENVIRONMENT` | `production` |

To generate SECRET_KEY:
```bash
openssl rand -hex 32
```

### 4.4 Create Service

Click **"Apply"** or **"Create Web Service"**

---

## Step 5: Wait for Deployment

Render will:
1. Pull your code from GitHub
2. Build the Docker image (~5-10 minutes)
3. Deploy the application
4. Run health checks

**Status indicators:**
- 🟡 Yellow = Building
- 🟢 Green = Live
- 🔴 Red = Error (check logs)

---

## Step 6: Access Your Application

### 6.1 Get Your Live URL

Once deployment is complete, you'll see a URL like:
```
https://enterprise-ai-platform-xxx.onrender.com
```

### 6.2 Login Credentials

| Field | Value |
|-------|-------|
| **Email** | `admin@enterprise.ai` |
| **Password** | `Admin123!` |

### 6.3 Test Persistent Memory

1. Login with credentials
2. Say: "I'm John from Data Conversion working on CA WC migration"
3. Ask a question about policy mapping
4. Close browser
5. Reopen URL
6. Ask: "What was I working on?"
7. **AI should remember!**

---

## Step 7: Custom Domain (Optional)

### 7.1 Add Custom Domain

1. In Render dashboard, go to your service
2. Click **"Settings"**
3. Scroll to **"Custom Domain"**
4. Enter your domain (e.g., `ai.yourcompany.com`)
5. Follow DNS configuration instructions

### 7.2 DNS Configuration

Add CNAME record:
- **Type**: CNAME
- **Name**: `ai` (or subdomain)
- **Value**: `enterprise-ai-platform-xxx.onrender.com`

---

## Complete Deployment Script

Save this as `deploy.sh` and run it:

```bash
#!/bin/bash

# Enterprise AI Platform - GitHub + Render Deployment Script

set -e

echo "=============================================="
echo "Enterprise AI Platform Deployment"
echo "=============================================="
echo ""

# Check if GitHub username is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Example: ./deploy.sh johnsmith"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="enterprise-ai-platform"

echo "Step 1: Checking prerequisites..."

# Check git
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed"
    echo "Install from: https://git-scm.com/downloads"
    exit 1
fi

echo "✓ Git is installed"

# Check if in correct directory
if [ ! -f "Dockerfile.simple" ]; then
    echo "ERROR: Not in project directory"
    echo "Please run from: /mnt/okcomputer/output/enterprise-ai-platform"
    exit 1
fi

echo "✓ In correct directory"

echo ""
echo "Step 2: Creating GitHub repository..."

# Create repo via GitHub API
curl -s -u $GITHUB_USERNAME https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO_NAME\",\"private\":false}" > /dev/null

echo "✓ GitHub repository created"

echo ""
echo "Step 3: Pushing code to GitHub..."

# Initialize and push
git init
git add .
git commit -m "Initial commit - Enterprise AI Platform"
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
git push -u origin main

echo "✓ Code pushed to GitHub"

echo ""
echo "=============================================="
echo "DEPLOYMENT COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Go to https://render.com"
echo "2. Sign up with GitHub"
echo "3. Click 'New +' → 'Blueprint'"
echo "4. Select '$REPO_NAME' repository"
echo "5. Click 'Apply'"
echo ""
echo "Your app will be live at:"
echo "https://$REPO_NAME-xxx.onrender.com"
echo ""
echo "Login: admin@enterprise.ai / Admin123!"
echo ""
echo "=============================================="
```

**Usage:**
```bash
chmod +x deploy.sh
./deploy.sh YOUR_GITHUB_USERNAME
```

---

## Troubleshooting

### Issue: Git push fails

**Solution:**
```bash
# Check remote URL
git remote -v

# Fix if needed
git remote set-url origin https://github.com/YOUR_USERNAME/enterprise-ai-platform.git

# Try again
git push -u origin main
```

### Issue: Render build fails

**Solution:**
1. Check Render logs in dashboard
2. Ensure `Dockerfile.simple` exists in root
3. Verify `render-simple.yaml` is present

### Issue: Application won't start

**Solution:**
1. Check environment variables in Render dashboard
2. Verify `SECRET_KEY` is set
3. Check health endpoint: `/api/health`

### Issue: Slow performance

**Solution:**
- Render free tier has limitations
- Upgrade to paid plan for better performance
- Or deploy to AWS/GCP for production

---

## Alternative Deployment Options

### Option A: Deploy to Railway.app

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway init
railway up
```

### Option B: Deploy to Heroku

```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create enterprise-ai-platform

# Deploy
git push heroku main
```

### Option C: Deploy to AWS (Production)

See `CLOUD-DEPLOYMENT.md` for AWS ECS/Fargate setup.

---

## Post-Deployment Checklist

- [ ] Application loads at live URL
- [ ] Login works with default credentials
- [ ] Chat interface is functional
- [ ] Persistent memory works (test by closing/reopening)
- [ ] AI responds with WC domain knowledge
- [ ] Memory panel shows stored information

---

## Support

If you encounter issues:

1. Check Render logs: Dashboard → Service → Logs
2. Review GitHub Actions (if enabled)
3. Verify all files pushed correctly
4. Check environment variables

---

**Your Enterprise AI Platform will be live in ~10 minutes after starting deployment!**
