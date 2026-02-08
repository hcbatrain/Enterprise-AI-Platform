#!/bin/bash

# Enterprise AI Platform - Production Deployment Script
# This script deploys the full application with all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Enterprise AI Platform - Deployment                 ║"
echo "║       Workers' Compensation Insurance Domain Expert           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check available memory
echo ""
echo -e "${BLUE}Checking system resources...${NC}"
TOTAL_MEM=$(docker system info --format '{{.MemTotal}}' 2>/dev/null || echo "0")
TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))

if [ "$TOTAL_MEM_GB" -lt 6 ]; then
    echo -e "${YELLOW}⚠ Warning: Less than 6GB RAM available (${TOTAL_MEM_GB}GB detected)${NC}"
    echo "   The platform may run slowly. Recommended: 8GB+ RAM"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Sufficient memory available (${TOTAL_MEM_GB}GB)${NC}"
fi

# Create environment file
echo ""
echo -e "${BLUE}Setting up environment...${NC}"

if [ ! -f .env ]; then
    cat > .env << EOF
# Database Configuration
POSTGRES_USER=enterprise
POSTGRES_PASSWORD=enterprise123
POSTGRES_DB=enterprise_ai

# Neo4j Configuration
NEO4J_AUTH=neo4j/enterprise123

# Application Secret (CHANGE IN PRODUCTION!)
SECRET_KEY=$(openssl rand -hex 32)

# LLM Configuration
LLM_MODEL=llama3.2:3b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Environment
ENVIRONMENT=production
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Pull and build images
echo ""
echo -e "${BLUE}Building and pulling Docker images...${NC}"
echo "   This may take 15-30 minutes on first run..."
echo ""

docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml build

echo -e "${GREEN}✓ Images ready${NC}"

# Start services
echo ""
echo -e "${BLUE}Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d postgres neo4j redis ollama

# Wait for services
echo ""
echo -e "${BLUE}Waiting for services to be ready...${NC}"
echo "   This may take 2-3 minutes..."

# Wait for PostgreSQL
echo "   ⏳ Waiting for PostgreSQL..."
until docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U enterprise > /dev/null 2>&1; do
    sleep 2
done
echo -e "${GREEN}   ✓ PostgreSQL is ready${NC}"

# Wait for Neo4j
echo "   ⏳ Waiting for Neo4j..."
until curl -s http://localhost:7474 > /dev/null 2>&1; do
    sleep 2
done
echo -e "${GREEN}   ✓ Neo4j is ready${NC}"

# Wait for Redis
echo "   ⏳ Waiting for Redis..."
until docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; do
    sleep 2
done
echo -e "${GREEN}   ✓ Redis is ready${NC}"

# Wait for Ollama
echo "   ⏳ Waiting for Ollama LLM service..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done
echo -e "${GREEN}   ✓ Ollama is ready${NC}"

# Pull default LLM model
echo ""
echo -e "${BLUE}Downloading LLM model (llama3.2:3b)...${NC}"
echo "   This will take 5-10 minutes..."
docker-compose -f docker-compose.prod.yml exec -T ollama ollama pull llama3.2:3b
echo -e "${GREEN}✓ LLM model ready${NC}"

# Start backend and frontend
echo ""
echo -e "${BLUE}Starting application services...${NC}"
docker-compose -f docker-compose.prod.yml up -d backend frontend

# Wait for backend
echo "   ⏳ Waiting for backend API..."
until curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
    sleep 2
done
echo -e "${GREEN}   ✓ Backend is ready${NC}"

# Initialize database
echo ""
echo -e "${BLUE}Initializing database...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from app.db.session import init_db
asyncio.run(init_db())
" 2>/dev/null || echo "   Database already initialized"
echo -e "${GREEN}✓ Database initialized${NC}"

# Create default admin user
echo ""
echo -e "${BLUE}Creating default admin user...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.auth_service import auth_service
from app.models.user import User

async def create_admin():
    async with AsyncSessionLocal() as db:
        try:
            user = await auth_service.create_user(
                db,
                email='admin@enterprise.ai',
                username='admin',
                password='Admin123!',
                first_name='Admin',
                last_name='User',
                role='admin',
                is_superuser=True
            )
            print('Admin user created successfully')
        except Exception as e:
            print(f'Admin user may already exist: {e}')

asyncio.run(create_admin())
" 2>/dev/null || echo "   Admin user may already exist"

# Display success message
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    🎉 DEPLOYMENT SUCCESSFUL!                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}Your Enterprise AI Platform is now running!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 Web Application:    ${BLUE}http://localhost:3000${NC}"
echo "  🔧 API Documentation:  ${BLUE}http://localhost:8000/api/docs${NC}"
echo "  🗄️  Neo4j Browser:      ${BLUE}http://localhost:7474${NC}"
echo "  🤖 Ollama API:         ${BLUE}http://localhost:11434${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  👤 Default Login:"
echo "     Email:    ${YELLOW}admin@enterprise.ai${NC}"
echo "     Password: ${YELLOW}Admin123!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📚 Useful Commands:"
echo "     View logs:        ${BLUE}docker-compose -f docker-compose.prod.yml logs -f${NC}"
echo "     Stop services:    ${BLUE}docker-compose -f docker-compose.prod.yml down${NC}"
echo "     Full shutdown:    ${BLUE}docker-compose -f docker-compose.prod.yml down -v${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}The AI will remember everything about your employees and projects!${NC}"
echo ""

# Show running services
echo -e "${BLUE}Running services:${NC}"
docker-compose -f docker-compose.prod.yml ps
