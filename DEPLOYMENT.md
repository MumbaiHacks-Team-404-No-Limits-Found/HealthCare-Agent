# Healthcare Agent - Docker Deployment Guide

This guide provides step-by-step instructions to deploy the Healthcare Agent application using Docker.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository (if needed)

Verify installations:
```bash
docker --version
docker-compose --version
```

## 🏗️ Architecture

The application consists of the following services:

1. **MongoDB**: Database for storing volunteer, camp, and assignment data
2. **Redis**: Cache and message broker for Celery tasks
3. **Backend (FastAPI)**: REST API and GraphQL endpoint
4. **Celery Worker**: Background task processor
5. **Celery Beat**: Periodic task scheduler
6. **Frontend (Next.js)**: Web application UI

## 🚀 Quick Start Deployment

### Step 1: Clone or Navigate to Project

```bash
cd /Users/dokuparthinilesh/Desktop/hacke
```

### Step 2: Create Environment File

Copy the template and configure your environment variables:

```bash
cp env.template .env
```

Edit the `.env` file with your actual values:

```bash
nano .env
# or
vim .env
# or use any text editor
```

**Required Settings:**
- `JWT_SECRET_KEY`: Generate a strong random key (minimum 32 characters)

**Optional Settings:**
- Twilio credentials (for SMS/WhatsApp notifications)
- NotificationAPI credentials (alternative to Twilio)

### Step 3: Generate JWT Secret Key

Generate a secure JWT secret key:

```bash
# Option 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Option 3: Using /dev/urandom
cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

Copy the generated key and add it to your `.env` file:
```
JWT_SECRET_KEY=your_generated_key_here
```

### Step 4: Build Docker Images

Build all services (this may take 5-10 minutes on first run):

```bash
docker-compose build
```

To build without cache (if you encounter issues):

```bash
docker-compose build --no-cache
```

### Step 5: Start All Services

Start all containers in detached mode:

```bash
docker-compose up -d
```

Check if all services are running:

```bash
docker-compose ps
```

You should see all services with "Up" status.

### Step 6: View Logs

To view logs from all services:

```bash
docker-compose logs -f
```

To view logs from a specific service:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

### Step 7: Initialize Database (First Time Only)

Seed the database with initial data:

```bash
# Create admin user
docker-compose exec backend python seed_admin.py

# Seed initial data from CSV files (optional)
docker-compose exec backend python seed_from_csv.py
```

### Step 8: Access the Application

Once all services are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql

## 🔧 Common Commands

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This deletes all data)
docker-compose down -v
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### View Logs

```bash
# All services (follow mode)
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Execute Commands in Containers

```bash
# Open shell in backend container
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python script_name.py

# Open MongoDB shell
docker-compose exec mongodb mongosh agentic_volunteer
```

### Check Service Health

```bash
# View running containers
docker-compose ps

# Check resource usage
docker stats

# View specific service details
docker-compose logs backend --tail=50
```

## 🔍 Troubleshooting

### Services Won't Start

**Problem**: Containers fail to start or exit immediately.

**Solution**:
```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs frontend

# Rebuild images
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port Already in Use

**Problem**: Error message about ports 3000, 8000, 27017, or 6379 being in use.

**Solution**:
```bash
# Find what's using the port (e.g., 8000)
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml
# For example, change "8000:8000" to "8001:8000"
```

### Database Connection Issues

**Problem**: Backend can't connect to MongoDB.

**Solution**:
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# Check MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb

# Verify MongoDB health
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Frontend Can't Reach Backend

**Problem**: Frontend shows API connection errors.

**Solution**:
1. Check backend is running: `docker-compose ps backend`
2. Test backend health: `curl http://localhost:8000/health`
3. Check CORS settings in `.env` file
4. Verify environment variables in frontend container:
   ```bash
   docker-compose exec frontend env | grep NEXT_PUBLIC
   ```

### Celery Worker Issues

**Problem**: Background tasks not executing.

**Solution**:
```bash
# Check Celery worker logs
docker-compose logs celery_worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery services
docker-compose restart celery_worker celery_beat
```

