# Cloud Deployment Guide

## Option A: Render.com (Recommended - Free Tier)

### Prerequisites
1. GitHub account with your code pushed
2. Free Render.com account
3. Neo4j Aura account (free tier)

### Step 1: Set Up Neo4j Aura (Free)
1. Go to https://neo4j.com/cloud/aura/
2. Sign up for a free account
3. Create a new database
4. Save the connection URI and credentials

### Step 2: Deploy to Render
1. Fork/push this repository to GitHub
2. Go to https://dashboard.render.com/
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will detect `render.yaml` and create all services

### Step 3: Configure Environment Variables
After services are created, add these environment variables:

**Backend Service:**
- `NEO4J_URI`: Your Neo4j Aura connection string
- `NEO4J_USER`: Your Neo4j username
- `NEO4J_PASSWORD`: Your Neo4j password

### Step 4: Access Your Application
- Frontend: `https://enterprise-ai-frontend.onrender.com`
- Backend API: `https://enterprise-ai-backend.onrender.com/api`
- API Docs: `https://enterprise-ai-backend.onrender.com/api/docs`

---

## Option B: Railway.app (Alternative)

### Step 1: Create Project
1. Go to https://railway.app
2. Create new project from GitHub repo
3. Add PostgreSQL, Redis plugins

### Step 2: Deploy Services
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

---

## Option C: AWS Deployment (Production)

For production deployment on AWS, use:
- **ECS Fargate** for container orchestration
- **RDS PostgreSQL** with pgvector extension
- **ElastiCache Redis**
- **Neo4j Aura** or self-managed on EC2
- **Application Load Balancer**
- **Route 53** for DNS

See `infrastructure/aws/` for Terraform configurations.

---

## Important Notes

### LLM Service Considerations
The LLM service (Ollama) requires significant compute resources:
- **Minimum**: 4GB RAM, 2 vCPUs
- **Recommended**: 8GB+ RAM, 4 vCPUs

For cloud deployment, you have options:

1. **Use External LLM API** (OpenAI, Anthropic)
   - Modify `backend/app/services/llm_service.py` to use API instead of local Ollama
   - Update environment variables

2. **Deploy Ollama on GPU Instance**
   - Use AWS EC2 g4dn.xlarge or similar
   - Higher cost but better performance

3. **Use Together.ai or RunPod**
   - Serverless GPU inference
   - Pay-per-use pricing

### Free Tier Limitations
- Render free tier: Services sleep after 15 min inactivity
- Neo4j Aura free: 200k nodes/relationships limit
- Consider upgrading for production use

---

## Quick Local Demo (No Cloud Needed)

For immediate testing without cloud deployment:

```bash
# Clone and run locally
git clone <your-repo>
cd enterprise-ai-platform
./quick-start.sh
```

Access at http://localhost after services start.
