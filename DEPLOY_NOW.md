# Deploy Enterprise AI Platform - Step by Step

## Fastest Option: Render.com (FREE, Live URL in 10 minutes)

### Prerequisites
- GitHub account (free)
- Render.com account (free)

### Step 1: Push Code to GitHub (2 minutes)

Open your terminal and run:

```bash
# Go to the project directory
cd /mnt/okcomputer/output/enterprise-ai-platform

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment"

# Create GitHub repo and push (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/enterprise-ai-platform.git
git push -u origin main
```

### Step 2: Deploy to Render (5 minutes)

1. Go to https://dashboard.render.com
2. Sign up/login with GitHub
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will detect `render-simple.yaml` and deploy automatically
6. Wait 3-5 minutes for build

### Step 3: Get Your Live URL

After deployment, you'll get a URL like:
```
https://enterprise-ai-platform-xxx.onrender.com
```

**Login:** admin@enterprise.ai / Admin123!

---

## Option 2: Run on Your Computer (15 minutes)

### For Mac/Linux:

```bash
# 1. Install Docker Desktop from https://www.docker.com/products/docker-desktop

# 2. Open terminal and run:
cd /mnt/okcomputer/output/enterprise-ai-platform
./deploy.sh

# 3. Wait 10-15 minutes for setup

# 4. Open browser to:
open http://localhost:3000
```

### For Windows:

```powershell
# 1. Install Docker Desktop from https://www.docker.com/products/docker-desktop

# 2. Open PowerShell and run:
cd C:\path\to\enterprise-ai-platform
.\deploy.sh

# 3. Wait 10-15 minutes

# 4. Open browser to:
start http://localhost:3000
```

---

## Option 3: I Deploy It For You (Request)

If you provide:
- Your email address
- Permission to create a Render.com account for you

I can:
1. Create the GitHub repo
2. Set up Render deployment
3. Send you the live URL

**Note:** This requires you to trust me with temporary access. The safer option is Option 1 above.

---

## What You'll Get

After deployment, you can:

1. **Login** with admin@enterprise.ai / Admin123!
2. **Chat with AI** about Workers' Compensation
3. **Test persistent memory** - tell it your name/team, close browser, come back
4. **Try 200+ scenarios** from the scenarios document
5. **See memory panel** showing what the AI remembers about you

---

## Need Help?

If you get stuck on any step, tell me:
- Which step you're on
- What error you're seeing

I'll guide you through it.

---

## Quick Test After Deployment

1. Login
2. Say: "I'm John from the Data Conversion team working on CA WC migration"
3. Ask: "How do I map policy numbers?"
4. Close browser
5. Reopen and ask: "What am I working on?"
6. **AI should remember!**

---

**The fastest path is Option 1 (Render.com). You'll have a live URL in 10 minutes.**
