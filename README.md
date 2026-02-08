# Enterprise AI Platform

A production-ready, offline, compliant, role-aware AI platform for insurance software delivery organizations.

## Features

- **Complete Offline Operation**: All AI processing occurs within organizational boundaries
- **Role-Aware Intelligence**: Dynamically adapts responses based on user role and context
- **Domain Expertise**: Deep knowledge of Workers' Compensation insurance and Sapiens CourseSuite
- **RAG (Retrieval-Augmented Generation)**: Grounded answers with source attribution
- **Knowledge Graph**: Semantic relationships between business concepts, systems, and data
- **Document Management**: Upload, process, and search documents
- **Compliance Ready**: Built for SOC 2, ISO 27001, GDPR, and CMMI

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│   LLM Service   │
│   (Port 80)      │     │   (Port 8000)    │     │  (Ollama/vLLM)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │     Neo4j       │     │     Redis       │
│  + pgvector     │     │ Knowledge Graph │     │   Cache/Queue   │
│  (Port 5432)    │     │  (Port 7474)    │     │  (Port 6379)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM recommended
- For GPU acceleration: NVIDIA Docker runtime

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd enterprise-ai-platform
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
docker-compose up -d
```

4. Pull the LLM model:
```bash
docker-compose exec llm-service ollama pull llama2:7b
```

5. Access the application:
- Frontend: http://localhost
- API Docs: http://localhost:8000/api/docs
- Neo4j Browser: http://localhost:7474

### Default Credentials

- PostgreSQL: enterprise / enterprise123
- Neo4j: neo4j / enterprise123

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## User Roles

The platform supports the following roles with different access levels:

| Role | Description |
|------|-------------|
| Business Analyst | Business requirements, workflows, rules |
| Developer | Code, APIs, technical implementation |
| QA Tester | Test cases, scenarios, validation |
| Technical Architect | System design, architecture decisions |
| Project Manager | Project tracking, reports |
| Manager | Team metrics, organizational data |
| Administrator | Full system access |
| Executive | Dashboards, summaries |

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `GET /api/v1/auth/me` - Get current user

### Chat
- `GET /api/v1/chat/conversations` - List conversations
- `POST /api/v1/chat/conversations` - Create conversation
- `POST /api/v1/chat/messages` - Send message

### Documents
- `GET /api/v1/documents` - List documents
- `POST /api/v1/documents/upload` - Upload document
- `DELETE /api/v1/documents/{id}` - Delete document

### Knowledge Graph
- `GET /api/v1/knowledge/stats` - Get statistics
- `GET /api/v1/knowledge/entities/search` - Search entities
- `GET /api/v1/knowledge/entities/{id}` - Get entity details

### Search
- `GET /api/v1/search/documents` - Search documents
- `GET /api/v1/search/unified` - Unified search

## Configuration

Environment variables (in `.env`):

```env
# Database
POSTGRES_USER=enterprise
POSTGRES_PASSWORD=enterprise123
POSTGRES_DB=enterprise_ai

# Neo4j
NEO4J_AUTH=neo4j/enterprise123

# Security
SECRET_KEY=your-super-secret-key

# LLM
LLM_MODEL=llama2:7b
GPU_LAYERS=0
```

## Production Deployment

1. Update `.env` with production values
2. Use strong passwords
3. Enable HTTPS
4. Configure backup schedules
5. Set up monitoring

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Monitoring

The platform includes health check endpoints:
- `GET /health` - Service health
- `GET /api/v1/knowledge/stats` - Knowledge graph statistics

## Troubleshooting

### LLM Service Not Responding
```bash
docker-compose logs llm-service
docker-compose exec llm-service ollama list
```

### Database Connection Issues
```bash
docker-compose ps
docker-compose logs postgres
```

### Document Processing Failed
Check document status in the UI or API:
```bash
curl http://localhost:8000/api/v1/documents
```

## License

Proprietary - Internal Use Only

## Support

For support, contact your system administrator or IT department.
