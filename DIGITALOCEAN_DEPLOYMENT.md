# DigitalOcean Deployment Guide
## RetailIQ Analytics - Complete Production Setup

This guide will deploy your complete retail analytics system with all detection features on DigitalOcean App Platform.

## 🏗️ Architecture Overview

**Frontend**: Vercel (already deployed) ↔ **Backend**: DigitalOcean App Platform ↔ **Database**: DigitalOcean Managed PostgreSQL

## 📋 Prerequisites

1. DigitalOcean account
2. GitHub repository with your code
3. OpenAI API key
4. Your frontend deployed on Vercel

## 🚀 Step 1: Prepare Your Repository

1. **Push these files to your GitHub repository:**
   - `main_digitalocean.py` - Enhanced backend with PostgreSQL
   - `Dockerfile.digitalocean` - Optimized Docker build
   - `requirements.digitalocean.txt` - Production dependencies
   - `database/postgresql_schema.sql` - Complete database schema
   - `.do/app.yaml` - App Platform configuration

2. **Update your repository structure:**
   ```
   your-repo/
   ├── main_digitalocean.py
   ├── Dockerfile.digitalocean
   ├── requirements.digitalocean.txt
   ├── database/
   │   └── postgresql_schema.sql
   ├── .do/
   │   └── app.yaml
   └── (other existing files)
   ```

## 🗄️ Step 2: Create PostgreSQL Database

1. **Go to DigitalOcean Control Panel**
2. **Create → Databases → PostgreSQL**
3. **Configuration:**
   - Database Engine: PostgreSQL 15
   - Plan: Basic ($15/month minimum for production)
   - Region: Same as your app (e.g., New York)
   - Database Name: `retail-analytics`

4. **Wait for database creation** (5-10 minutes)

5. **Get connection details:**
   - Copy the connection string (DATABASE_URL)
   - Note down: host, port, username, password, database name

## 🛠️ Step 3: Initialize Database Schema

1. **Connect to your database using psql or pgAdmin**
2. **Run the schema file:**
   ```sql
   \i database/postgresql_schema.sql
   ```
   
   Or copy and paste the contents of `database/postgresql_schema.sql`

3. **Verify installation:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```
   
   You should see tables like: users, stores, cameras, visitors, detections, etc.

## 🚀 Step 4: Deploy Backend to App Platform

### Option A: Using DigitalOcean Console (Recommended)

1. **Go to DigitalOcean Control Panel**
2. **Create → Apps**
3. **Choose Source:**
   - GitHub
   - Select your repository
   - Select branch (main/master)

4. **Configure App:**
   - **App Name**: `retail-analytics-backend`
   - **Region**: Same as database
   - **Plan**: Basic ($12/month minimum)

5. **Environment Variables:**
   Click "Environment Variables" and add:
   ```
   DATABASE_URL=your_postgresql_connection_string
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_secure_random_string_here
   CORS_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com
   ENVIRONMENT=production
   ```

6. **Build Settings:**
   - **Dockerfile Path**: `Dockerfile.digitalocean`
   - **Build Command**: (leave empty, handled by Dockerfile)
   - **Run Command**: (leave empty, handled by Dockerfile)

7. **Click "Create Resources"**

### Option B: Using doctl CLI

```bash
# Install doctl and authenticate
doctl apps create .do/app.yaml

# Update environment variables
doctl apps update YOUR_APP_ID --spec .do/app.yaml
```

## 🔧 Step 5: Configure Environment Variables

In your DigitalOcean app settings, set these **required** environment variables:

```bash
# Database (get from your DigitalOcean database)
DATABASE_URL=postgresql://user:password@host:port/database

# OpenAI (get from OpenAI platform)
OPENAI_API_KEY=sk-your-openai-api-key

# Security (generate a secure random string)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here-make-it-long-and-random

# CORS (your frontend URLs)
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com

# Environment
ENVIRONMENT=production
```

### Generate JWT Secret Key:
```python
import secrets
import string

# Generate a secure 64-character secret key
secret = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(64))
print(f"JWT_SECRET_KEY={secret}")
```

## 🌐 Step 6: Update Frontend Configuration

Update your Vercel frontend environment variables:

```bash
# In your Vercel dashboard, set:
REACT_APP_API_URL=https://your-app-name.ondigitalocean.app
NEXT_PUBLIC_API_URL=https://your-app-name.ondigitalocean.app
```

## ✅ Step 7: Verify Deployment

1. **Check app deployment:**
   - Go to your app URL: `https://your-app-name.ondigitalocean.app`
   - Should show: `{"service": "RetailIQ Analytics API", "status": "running"...}`

