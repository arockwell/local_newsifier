# Deployment Configuration for CLI to FastAPI Migration

## Overview

This document details the deployment configuration changes needed to support the new FastAPI-based CLI architecture, covering local development, staging, and production environments.

## Environment Configuration

### Development Environment

#### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://newsifier:password@db:5432/newsifier
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src
    depends_on:
      - db
      - redis
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=newsifier
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=newsifier
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://newsifier:password@db:5432/newsifier
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    command: celery -A local_newsifier.celery_app worker --loglevel=info

  beat:
    build: .
    environment:
      - DATABASE_URL=postgresql://newsifier:password@db:5432/newsifier
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    command: celery -A local_newsifier.celery_app beat --loglevel=info

volumes:
  postgres_data:
  redis_data:
```

#### Local Development Script
```bash
#!/bin/bash
# scripts/dev.sh

# Start all services
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 5

# Run database migrations
docker-compose exec api alembic upgrade head

# Show logs
docker-compose logs -f api
```

### Staging Environment

#### Railway Configuration
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  },
  "services": [
    {
      "name": "api",
      "source": {
        "repo": "https://github.com/yourusername/local-newsifier"
      },
      "deploy": {
        "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "numReplicas": 2,
        "healthcheckPath": "/cli/health",
        "healthcheckTimeout": 30
      }
    },
    {
      "name": "worker",
      "source": {
        "repo": "https://github.com/yourusername/local-newsifier"
      },
      "deploy": {
        "startCommand": "celery -A local_newsifier.celery_app worker --loglevel=info",
        "numReplicas": 1
      }
    },
    {
      "name": "beat",
      "source": {
        "repo": "https://github.com/yourusername/local-newsifier"
      },
      "deploy": {
        "startCommand": "celery -A local_newsifier.celery_app beat --loglevel=info",
        "numReplicas": 1
      }
    }
  ]
}
```

### Production Environment

#### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: newsifier-api
  labels:
    app: newsifier
    component: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: newsifier
      component: api
  template:
    metadata:
      labels:
        app: newsifier
        component: api
    spec:
      containers:
      - name: api
        image: newsifier/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: newsifier-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: newsifier-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /cli/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /cli/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: newsifier-api
spec:
  selector:
    app: newsifier
    component: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Environment Variables

### API Service
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/newsifier
REDIS_URL=redis://host:6379
SECRET_KEY=your-secret-key-here

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.newsifier.com
MAX_WORKERS=4
WORKER_TIMEOUT=120
```

### CLI Configuration
```bash
# CLI-specific
NEWSIFIER_API_URL=https://api.newsifier.com
NEWSIFIER_TIMEOUT=30
NEWSIFIER_RETRY_COUNT=3
NEWSIFIER_CACHE_DIR=/tmp/newsifier-cache
```

## Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create non-root user
RUN useradd -m -u 1000 newsifier && chown -R newsifier:newsifier /app
USER newsifier

# Default command (overridden by docker-compose/k8s)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring and Logging

### Prometheus Metrics
```python
# src/api/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
import time

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Structured Logging
```python
# src/config/logging.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

    return logger

logger = setup_logging()
```

## Deployment Scripts

### Deploy Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=$1
VERSION=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <environment> <version>"
    exit 1
fi

echo "Deploying version $VERSION to $ENVIRONMENT..."

# Build and tag image
docker build -t newsifier/api:$VERSION .
docker tag newsifier/api:$VERSION newsifier/api:latest

# Push to registry
docker push newsifier/api:$VERSION
docker push newsifier/api:latest

# Deploy based on environment
case $ENVIRONMENT in
    staging)
        railway up
        ;;
    production)
        kubectl set image deployment/newsifier-api api=newsifier/api:$VERSION
        kubectl rollout status deployment/newsifier-api
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "Deployment complete!"
```

### Rollback Script
```bash
#!/bin/bash
# scripts/rollback.sh

set -e

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: ./rollback.sh <environment>"
    exit 1
fi

case $ENVIRONMENT in
    staging)
        railway rollback
        ;;
    production)
        kubectl rollout undo deployment/newsifier-api
        kubectl rollout status deployment/newsifier-api
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "Rollback complete!"
```

## Health Checks

### API Health Endpoint
```python
# src/api/routers/cli.py
@router.get("/health")
async def health_check(
    session: Session = Depends(get_session),
    redis_client: Redis = Depends(get_redis)
):
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": get_version(),
        "checks": {}
    }

    # Database check
    try:
        session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Redis check
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {str(e)}"

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```

## CLI Distribution

### PyPI Package
```toml
# pyproject.toml
[tool.poetry]
name = "newsifier-cli"
version = "2.0.0"
description = "CLI for Local Newsifier"
packages = [{include = "cli", from = "src"}]

[tool.poetry.scripts]
newsifier = "cli.commands:cli"

[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1"
httpx = "^0.27"
rich = "^13.0"
```

### Installation Instructions
```bash
# Install from PyPI
pip install newsifier-cli

# Configure API endpoint
export NEWSIFIER_API_URL=https://api.newsifier.com

# Use CLI
newsifier process https://example.com/article
newsifier report --days 7 --format json
newsifier health
```

## Migration Checklist

- [ ] Update Docker configuration
- [ ] Configure environment variables
- [ ] Set up health checks
- [ ] Configure monitoring
- [ ] Update CI/CD pipelines
- [ ] Test deployment scripts
- [ ] Document rollback procedures
- [ ] Update operational runbooks
