# Complete Setup Guide - RetailIQ Analytics
## Step-by-Step DigitalOcean Deployment

## 🗄️ Step 1: Create and Configure PostgreSQL Database

### Create Database in DigitalOcean:
1. **Go to DigitalOcean Control Panel**
2. **Create → Databases → PostgreSQL**
3. **Configuration:**
   - Engine: PostgreSQL 15
   - Plan: Basic ($15/month)
   - Region: Bangalore 1 (blr1) - matches your current setup
   - Database Name: **`retail_analytics`** (not defaultdb)

### Your Current Connection Details:
```
Host: db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com
Port: 25061
Username: doadmin
Password: [YOUR_DATABASE_PASSWORD_HERE]
```

### Correct Database URLs to Try:

**Option 1: Using retail_analytics database (create this):**
```
DATABASE_URL=postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/retail_analytics?sslmode=require
```

**Option 2: Check what databases exist first:**
Go to your DigitalOcean database dashboard and see what databases are listed.

## 🧪 Step 2: Test Database Connection

### Method 1: Using our script
```bash
export DATABASE_URL='postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/retail_analytics?sslmode=require'
python test_connection.py
```

### Method 2: Direct connection test
```bash
pip install psycopg2-binary
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com',
        port=25061,
        user='doadmin',
        password='[YOUR_PASSWORD]',
        database='retail_analytics',  # or try 'postgres', 'doadmin'
        sslmode='require'
    )
    print('✅ Connection successful!')
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    print('PostgreSQL version:', cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print('❌ Connection failed:', e)
"
```

## 🛠️ Step 3: Create Database (if needed)

If the `retail_analytics` database doesn't exist, create it:

### Method 1: Using DigitalOcean Console
1. Go to your database in DigitalOcean dashboard
2. Click on "Users & Databases" tab
3. Click "Create Database"
4. Name: `retail_analytics`
5. Click "Save"

### Method 2: Using psql command line
```bash
psql "postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/postgres?sslmode=require" -c "CREATE DATABASE retail_analytics;"
```

## 📊 Step 4: Initialize Database Schema

Once connected successfully:

```bash
# Set the correct DATABASE_URL
export DATABASE_URL='postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/retail_analytics?sslmode=require'

# Install dependencies
pip install sqlalchemy psycopg2-binary

# Test connection
python test_connection.py

# Create all tables
python create_tables.py
```

## 🚀 Step 5: Deploy to DigitalOcean App Platform

### Update Environment Variables:
```bash
DATABASE_URL=postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/retail_analytics?sslmode=require

JWT_SECRET_KEY=3ngfxh){,96P$byppEE;gd!tr2|V_/.qR6:WWt[|S{Tx]*sv;i-*cY&[,*w#cT@g

OPENAI_API_KEY=your-openai-api-key-here

CORS_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com

ENVIRONMENT=production
```

### Deploy Steps:
1. **Go to DigitalOcean App Platform**
2. **Create New App**
3. **Connect to GitHub: mj-112358/retail-analytics-final**
4. **Set Environment Variables** (above)
5. **Deploy**

## 🔍 Step 6: Verify Everything Works

### Test Endpoints:
1. **Health Check:** `https://your-app.ondigitalocean.app/health`
2. **API Root:** `https://your-app.ondigitalocean.app/`
3. **System Status:** `https://your-app.ondigitalocean.app/api/system/status`

### Test Features:
1. **Signup:** POST `/api/auth/signup`
2. **Login:** POST `/api/auth/login`
3. **Add Camera:** POST `/cameras`
4. **Dashboard:** GET `/api/dashboard/metrics`
5. **AI Insights:** POST `/api/dashboard/insights`

## 🚨 Troubleshooting

### Common Database Issues:

1. **"No such database" error:**
   - Database doesn't exist, create it in DigitalOcean dashboard
   - Or try connecting to 'postgres' database first

2. **Connection timeout:**
   - Check firewall settings
   - Verify SSL mode is required

3. **Permission denied:**
   - Double-check username/password
   - Ensure user has database creation privileges

### Test Different Database Names:
```bash
# Try these database names:
retail_analytics
postgres  
doadmin
defaultdb
```

### Get Database List:
```bash
psql "postgresql://doadmin:[YOUR_PASSWORD]@db-postgresql-blr1-04807-do-user-24956774-0.l.db.ondigitalocean.com:25061/postgres?sslmode=require" -c "\l"
```

## ✅ Success Indicators

### Database Setup Complete:
- ✅ Connection test passes
- ✅ All 15 tables created
- ✅ Zone types initialized (12 default zones)
- ✅ Foreign keys and indexes working

### App Deployment Complete:
- ✅ Health endpoint returns "healthy"
- ✅ System status shows all features enabled
- ✅ Frontend can connect and authenticate
- ✅ Camera management working
- ✅ Analytics data being stored

## 🎯 Next Steps After Successful Setup:

1. **Test with Real RTSP Camera:** Add actual camera feeds
2. **Configure OpenAI:** Add your OpenAI API key for insights
3. **Test Analytics:** Verify visitor tracking and metrics
4. **Scale Resources:** Upgrade app/database plans if needed
5. **Monitor Performance:** Set up alerts and monitoring

---

**Your system includes ALL requested features:**
- ✅ Authentication system ready for production
- ✅ Camera management with zone types
- ✅ Real-time RTSP processing with YOLO
- ✅ Zone-wise visitor analytics
- ✅ Product interaction tracking
- ✅ Queue monitoring system
- ✅ AI insights with promotional analysis
- ✅ Festival spike detection
- ✅ Comprehensive dashboard metrics