2. **Check health endpoint:**
   - Visit: `https://your-app-name.ondigitalocean.app/health`
   - Should show: `{"status": "healthy", "database": "healthy"...}`

3. **Check API documentation:**
   - Visit: `https://your-app-name.ondigitalocean.app/docs`
   - Should show FastAPI documentation

4. **Test frontend connection:**
   - Open your Vercel frontend
   - Try signing up or logging in
   - Should successfully connect to your backend

## 🔍 Step 8: Test All Features

### Authentication Test:
1. Sign up with a new account
2. Login with the account
3. Verify JWT tokens are working

### Camera Management Test:
1. Add a new camera with RTSP URL
2. Select appropriate zone type
3. Check if detection starts

### Dashboard Test:
1. View dashboard metrics
2. Check zone-wise analytics
3. Generate AI insights

### Database Test:
Connect to your PostgreSQL database and verify:
```sql
-- Check if data is being stored
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM cameras;
SELECT COUNT(*) FROM visitors WHERE date = CURRENT_DATE;
```

## 📊 Step 9: Monitor and Scale

### Monitoring:
- **App Platform Dashboard**: Monitor CPU, memory, requests
- **Database Dashboard**: Monitor connections, queries, storage
- **Application Logs**: Check for errors and performance issues

### Scaling:
- **Vertical Scaling**: Upgrade app plan for more CPU/memory
- **Database Scaling**: Upgrade database plan for more storage/connections
- **Horizontal Scaling**: Add more app instances (Professional plan)

## 🚨 Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check Dockerfile path is correct
   - Verify all files are in repository
   - Check build logs for specific errors

2. **Database Connection Error:**
   - Verify DATABASE_URL is correct
   - Check database is running and accessible
   - Confirm database allows connections from your app

3. **OpenCV/YOLO Issues:**
   - Check app logs for library loading errors
   - Increase app memory if needed
   - Verify YOLO model downloads correctly

4. **CORS Errors:**
   - Update CORS_ORIGINS with correct frontend URL
   - Include both www and non-www versions
   - Check protocol (http vs https)

### Useful Commands:

```bash
# View app logs
doctl apps logs YOUR_APP_ID

# Check app info
doctl apps get YOUR_APP_ID

# Update app
doctl apps update YOUR_APP_ID --spec .do/app.yaml

# Database connection test
psql $DATABASE_URL -c "SELECT version();"
```

## 💰 Cost Estimation

**Monthly Costs:**
- App Platform Basic: $12/month
- PostgreSQL Basic: $15/month
- **Total: ~$27/month**

**For production scale:**
- App Platform Professional: $25/month
- PostgreSQL Standard: $50/month
- **Total: ~$75/month**

## 🔐 Security Best Practices

1. **Environment Variables:** Never commit sensitive data to repository
2. **Database Access:** Use connection pooling and prepared statements
3. **API Security:** Implement rate limiting and input validation
4. **HTTPS Only:** Ensure all communication is encrypted
5. **Regular Updates:** Keep dependencies updated

## 📈 Performance Optimization

1. **Database Indexing:** Already included in schema
2. **Connection Pooling:** Implemented in backend
3. **Caching:** Consider Redis for session caching
4. **CDN:** Use DigitalOcean Spaces for static assets
5. **Monitoring:** Set up alerts for high CPU/memory usage

## 🎯 Next Steps

1. **Custom Domain**: Add your custom domain to both frontend and backend
2. **SSL Certificate**: Enable automatic HTTPS certificates
3. **Monitoring**: Set up uptime monitoring and alerts
4. **Backup Strategy**: Configure automated database backups
5. **CI/CD Pipeline**: Set up automated deployments from GitHub

## 📞 Support

- **DigitalOcean Community**: [community.digitalocean.com](https://community.digitalocean.com)
- **Documentation**: [docs.digitalocean.com](https://docs.digitalocean.com)
- **Support Tickets**: Available with paid plans

---

## 🎉 Congratulations!

Your complete retail analytics system is now deployed with:
- ✅ Full computer vision capabilities
- ✅ Real-time RTSP camera processing
- ✅ Advanced detection features
- ✅ PostgreSQL database with comprehensive analytics
- ✅ AI insights powered by OpenAI
- ✅ Production-ready security and performance
- ✅ Scalable architecture

Your system now supports all the features you requested:
- Home page, signup/login with database
- Dashboard with camera management
- Real-time detection with zone analytics
- Live visitor counts and dwell time analysis
- Queue monitoring and product interaction tracking  
- Combined store metrics and AI insights
- Promotional effectiveness analysis
- Festival spike detection

The system is ready for production use by store managers!