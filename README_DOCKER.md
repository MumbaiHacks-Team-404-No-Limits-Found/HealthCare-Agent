# Healthcare Agent - Docker Deployment

Complete Docker setup for the Healthcare Agent application with backend (FastAPI), frontend (Next.js), MongoDB, Redis, and Celery workers.

## 📁 Project Structure

```
hacke/
├── healthcare_agent/
│   └── backend/
│       ├── Dockerfile              # Backend Docker image
│       ├── .dockerignore           # Backend ignore patterns
│       ├── requirements.txt        # Python dependencies
│       └── app/                    # FastAPI application
├── frontend/
│   ├── Dockerfile                  # Frontend Docker image (multi-stage)
│   ├── .dockerignore               # Frontend ignore patterns
│   └── package.json                # Node.js dependencies
├── docker-compose.yml              # Main orchestration file
├── docker-compose.prod.yml         # Production overrides
├── nginx/
│   └── nginx.conf                  # Reverse proxy configuration
├── env.template                    # Environment variables template
├── deploy.sh                       # Interactive deployment script
├── DEPLOYMENT.md                   # Comprehensive deployment guide
└── DOCKER_COMMANDS.md              # Quick command reference
```

## 🚀 Quick Start

### Option 1: Using the Deploy Script (Recommended)

```bash
./deploy.sh
```

Follow the interactive prompts to:
1. Create environment configuration
2. Build Docker images
3. Start all services
4. Initialize the database

### Option 2: Manual Deployment

```bash
# 1. Create environment file
cp env.template .env
nano .env  # Edit and set JWT_SECRET_KEY

# 2. Build and start services
docker-compose up -d --build

# 3. Wait for services to start (30 seconds)
sleep 30

# 4. Initialize database
docker-compose exec backend python seed_admin.py

# 5. (Optional) Seed sample data
docker-compose exec backend python seed_from_csv.py
```

## 🌐 Access URLs

After deployment, access the application at:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Web application UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI documentation |
| **GraphQL** | http://localhost:8000/graphql | GraphQL playground |
| **MongoDB** | localhost:27017 | Database (internal) |
| **Redis** | localhost:6379 | Cache/queue (internal) |

## 🔑 Environment Variables

Key environment variables to configure in `.env`:

### Required
- `JWT_SECRET_KEY` - Secret key for JWT tokens (generate with: `openssl rand -base64 32`)

### Optional
- `TWILIO_ACCOUNT_SID` - Twilio account SID for SMS/WhatsApp
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `TWILIO_WHATSAPP_FROM` - WhatsApp sender number
- `NOTIFICATIONAPI_CLIENT_ID` - NotificationAPI client ID
- `NOTIFICATIONAPI_CLIENT_SECRET` - NotificationAPI secret

See `env.template` for complete list.

## 📦 Services

The Docker Compose setup includes:

### 1. MongoDB (mongo:7.0)
- **Purpose**: Primary database
- **Port**: 27017
- **Volume**: `mongodb_data`
- **Health Check**: Built-in ping command

### 2. Redis (redis:7-alpine)
- **Purpose**: Cache and Celery message broker
- **Port**: 6379
- **Volume**: `redis_data`
- **Persistence**: AOF enabled

### 3. Backend (FastAPI)
- **Purpose**: REST API and GraphQL endpoint
- **Port**: 8000
- **Features**: JWT auth, CORS, rate limiting
- **Health Check**: `/health` endpoint

### 4. Celery Worker
- **Purpose**: Background task processing
- **Tasks**: Notifications, forecasting, planning
- **Scaling**: Can be scaled with `--scale celery_worker=N`

### 5. Celery Beat
- **Purpose**: Periodic task scheduler
- **Tasks**: Scheduled forecasts, reminders

### 6. Frontend (Next.js)
- **Purpose**: Web application UI
- **Port**: 3000
- **Build**: Optimized production build

## 📋 Common Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

### Database Operations
```bash
# Create admin user
docker-compose exec backend python seed_admin.py

# Seed CSV data
docker-compose exec backend python seed_from_csv.py

# MongoDB shell
docker-compose exec mongodb mongosh agentic_volunteer

# Backup database
docker-compose exec mongodb mongodump --out /data/backup
```

### Debugging
```bash
# Backend shell
docker-compose exec backend bash

# View environment variables
docker-compose exec backend env

# Test API
curl http://localhost:8000/health

# Check Redis
docker-compose exec redis redis-cli ping
```

See [DOCKER_COMMANDS.md](./DOCKER_COMMANDS.md) for complete command reference.

## 🏭 Production Deployment

For production, use the production override:

```bash
# Set production environment variables
cp env.template .env
# Edit .env with production values

# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Production features:
- ✅ Resource limits and reservations
- ✅ Service replication
- ✅ MongoDB authentication
- ✅ Redis password protection
- ✅ Nginx reverse proxy
- ✅ Rate limiting
- ✅ SSL/TLS ready
- ✅ Always restart policy

### Production Checklist

- [ ] Generate strong JWT_SECRET_KEY
- [ ] Set up MongoDB authentication
- [ ] Configure Redis password
- [ ] Set CORS_ORIGINS to your domain
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure automated backups
- [ ] Review and restrict exposed ports
- [ ] Set up firewall rules
- [ ] Configure log aggregation

## 🔧 Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache

# Check disk space
docker system df
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database Connection Failed
```bash
# Check MongoDB status
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb

# Check logs
docker-compose logs mongodb
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed troubleshooting.

## 📊 Monitoring

### Health Checks
```bash
# Check all services
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Check MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check Redis
docker-compose exec redis redis-cli ping
```

### Resource Usage
```bash
# View resource consumption
docker stats

# View specific container
docker stats healthcare_backend
```

### Logs
```bash
# Follow all logs
docker-compose logs -f

# Last 100 lines of backend
docker-compose logs --tail=100 backend

# Logs since 1 hour ago
docker-compose logs --since 1h
```

## 💾 Backup and Restore

### Backup
```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup
docker cp healthcare_mongodb:/data/backup ./mongodb_backup

# Backup volumes
docker run --rm \
  -v hacke_mongodb_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/mongodb.tar.gz /data
```

### Restore
```bash
# Restore MongoDB
docker cp ./mongodb_backup healthcare_mongodb:/data/backup
docker-compose exec mongodb mongorestore /data/backup
```

## 🔄 Updates

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Update Dependencies
```bash
# Backend dependencies
# Edit requirements.txt then:
docker-compose build backend
docker-compose up -d --no-deps backend

# Frontend dependencies
# Edit package.json then:
docker-compose build frontend
docker-compose up -d --no-deps frontend
```

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide
- **[DOCKER_COMMANDS.md](./DOCKER_COMMANDS.md)** - Quick command reference
- **[env.template](./env.template)** - Environment variables reference

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review documentation: `DEPLOYMENT.md`
3. Try rebuilding: `docker-compose build --no-cache`
4. Check disk space: `docker system df`
5. Verify environment: `docker-compose config`

## 📝 Notes

- All data is persisted in Docker volumes
- CSV seed data is in `healthcare_agent/backend/data/`
- Frontend connects to backend via environment variables
- Default admin credentials set in `seed_admin.py`
- Celery workers can be scaled horizontally
- MongoDB and Redis are not exposed in production

---

**Created**: November 29, 2025  
**Last Updated**: November 29, 2025

For questions or issues, refer to the comprehensive documentation in `DEPLOYMENT.md`.

