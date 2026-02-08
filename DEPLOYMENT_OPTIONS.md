# Enterprise AI Platform - Deployment Options

## Option 1: Quick Local Deployment (Recommended for Testing) ⭐

### Requirements
- Docker & Docker Compose
- 8GB+ RAM recommended (6GB minimum)
- 20GB free disk space

### One-Command Deployment

```bash
cd /mnt/okcomputer/output/enterprise-ai-platform
./deploy.sh
```

This script will:
1. Check prerequisites
2. Create environment configuration
3. Pull and build Docker images
4. Start all services (PostgreSQL, Neo4j, Redis, Ollama, Backend, Frontend)
5. Download the LLM model
6. Initialize the database
7. Create default admin user

### After Deployment

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web Application** | http://localhost:3000 | admin@enterprise.ai / Admin123! |
| **API Documentation** | http://localhost:8000/api/docs | Same as above |
| **Neo4j Browser** | http://localhost:7474 | neo4j / enterprise123 |

### Stop the Application

```bash
docker-compose -f docker-compose.prod.yml down
```

---

## Option 2: Cloud Deployment - Render.com

### Prerequisites
1. GitHub account with code pushed
2. Free Render.com account
3. Neo4j Aura account (free tier)

### Step 1: Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/enterprise-ai-platform.git
git push -u origin main
```

### Step 2: Deploy to Render

1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml` and deploy all services

### Step 3: Configure Environment Variables

After deployment, set these in Render dashboard:
- `NEO4J_URI` - Your Neo4j Aura connection string
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

---

## Option 3: Cloud Deployment - AWS (Production)

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        AWS VPC                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   ALB        │  │  ECS Fargate │  │   RDS PostgreSQL │  │
│  │  (HTTPS)     │  │  (Backend)   │  │   + pgvector     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────────────────┐  │
│  │ CloudFront   │  │  S3 (Frontend│  │ ElastiCache      │  │
│  │  (CDN)       │  │   Static)    │  │   Redis          │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Neo4j Aura (Managed)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Estimated Costs
- ECS Fargate: ~$50-100/month
- RDS PostgreSQL: ~$15-30/month
- ElastiCache Redis: ~$15/month
- Neo4j Aura: Free tier available
- ALB: ~$20/month
- **Total: ~$100-165/month**

---

## Option 4: Simplified Single-Container Demo

For quick testing without full infrastructure, use this simplified version:

```bash
# Build and run simplified demo
docker build -f Dockerfile.demo -t enterprise-ai-demo .
docker run -p 8080:8080 enterprise-ai-demo
```

**Note:** This is a simplified demo with:
- In-memory database (data lost on restart)
- Mock LLM responses
- Limited functionality

---

## Troubleshooting

### Issue: "Not enough memory"
**Solution:** Close other applications or upgrade your machine. The platform needs 6-8GB RAM.

### Issue: "Port already in use"
**Solution:** Change ports in `docker-compose.prod.yml`:
```yaml
ports:
  - "3001:80"  # Instead of 3000:80
```

### Issue: "Ollama model download fails"
**Solution:** Manually pull the model:
```bash
docker-compose -f docker-compose.prod.yml exec ollama ollama pull llama3.2:3b
```

### Issue: "Database connection failed"
**Solution:** Wait longer for PostgreSQL to start, then restart:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

---

## Need Help?

If you're having trouble deploying, I can:

1. **Create a video walkthrough** of the deployment process
2. **Set up a demo environment** on my infrastructure
3. **Provide 1-on-1 support** for your specific setup

---

## Quick Start Checklist

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] 8GB+ RAM available
- [ ] Run `./deploy.sh`
- [ ] Wait 10-15 minutes for setup
- [ ] Access http://localhost:3000
- [ ] Login with admin@enterprise.ai / Admin123!
- [ ] Test persistent memory feature

---

**The fastest way to test is Option 1 - Local Deployment with `./deploy.sh`**
