# 🐳 Docker Deployment Guide

This guide explains how to deploy the Website Content Search application using Docker Compose.

## 📋 Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **At least 4GB RAM** available for all services

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd search-engine
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Weaviate**: http://localhost:8080

## 📁 Docker Compose Services

### 🔍 Weaviate (Vector Database)
- **Image**: `semitechnologies/weaviate:1.32.1`
- **Ports**: 8080 (HTTP), 50051 (gRPC)
- **Volume**: Persistent data storage
- **Health Check**: Automatic readiness verification

### 🔧 Backend (FastAPI)
- **Build**: Custom Dockerfile from `./backend`
- **Port**: 8000
- **Dependencies**: Weaviate
- **Environment**: CORS configuration for frontend

### 🌐 Frontend (Next.js)
- **Build**: Custom Dockerfile from `./frontend`
- **Port**: 3000
- **Dependencies**: Backend
- **Environment**: API URL configuration

## 🛠️ Service Dependencies

```
Frontend → Backend → Weaviate
```

Services start in the correct order with health checks:
1. **Weaviate** starts first and waits for readiness
2. **Backend** starts after Weaviate is healthy
3. **Frontend** starts after Backend is healthy

## 📊 Monitoring

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs weaviate

# Follow logs in real-time
docker-compose logs -f
```

### Health Checks
All services include health checks:
- **Weaviate**: Checks `/v1/.well-known/ready` endpoint
- **Backend**: Checks `/docs` endpoint
- **Frontend**: Checks root endpoint

## 🔧 Configuration

### Environment Variables

#### Backend Environment
```yaml
WEAVIATE_URL: http://weaviate:8080
CORS_ORIGINS: http://localhost:3000,http://frontend:3000
```

#### Frontend Environment
```yaml
NEXT_PUBLIC_API_URL: http://localhost:8000
```

#### Weaviate Environment
```yaml
QUERY_DEFAULTS_LIMIT: 25
AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
DEFAULT_VECTORIZER_MODULE: "none"
ENABLE_MODULES: ""
CLUSTER_HOSTNAME: "node1"
```

## 🚀 Production Deployment

### 1. Environment-Specific Configuration
Create environment-specific compose files:

```bash
# Development
docker-compose -f docker-compose.yml up -d

# Production (with additional config)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Production Optimizations
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - WEAVIATE_URL=http://weaviate:8080
      - CORS_ORIGINS=https://yourdomain.com
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
  
  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  weaviate:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 3. Reverse Proxy Setup
For production, add a reverse proxy (nginx/traefik):

```yaml
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :8080

# Stop conflicting services
sudo systemctl stop <service-name>
```

#### 2. Memory Issues
```bash
# Check available memory
free -h

# Increase Docker memory limit
# In Docker Desktop: Settings → Resources → Memory
```

#### 3. Build Failures
```bash
# Clean build
docker-compose build --no-cache

# Check build logs
docker-compose build backend
docker-compose build frontend
```

#### 4. Service Not Starting
```bash
# Check service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build
```

### Debug Commands

#### Check Service Health
```bash
# All services
docker-compose ps

# Specific service health
docker inspect <container-name> | grep Health -A 10
```

#### Access Service Shell
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Weaviate shell
docker-compose exec weaviate sh
```

#### View Resource Usage
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## 🧹 Maintenance

### Regular Maintenance
```bash
# Update images
docker-compose pull

# Rebuild services
docker-compose up -d --build

# Clean up unused resources
docker system prune -f

# Clean up volumes (⚠️ removes data)
docker volume prune -f
```

### Backup Weaviate Data
```bash
# Create backup
docker run --rm -v weaviate_data:/data -v $(pwd):/backup alpine tar czf /backup/weaviate-backup.tar.gz -C /data .

# Restore backup
docker run --rm -v weaviate_data:/data -v $(pwd):/backup alpine tar xzf /backup/weaviate-backup.tar.gz -C /data
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale with load balancer
# Add nginx/traefik configuration for load balancing
```

### Resource Scaling
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
  
  weaviate:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

## 🛡️ Security

### Production Security Checklist
- [ ] Use HTTPS with valid certificates
- [ ] Configure proper CORS origins
- [ ] Set up firewall rules
- [ ] Use secrets management for sensitive data
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### Secrets Management
```yaml
# Use Docker secrets for sensitive data
services:
  backend:
    secrets:
      - api_key
      - database_password

secrets:
  api_key:
    file: ./secrets/api_key.txt
  database_password:
    file: ./secrets/db_password.txt
```

## 📝 Useful Commands

### Development
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Production
```bash
# Start in detached mode
docker-compose up -d

# Update and restart
docker-compose pull && docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3

# Monitor resources
docker stats
```

---

**🎯 Ready to deploy!** Run `docker-compose up -d` to start all services. 