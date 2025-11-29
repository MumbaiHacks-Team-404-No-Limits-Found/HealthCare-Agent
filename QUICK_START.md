# 🚀 Healthcare Agent - Quick Start Guide

Get your Healthcare Agent application running with Docker in under 5 minutes!

---

## ⚡ Super Quick Start (Copy & Paste)

```bash
# 1. Navigate to project directory
cd /Users/dokuparthinilesh/Desktop/hacke

# 2. Create environment file
cp env.template .env

# 3. Generate and set JWT secret (automatic)
python3 -c "import secrets; key=secrets.token_urlsafe(32); print(key); 
import fileinput; 
[print(line.replace('your-super-secret-jwt-key-change-this-in-production', key), end='') 
for line in fileinput.input('.env', inplace=True)]"

# 4. Build and start everything
docker-compose up -d --build

# 5. Wait for services to initialize
echo "Waiting 30 seconds for services to start..."
sleep 30

# 6. Create admin user
docker-compose exec backend python seed_admin.py

# 7. Done! Open your browser
echo "✅ Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000/docs"
```

---

## 📋 Step-by-Step Instructions

### Step 1: Navigate to Project
```bash
cd /Users/dokuparthinilesh/Desktop/hacke
```

### Step 2: Create Environment File
```bash
cp env.template .env
```

### Step 3: Generate JWT Secret
```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output and edit .env file
nano .env
# Set JWT_SECRET_KEY=<your-generated-key>
```

### Step 4: Build Docker Images
```bash
docker-compose build
```
⏱️ This takes 5-10 minutes on first run

### Step 5: Start All Services
```bash
docker-compose up -d
```

### Step 6: Check Status
```bash
docker-compose ps
```
All services should show "Up" status

### Step 7: Initialize Database
```bash
# Create admin user
docker-compose exec backend python seed_admin.py

# Optional: Seed sample data
docker-compose exec backend python seed_from_csv.py
```

### Step 8: Access Application
Open your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **GraphQL**: http://localhost:8000/graphql

---

## 🎯 Using the Deploy Script (Alternative)

Make the script executable and run it:

```bash
chmod +x deploy.sh
./deploy.sh
```

Follow the interactive menu!

---

## 🔧 Essential Commands

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Restart After Code Changes
```bash
docker-compose restart backend frontend
```

### Complete Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

---

## ✅ Verify Deployment

Check each service is working:

```bash
# 1. Check all containers are running
docker-compose ps

# 2. Test backend health
curl http://localhost:8000/health

# 3. Check MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# 4. Check Redis
docker-compose exec redis redis-cli ping

# 5. View logs (should show no errors)
docker-compose logs --tail=20
```

---

## 🐛 Quick Troubleshooting

### Problem: Port already in use
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Problem: Build fails
```bash
# Clean build
docker-compose build --no-cache
```

### Problem: Services won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs mongodb

# Restart
docker-compose restart
```

---

## 📚 Need More Help?

- **Detailed Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **All Commands**: [DOCKER_COMMANDS.md](./DOCKER_COMMANDS.md)
- **Full Documentation**: [README_DOCKER.md](./README_DOCKER.md)

---

## 🎉 You're Done!

Your Healthcare Agent is now running:

```
✅ MongoDB running on port 27017
✅ Redis running on port 6379
✅ Backend API running on port 8000
✅ Frontend running on port 3000
✅ Celery workers processing tasks
✅ Celery beat scheduling tasks
```

**Login to the frontend at http://localhost:3000**

Default admin credentials can be found in `seed_admin.py`

---

**Questions?** Check the comprehensive [DEPLOYMENT.md](./DEPLOYMENT.md) guide!

