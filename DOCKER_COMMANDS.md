# Quick Docker Commands Reference

This is a quick reference guide for deploying and managing your Healthcare Agent application with Docker.

## 🚀 Quick Start (3 Commands)

```bash
# 1. Create environment file
cp env.template .env
# Edit .env and set JWT_SECRET_KEY

# 2. Build and start all services
docker-compose up -d --build

# 3. Initialize database
docker-compose exec backend python seed_admin.py
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql

---

## 📦 Essential Commands

### Build Services
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend

# Build without cache (clean build)
docker-compose build --no-cache
```

### Start Services
```bash
# Start all services (detached mode)
docker-compose up -d

# Start with build
docker-compose up -d --build

# Start specific service
docker-compose up -d backend

# Start and view logs (attached mode)
docker-compose up
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

---

## 📋 Monitoring Commands

### View Logs
```bash
# View all logs (follow mode)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker

# View last 100 lines
docker-compose logs --tail=100 backend

# View logs since 1 hour ago
docker-compose logs --since 1h backend
```

### Check Status
```bash
# List all containers
docker-compose ps

# View resource usage
docker stats

# View specific container stats
docker stats healthcare_backend

# Check health status
docker-compose ps
```

---

## 🔧 Database Commands

### MongoDB
```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh agentic_volunteer

# Backup database
docker-compose exec mongodb mongodump --out /data/backup --db agentic_volunteer

# Restore database
docker-compose exec mongodb mongorestore /data/backup

# Check MongoDB status
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Seed Data
```bash
# Create admin user
docker-compose exec backend python seed_admin.py

# Seed from CSV files
docker-compose exec backend python seed_from_csv.py

# Add test volunteer
docker-compose exec backend python add_test_volunteer.py
```

---

## 🐛 Debugging Commands

### Execute Commands in Container
```bash
# Open bash shell in backend
docker-compose exec backend bash

# Open shell in frontend
docker-compose exec frontend sh

# Run Python script
docker-compose exec backend python script_name.py

# Check environment variables
docker-compose exec backend env
docker-compose exec frontend env | grep NEXT_PUBLIC
```

### Inspect Services
```bash
# View service configuration
docker-compose config

# Inspect container
docker inspect healthcare_backend

# View container processes
docker-compose top

# View network information
docker network ls
docker network inspect hacke_healthcare_network
```

### Test Connectivity
```bash
# Test backend health endpoint
curl http://localhost:8000/health

# Test Redis
docker-compose exec redis redis-cli ping

# Test MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Test from within container
docker-compose exec backend curl http://localhost:8000/health
```

---

## 🔄 Update and Rebuild

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Update Specific Service
```bash
# Rebuild backend only
docker-compose build backend
docker-compose up -d --no-deps backend

# Rebuild frontend only
docker-compose build frontend
docker-compose up -d --no-deps frontend
```

---

## 🧹 Cleanup Commands

### Remove Containers
```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all
```

### Clean Docker System
```bash
# Remove unused containers, networks, images
docker system prune

# Remove everything (including volumes)
docker system prune -a --volumes

# Remove specific volume
docker volume rm hacke_mongodb_data
```

### Clean Build Cache
```bash
# Remove build cache
docker builder prune

# Remove all build cache
docker builder prune -a
```

---

## 📊 Scale Services

```bash
# Scale celery workers to 3
docker-compose up -d --scale celery_worker=3

# Scale back to 1
docker-compose up -d --scale celery_worker=1
```

---

## 💾 Backup and Restore

### Backup
```bash
# Backup MongoDB volume
docker run --rm \
  -v hacke_mongodb_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/mongodb_backup.tar.gz /data

# Backup Redis volume
docker run --rm \
  -v hacke_redis_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/redis_backup.tar.gz /data

# Export container to image
docker commit healthcare_backend healthcare_backend_backup
```

### Restore
```bash
# Restore MongoDB volume
docker run --rm \
  -v hacke_mongodb_data:/data \
  -v $(pwd):/backup \
  ubuntu bash -c "cd / && tar xzf /backup/mongodb_backup.tar.gz"

# Restore Redis volume
docker run --rm \
  -v hacke_redis_data:/data \
  -v $(pwd):/backup \
  ubuntu bash -c "cd / && tar xzf /backup/redis_backup.tar.gz"
```

---

## 🔐 Security Commands

### Generate Secrets
```bash
# Generate JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32

# Or using /dev/urandom
cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

### Check Security
```bash
# Scan images for vulnerabilities (requires Docker Scout)
docker scout cves healthcare_agent-backend
docker scout cves healthcare_agent-frontend

# Check for security issues
docker-compose config --quiet
```

---

## 🌐 Production Commands

### Deploy to Production
```bash
# 1. Set production environment
export COMPOSE_FILE=docker-compose.yml
export COMPOSE_PROJECT_NAME=healthcare_prod

# 2. Build production images
docker-compose build --no-cache

# 3. Start with resource limits
docker-compose up -d

# 4. Check health
docker-compose ps
docker-compose logs --tail=50
```

### Update Production
```bash
# Zero-downtime update
docker-compose build backend
docker-compose up -d --no-deps --scale backend=2 backend
sleep 30
docker-compose up -d --no-deps --scale backend=1 backend
```

---

## 🎯 Common Workflows

### Fresh Start
```bash
# Complete fresh start
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose exec backend python seed_admin.py
```

### Quick Restart
```bash
# Quick restart after code change
docker-compose restart backend frontend
```

### View All Logs
```bash
# View logs from all services
docker-compose logs -f --tail=50
```

### Health Check All Services
```bash
# Check all services
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:3000
docker-compose exec redis redis-cli ping
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 📞 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs backend

# Check configuration
docker-compose config

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

### Port Conflicts
```bash
# Find what's using a port
lsof -i :8000
lsof -i :3000

# Kill process
kill -9 <PID>
```

### Database Issues
```bash
# Check MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb

# Reset database (WARNING: DELETES DATA)
docker-compose down
docker volume rm hacke_mongodb_data
docker-compose up -d
```

### Network Issues
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d

# Test connectivity between containers
docker-compose exec backend ping mongodb
docker-compose exec backend ping redis
```

---

## 🎓 Useful Docker Commands

```bash
# View Docker disk usage
docker system df

# View detailed disk usage
docker system df -v

# List all volumes
docker volume ls

# List all networks
docker network ls

# View Docker info
docker info

# View Docker version
docker version
```

---

## 📝 Pro Tips

1. **Always use `-d` flag** for production to run in detached mode
2. **Check logs regularly** with `docker-compose logs -f`
3. **Backup before updates** using volume backup commands
4. **Use `--no-cache`** when troubleshooting build issues
5. **Monitor resources** with `docker stats`
6. **Keep images updated** with `docker-compose pull`
7. **Clean up regularly** with `docker system prune`

---

**Quick Reference Card:**
```bash
# Most used commands
docker-compose up -d --build      # Build and start
docker-compose down               # Stop
docker-compose restart            # Restart
docker-compose logs -f            # View logs
docker-compose ps                 # Check status
docker-compose exec backend bash  # Shell access
```

---

For detailed deployment guide, see [DEPLOYMENT.md](./DEPLOYMENT.md)

