# Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Docker Desktop with WSL 2 integration enabled
- 8GB+ RAM available for containers
- Google AI Studio API key
- 20GB+ disk space

### One-Command Deployment
```bash
# Navigate to project directory
cd /home/scott/agent-orchestration

# Set environment variables
export GOOGLE_API_KEY="your-google-ai-studio-key"
export POSTGRES_PASSWORD="secure-database-password"

# Deploy the complete system
./deploy.sh
```

## 🏗️ Manual Step-by-Step Deployment

### Step 1: Environment Setup
```bash
# Create environment file
cat > .env << EOF
GOOGLE_API_KEY=your-google-ai-studio-key-here
POSTGRES_PASSWORD=secure-database-password-here
REDIS_URL=redis://redis:6379
DEBUG=false
LOG_LEVEL=INFO
EOF
```

### Step 2: Database Infrastructure
```bash
# Start PostgreSQL database
docker-compose up -d postgres

# Wait for database to be ready
timeout 60 bash -c 'until docker-compose exec postgres pg_isready -U cognee_user -d cognee_agents; do sleep 2; done'

# Start PgBouncer connection pooler
docker-compose up -d pgbouncer

# Verify database connection
docker-compose exec postgres psql -U cognee_user -d cognee_agents -c "SELECT 'Database Ready!' as status;"
```

### Step 3: Cache & Queue Services  
```bash
# Start Redis cache
docker-compose up -d redis

# Verify Redis is running
docker-compose exec redis redis-cli ping
```

### Step 4: Agent Orchestration Service
```bash
# Build and start agent orchestrator
docker-compose build agent-orchestrator
docker-compose up -d agent-orchestrator

# Start background worker
docker-compose up -d celery-worker
```

### Step 5: Verification & Testing
```bash
# Check all services are healthy
docker-compose ps

# Test API endpoint
curl http://localhost:8000/health

# Test document analysis
curl -X POST http://localhost:8000/api/analyze-document \
  -H "Content-Type: application/json" \
  -d '{
    "content": "SERVICE AGREEMENT between TechCorp LLC and AI Services Inc. Contract value: $150,000",
    "filename": "test-contract.txt",
    "priority": "normal"
  }'
```

## 🔧 Configuration Options

### Environment Variables

#### Required Configuration
```bash
# API Keys
GOOGLE_API_KEY=          # Google AI Studio API key for Gemini models
POSTGRES_PASSWORD=       # PostgreSQL database password

# Database Configuration (Optional - defaults provided)
POSTGRES_HOST=localhost  # PostgreSQL host
POSTGRES_PORT=5432       # PostgreSQL port
POSTGRES_USER=cognee_user
POSTGRES_DB=cognee_agents
USE_PGBOUNCER=true       # Use connection pooling
```

#### Performance Tuning
```bash
# Agent Configuration
MAX_PARALLEL_AGENTS=6           # Maximum concurrent agents
AGENT_TIMEOUT_SECONDS=120       # Agent processing timeout
VALIDATION_TIMEOUT_SECONDS=60   # Validation timeout

# Database Pool Configuration
POSTGRES_POOL_SIZE=20           # Connection pool size
POSTGRES_MAX_OVERFLOW=30        # Maximum overflow connections

# Business Rules
HIGH_VALUE_THRESHOLD=10000000   # $10M threshold for mandatory review
AUTO_APPROVE_THRESHOLD=0.80     # 80% confidence for auto-approval
```

### Docker Compose Overrides
Create `docker-compose.override.yml` for custom configurations:

```yaml
services:
  postgres:
    environment:
      # Increase connection limit for high-volume environments
      - POSTGRES_MAX_CONNECTIONS=400
    
  agent-orchestrator:
    environment:
      # Enable debug logging
      - LOG_LEVEL=DEBUG
      - DEBUG=true
    
    # Add resource limits for production
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

## 🌐 Production Deployment Considerations

### Hardware Requirements

#### Minimum Production Setup
- **CPU:** 4 cores (8 threads)
- **RAM:** 16GB
- **Storage:** 100GB SSD
- **Network:** 1Gbps connection

#### Recommended Production Setup  
- **CPU:** 8 cores (16 threads)
- **RAM:** 32GB
- **Storage:** 500GB NVMe SSD
- **Network:** 10Gbps connection with redundancy

### Database Configuration for Production

#### PostgreSQL Optimization
```sql
-- Production PostgreSQL settings
ALTER SYSTEM SET max_connections = 400;
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

