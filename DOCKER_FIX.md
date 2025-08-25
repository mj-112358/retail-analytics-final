# 🔧 DOCKER PORT FIX GUIDE

## ❌ ISSUE IDENTIFIED
From your Docker Desktop screenshots, I can see:
- `trusting_bardeen` (backend) running on **8080:8080** ❌ 
- `determined_maxwell` (frontend) running on **3000:80** ✅

**The backend port mapping is WRONG!**

## ✅ CORRECT CONFIGURATION

### Backend should be:
- **Host Port**: 3000 
- **Container Port**: 3000
- **Port Mapping**: `3000:3000` ✅

### Frontend should be:
- **Host Port**: 5173 (or 3001)
- **Container Port**: 80 (nginx)  
- **Port Mapping**: `5173:80` ✅

## 🔧 HOW TO FIX

### Option 1: Stop and Restart Containers with Correct Ports

```bash
# Stop the existing backend container
docker stop trusting_bardeen
docker rm trusting_bardeen

# Run backend with CORRECT port mapping
docker run -d \
  --name retail-analytics-backend \
  -p 3000:3000 \
  -e PORT=3000 \
  -e OPENAI_API_KEY=your-key-here \
  -e JWT_SECRET_KEY=your-jwt-key-here \
  retail-analytics-backend
```

### Option 2: Use Docker Compose (RECOMMENDED)

```bash
# Copy .env.example to .env and add your keys
cp .env.example .env
# Edit .env with your actual API keys

# Run with Docker Compose
docker-compose up -d

# This will create:
# - Backend on localhost:3000 ✅
# - Frontend on localhost:5173 ✅
```

## 🌐 CORRECT ACCESS URLS

After fixing:
- **Backend API**: http://localhost:3000
- **Frontend**: http://localhost:5173
- **Health Check**: http://localhost:3000/health
- **API Docs**: http://localhost:3000/docs

## 🚨 WHY THIS MATTERS

1. **Frontend expects backend on port 3000** - hardcoded in api.ts
2. **Railway deployment uses port 3000** - configured in railway.toml  
3. **Health checks expect port 3000** - required for Railway deployment

Your current 8080:8080 mapping will cause:
- ❌ Frontend can't connect to backend
- ❌ Railway health checks will fail
- ❌ API calls return connection errors

## ✅ NEXT STEPS

1. **Stop current backend container** (trusting_bardeen)
2. **Use Docker Compose** with the provided configuration
3. **Test**: Visit http://localhost:3000/health - should return healthy status
4. **Deploy to Railway** - now it will work correctly!

The fix is ready - just restart your containers with the correct port mapping! 🚀