### Out of Disk Space

**Problem**: Docker running out of disk space.

**Solution**:
```bash
# Remove unused Docker resources
docker system prune -a

# Remove specific volumes (WARNING: This deletes data)
docker volume rm hacke_mongodb_data
docker volume rm hacke_redis_data
```

## 🔄 Updating the Application

### Pull Latest Changes

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Restart services
docker-compose down
docker-compose up -d
```

### Update Dependencies

**Backend:**
```bash
# Update requirements.txt then rebuild
docker-compose build backend
docker-compose restart backend
```

**Frontend:**
```bash
# Update package.json then rebuild
docker-compose build frontend
docker-compose restart frontend
```

## 💾 Backup and Restore

### Backup MongoDB Data

```bash
# Create backup
docker-compose exec mongodb mongodump --out /data/backup --db agentic_volunteer

# Copy backup to host
docker cp healthcare_mongodb:/data/backup ./mongodb_backup
```

### Restore MongoDB Data

```bash
# Copy backup to container
docker cp ./mongodb_backup healthcare_mongodb:/data/backup

# Restore backup
docker-compose exec mongodb mongorestore /data/backup
```

### Export Docker Volumes

```bash
# Backup MongoDB volume
docker run --rm -v hacke_mongodb_data:/data -v $(pwd):/backup ubuntu tar czf /backup/mongodb_backup.tar.gz /data

# Backup Redis volume
docker run --rm -v hacke_redis_data:/data -v $(pwd):/backup ubuntu tar czf /backup/redis_backup.tar.gz /data
```

## 🌐 Production Deployment

For production deployment, consider these additional steps:

### 1. Use Production Environment Variables

```bash
# Set production values in .env
JWT_SECRET_KEY=<strong-random-key>
CORS_ORIGINS=https://yourdomain.com
MONGO_URI=mongodb://mongodb:27017/agentic_volunteer
```

### 2. Enable HTTPS

Use a reverse proxy like Nginx or Traefik with Let's Encrypt SSL certificates.

### 3. Scale Services

```bash
# Scale celery workers
docker-compose up -d --scale celery_worker=3
```

### 4. Set Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 5. Use Docker Secrets

For sensitive data, use Docker secrets instead of environment variables:

```bash
echo "your_secret_key" | docker secret create jwt_secret -
```

### 6. Enable Logging

Configure centralized logging (e.g., ELK stack, Loki).

### 7. Set Up Monitoring

Use Prometheus and Grafana for monitoring:
- Container metrics
- Application metrics
- Database performance

### 8. Configure Auto-restart Policies

Already configured in docker-compose.yml with `restart: unless-stopped`

## 📊 Monitoring and Logs

### Health Check Endpoints

- Backend: http://localhost:8000/health
- MongoDB: `docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"`
- Redis: `docker-compose exec redis redis-cli ping`

### View Container Stats

```bash
# Real-time resource usage
docker stats

# Specific container
docker stats healthcare_backend
```

### Persistent Logs

Logs are stored in Docker and can be viewed with:

```bash
docker-compose logs --since 1h backend > backend_logs.txt
```

## 🛑 Stopping and Cleanup

### Stop All Services

```bash
docker-compose down
```

### Complete Cleanup (Including Data)

```bash
# WARNING: This removes all data
docker-compose down -v
docker system prune -a
```

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this documentation
3. Check GitHub issues
4. Contact the development team

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change JWT_SECRET_KEY to a strong random value
- [ ] Configure CORS_ORIGINS with your actual domain
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Set up firewall rules
- [ ] Regularly update Docker images
- [ ] Enable database authentication
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Review and restrict exposed ports
- [ ] Use Docker secrets for sensitive data

## 📝 Additional Notes

- All data is persisted in Docker volumes
- Default credentials for admin user can be configured in `seed_admin.py`
- CSV data files are in `healthcare_agent/backend/data/`
- Frontend API URLs are configured via environment variables

---

**Last Updated**: November 29, 2025

