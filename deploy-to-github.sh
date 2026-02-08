#!/bin/bash

# Enterprise AI Platform - One-Command GitHub Deployment
# Usage: ./deploy-to-github.sh YOUR_GITHUB_USERNAME

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: GitHub username required${NC}"
    echo ""
    echo "Usage: ./deploy-to-github.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Example:"
    echo "  ./deploy-to-github.sh johnsmith"
    echo ""
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="enterprise-ai-platform"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Enterprise AI Platform - GitHub Deployment              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: Git is not installed${NC}"
    echo "Install from: https://git-scm.com/downloads"
    exit 1
fi
echo -e "${GREEN}✓ Git is installed${NC}"

if [ ! -f "Dockerfile.simple" ]; then
    echo -e "${RED}ERROR: Not in project directory${NC}"
    echo "Please run from: /mnt/okcomputer/output/enterprise-ai-platform"
    exit 1
fi
echo -e "${GREEN}✓ In correct directory${NC}"

# Step 2: Check GitHub authentication
echo ""
echo -e "${BLUE}Step 2: Checking GitHub authentication...${NC}"

if ! git ls-remote https://github.com/$GITHUB_USERNAME &> /dev/null; then
    echo -e "${YELLOW}⚠ Please enter your GitHub credentials when prompted${NC}"
fi

# Step 3: Create GitHub repository
echo ""
echo -e "${BLUE}Step 3: Creating GitHub repository...${NC}"

# Check if repo already exists
if curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/$GITHUB_USERNAME/$REPO_NAME | grep -q "200"; then
    echo -e "${YELLOW}⚠ Repository already exists${NC}"
    read -p "Continue with existing repo? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Create new repo
    echo "Creating repository: $REPO_NAME"
    curl -s -u $GITHUB_USERNAME https://api.github.com/user/repos \
        -d "{\"name\":\"$REPO_NAME\",\"description\":\"Enterprise AI Platform - Workers' Compensation Insurance Domain Expert\",\"private\":false}" > /dev/null
    echo -e "${GREEN}✓ GitHub repository created${NC}"
fi

# Step 4: Initialize and push
echo ""
echo -e "${BLUE}Step 4: Pushing code to GitHub...${NC}"

# Initialize git if not already
if [ ! -d ".git" ]; then
    git init
fi

# Configure git if needed
if [ -z "$(git config user.email)" ]; then
    git config user.email "deploy@enterprise.ai"
    git config user.name "Enterprise AI Deploy"
fi

# Add all files
git add .

# Commit
git commit -m "Initial commit - Enterprise AI Platform with persistent memory" || echo -e "${YELLOW}⚠ Nothing to commit${NC}"

# Add remote (force update if exists)
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main --force

echo -e "${GREEN}✓ Code pushed to GitHub${NC}"

# Step 5: Display success message
echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DEPLOYMENT COMPLETE!                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Go to Render.com${NC}"
echo "   URL: https://render.com"
echo ""
echo "2. ${YELLOW}Sign up with GitHub${NC}"
echo "   Click 'Get Started for Free' → 'Continue with GitHub'"
echo ""
echo "3. ${YELLOW}Create Blueprint${NC}"
echo "   Click 'New +' → 'Blueprint'"
echo "   Select: ${GREEN}$REPO_NAME${NC}"
echo ""
echo "4. ${YELLOW}Deploy${NC}"
echo "   Click 'Apply' and wait 5-10 minutes"
echo ""
echo "5. ${YELLOW}Access Your App${NC}"
echo "   URL: https://$REPO_NAME-xxx.onrender.com"
echo "   Login: ${GREEN}admin@enterprise.ai${NC} / ${GREEN}Admin123!${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}GitHub Repository:${NC}"
echo "https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo -e "${BLUE}Files Uploaded:${NC}"
git ls-files | wc -l | xargs echo "  Total files:"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Your Enterprise AI Platform will be live in ~10 minutes!${NC}"
echo ""

# Open browser (macOS/Linux)
if command -v open &> /dev/null; then
    echo "Opening Render.com..."
    open "https://render.com"
elif command -v xdg-open &> /dev/null; then
    echo "Opening Render.com..."
    xdg-open "https://render.com"
fi