SELECT pg_reload_conf();
```

#### Backup Strategy
```bash
# Daily automated backups
docker-compose exec postgres pg_dump -U cognee_user cognee_agents > backup_$(date +%Y%m%d).sql

# Point-in-time recovery setup
docker-compose exec postgres psql -U cognee_user -d cognee_agents -c "
  ALTER SYSTEM SET wal_level = replica;
  ALTER SYSTEM SET archive_mode = on;
  ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';
  SELECT pg_reload_conf();
"
```

### Security Configuration

#### Database Security
```bash
# Create read-only user for monitoring
docker-compose exec postgres psql -U cognee_user -d cognee_agents -c "
  CREATE USER monitor_user WITH PASSWORD 'monitor_password';
  GRANT CONNECT ON DATABASE cognee_agents TO monitor_user;
  GRANT USAGE ON SCHEMA documents, analysis, agents TO monitor_user;
  GRANT SELECT ON ALL TABLES IN SCHEMA documents, analysis, agents TO monitor_user;
"
```

#### Network Security
```yaml
# Production docker-compose security
services:
  postgres:
    # Don't expose PostgreSQL port externally
    ports: []
    
  pgbouncer:
    # Don't expose PgBouncer port externally  
    ports: []
    
  agent-orchestrator:
    # Use environment-specific ports
    ports:
      - "443:8000"  # HTTPS only
```

### SSL/TLS Configuration
```bash
# Generate SSL certificates for production
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key \
  -out ssl/certificate.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Update docker-compose for HTTPS
services:
  agent-orchestrator:
    volumes:
      - ./ssl:/app/ssl
    environment:
      - SSL_CERT_PATH=/app/ssl/certificate.crt
      - SSL_KEY_PATH=/app/ssl/private.key
```

## 📊 Monitoring & Observability

### Health Check Endpoints
```bash
# System health
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/api/system-status

# Agent performance metrics
curl http://localhost:8000/api/agent-performance?hours_back=24

# Review queue status
curl http://localhost:8000/api/review-queue
```

### Log Management
```bash
# View orchestrator logs
docker-compose logs -f agent-orchestrator

# View database logs
docker-compose logs -f postgres

# View all service logs
docker-compose logs -f

# Export logs for analysis
docker-compose logs --since "24h" > system_logs_$(date +%Y%m%d).log
```

### Performance Monitoring
```bash
# Monitor container resource usage
docker stats $(docker-compose ps -q)

# Database performance monitoring
docker-compose exec postgres psql -U cognee_user -d cognee_agents -c "
  SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
  FROM pg_stat_user_tables 
  ORDER BY n_tup_ins DESC;
"
```

## 🔄 Maintenance & Updates

### Regular Maintenance Tasks

#### Daily
```bash
# Check system health
./scripts/health_check.sh

# Verify backup completion
ls -la backups/backup_$(date +%Y%m%d)*
```

#### Weekly  
```bash
# Update containers to latest versions
docker-compose pull
docker-compose up -d

# Database maintenance
docker-compose exec postgres psql -U cognee_user -d cognee_agents -c "
  VACUUM ANALYZE;
  REINDEX DATABASE cognee_agents;
"
```

#### Monthly
```bash
# Review and archive old logs
find ./logs -name "*.log" -mtime +30 -delete

# Update dependencies
docker-compose build --no-cache
```

### Scaling Operations

#### Horizontal Scaling
```bash
# Scale agent workers
docker-compose up -d --scale celery-worker=4

# Add read replica (requires PostgreSQL replication setup)
docker-compose -f docker-compose.yml -f docker-compose.replica.yml up -d
```

#### Vertical Scaling
```yaml
# Update resource limits
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
```

---

**Next:** [API Documentation →](./05-api-documentation.md)