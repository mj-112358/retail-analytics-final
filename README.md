# 🏪 RetailIQ Analytics - Complete Production System

## Complete retail analytics platform with real-time RTSP camera processing and AI insights

### ✅ Features Included:
- **Real-time RTSP camera processing** with YOLOv8 person detection
- **Complete authentication system** with JWT tokens
- **All analytics metrics**: visitor counts, dwell time, queue monitoring, footfall analysis
- **AI-powered insights** with OpenAI integration for business recommendations
- **Promotion effectiveness analysis** with 0-100 scoring
- **Festival spike detection** and seasonal analysis
- **Multi-zone tracking** with camera management dashboard

---

## 🚀 Railway Deployment

### 1. Create Railway Service
1. Go to [railway.app](https://railway.app)
2. Create new project → Deploy from GitHub
3. Select your repository: `mj-112358/retail-analytics-final`

### 2. Configure Service
- **Root Directory**: `/` (main folder)  
- **Dockerfile**: `Dockerfile.final.production`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port ${PORT}`
- **Health Check Path**: `/health`

### 3. Environment Variables
Add these in Railway Dashboard → Variables:

```bash
# Server (REQUIRED - Railway injects PORT automatically, but you can set it)
PORT=3000
ENVIRONMENT=production

# Database (Replace with your PostgreSQL URL)
DATABASE_URL=postgresql://postgres.gncefqvuczdrpvvgcbhz:dR7TT4I@$nrQg2C@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# Authentication (Generate new secure keys)
JWT_SECRET_KEY=your-ultra-secure-jwt-secret-key-256-bits
JWT_ACCESS_TOKEN_EXPIRES=24
REFRESH_SECRET_KEY=your-ultra-secure-refresh-secret-different-from-jwt

# OpenAI Integration
OPENAI_API_KEY=sk-proj-your-openai-api-key

# Supabase (Replace with your values)
SUPABASE_URL=https://gncefqvuczdrpvvgcbhz.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# CORS (Replace with your Vercel URL)
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

### 4. After Deployment
Your Railway backend will be available at:
`https://YOUR-RAILWAY-PROJECT.railway.app`

Test endpoints:
- Health: `https://YOUR-RAILWAY-PROJECT.railway.app/health`
- API Docs: `https://YOUR-RAILWAY-PROJECT.railway.app/docs`

---

## 🌐 Frontend Configuration (Vercel)

Update your Vercel environment variable:

```bash
VITE_API_URL=https://YOUR-RAILWAY-PROJECT.railway.app
```

---

## 💼 For Store Owners

### Complete Workflow:
1. **Sign Up** → Create account with store details
2. **Add Cameras** → Input RTSP URL + zone names ("Floor 1 - Dairy Section")
3. **Real-time Analytics** → View live visitor counts, dwell times, queues
4. **AI Insights** → Generate business insights with OpenAI
5. **Promo Analysis** → Analyze promotion effectiveness (0-100 score)
6. **Festival Analysis** → Track seasonal shopping patterns

---

## 🏗️ System Architecture

### Core Files:
- `main.py` - Main FastAPI application
- `auth_final.py` - Authentication system
- `analytics_engine_final.py` - Analytics calculations
- `openai_insights_final.py` - AI insights generation
- `rtsp_camera_system_final.py` - Camera processing
- `database/schema_final.sql` - Database schema

### Production Ready:
- ✅ No mock data
- ✅ Real database integration
- ✅ Secure authentication
- ✅ Real-time RTSP processing
- ✅ AI-powered insights
- ✅ Complete analytics metrics

---

## 🔧 Development

### Local Development:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy from .env.example)
export DATABASE_URL="your-db-url"
export OPENAI_API_KEY="your-key"

# Run application
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

### Frontend Development:
```bash
cd "project 5"
npm install
npm run dev
```

---

**Ready for real customers!** 🎯