# Environment Variables Setup Guide
## Required Configuration for DigitalOcean Deployment

## 🔑 **Your Generated JWT Secret Key:**
```
JWT_SECRET_KEY=3ngfxh){,96P$byppEE;gd!tr2|V_/.qR6:WWt[|S{Tx]*sv;i-*cY&[,*w#cT@g
```
**⚠️ IMPORTANT: Keep this secret key secure and never commit it to your repository!**

## 🌐 **DigitalOcean App Platform Environment Variables**

In your DigitalOcean App Platform dashboard, set these environment variables:

### **Required Variables:**

```bash
# Database Connection (get from your DigitalOcean PostgreSQL database)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Authentication (use the generated key above)
JWT_SECRET_KEY=3ngfxh){,96P$byppEE;gd!tr2|V_/.qR6:WWt[|S{Tx]*sv;i-*cY&[,*w#cT@g

# OpenAI Integration (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-openai-api-key-here

# CORS Origins (replace with your actual Vercel frontend URL)
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com

# Environment
ENVIRONMENT=production
```

### **Optional Variables:**
```bash
# Logging
LOG_LEVEL=INFO

# Performance
MAX_WORKERS=1
```

## 🔧 **Port Configuration - FIXED ✅**

Your deployment is correctly configured for **port 8080**:
- ✅ DigitalOcean deployment settings: **8080**  
- ✅ Dockerfile: **PORT=${PORT:-8080}**
- ✅ App.yaml: **http_port: 8080**
- ✅ Python code: **--port ${PORT:-8080}**

**All port configurations are now consistent!**

## 🎯 **How to Set Environment Variables in DigitalOcean:**

### **Method 1: Via Dashboard (Recommended)**
1. Go to your DigitalOcean App Platform dashboard
2. Select your app
3. Go to **Settings** → **Environment**
4. Click **Edit** next to your service
5. Add each variable:
   - **Key**: `JWT_SECRET_KEY`  
   - **Value**: `3ngfxh){,96P$byppEE;gd!tr2|V_/.qR6:WWt[|S{Tx]*sv;i-*cY&[,*w#cT@g`
   - **Scope**: `Run Time`
   - **Type**: `Secret` (for sensitive data)

6. Repeat for all variables above
7. Click **Save**

### **Method 2: Via App Spec (app.yaml)**
Your `.do/app.yaml` already has placeholders. Replace with actual values:

```yaml
envs:
- key: DATABASE_URL
  scope: RUN_AND_BUILD_TIME
  value: ${db.DATABASE_URL}
- key: OPENAI_API_KEY
  scope: RUN_TIME
  type: SECRET
  value: sk-your-actual-openai-key
- key: JWT_SECRET_KEY
  scope: RUN_TIME  
  type: SECRET
  value: 3ngfxh){,96P$byppEE;gd!tr2|V_/.qR6:WWt[|S{Tx]*sv;i-*cY&[,*w#cT@g
```

## 🔐 **Security Best Practices:**

1. **Never commit sensitive keys** to your repository
2. **Use "Secret" type** for sensitive environment variables in DigitalOcean
3. **Rotate keys periodically** for better security
4. **Use different keys** for development vs production

## 🧪 **Testing Your Configuration:**

After deployment, test these endpoints:

1. **Health Check:**
   ```
   GET https://your-app.ondigitalocean.app/health
   ```
   Should return: `{"status": "healthy", "database": "healthy"}`

2. **API Root:**
   ```
   GET https://your-app.ondigitalocean.app/
   ```
   Should return app info with version 3.0.0

3. **Authentication Test:**
   ```
   POST https://your-app.ondigitalocean.app/api/auth/signup
   ```
   Should work with proper JWT token generation

## 🚨 **Troubleshooting:**

### **JWT Token Issues:**
- Error: `Invalid token` → Check JWT_SECRET_KEY is set correctly
- Error: `Token expired` → Normal behavior, frontend should handle refresh

### **Database Connection Issues:**
- Error: `Database connection failed` → Check DATABASE_URL format
- Error: `Permission denied` → Verify database allows connections from your app

### **OpenAI Issues:**
- Warning: `OpenAI API key not set` → Set OPENAI_API_KEY environment variable
- Error: `API key invalid` → Verify key is correct and has billing enabled

### **Port Issues:**
- Error: `Port already in use` → DigitalOcean handles this automatically
- Error: `Connection refused` → Check health endpoint first

## 🎉 **Ready for Production!**

With these environment variables configured, your retail analytics system will have:
- ✅ Secure JWT authentication
- ✅ PostgreSQL database connectivity  
- ✅ OpenAI AI insights integration
- ✅ Proper CORS configuration
- ✅ Production-ready security
- ✅ All detection features working

Your port configuration is now consistent at **8080** across all components!