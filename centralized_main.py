"""
Centralized Retail Analytics Main Application
Multi-tenant system supporting multiple client stores with centralized YOLO processing
"""
import os
import logging
import asyncio
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiosqlite
import bcrypt
import jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "centralized_retail_analytics.db"

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"

# MediaMTX settings
MEDIA_SERVER_IP = os.getenv("MEDIA_SERVER_IP", "localhost")
MEDIA_SERVER_PORT = int(os.getenv("MEDIA_SERVER_PORT", "8554"))

# Import centralized processor
try:
    from centralized_rtsp_processor import (
        start_centralized_processor, 
        stop_centralized_processor,
        get_all_processors_status,
        get_all_analytics_summary
    )
    CENTRALIZED_PROCESSOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Centralized processor not available: {e}")
    CENTRALIZED_PROCESSOR_AVAILABLE = False

# FastAPI app
app = FastAPI(
    title="Centralized Retail Analytics API",
    description="Multi-tenant retail analytics with centralized YOLO processing",
    version="2.0.0"
)

# CORS Configuration for centralized system
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.railway.app",
        "*"  # Allow all origins for multi-tenant access
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class OrganizationCreate(BaseModel):
    name: str
    subscription_plan: str = "basic"

class StoreCreate(BaseModel):
    store_identifier: str
    name: str
    location: Optional[str] = None
    timezone: str = "UTC"

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "manager"

class CameraCreate(BaseModel):
    camera_identifier: int
    name: str
    zone_type: str
    location_description: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

# Database initialization
async def init_centralized_database():
    """Initialize the centralized database"""
    try:
        # Check if schema file exists
        if not os.path.exists("database/centralized_schema.sql"):
            logger.warning("Schema file not found, creating basic tables...")
            return
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Read and execute schema
            with open("database/centralized_schema.sql", 'r') as f:
                schema_sql = f.read()
            
            # Execute schema (split by semicolon for multiple statements)
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    await db.execute(statement)
            
            await db.commit()
            logger.info("✅ Centralized database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

@app.on_event("startup")
async def startup_event():
    await init_centralized_database()
    logger.info("🚀 Centralized RetailIQ Analytics - Production Ready")

# Authentication utilities
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request):
    """Get current authenticated user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT u.*, o.name as organization_name 
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = ?
        """, (payload.get("email"),))
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return dict(user)

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "Centralized RetailIQ Analytics API", 
        "status": "running",
        "version": "2.0.0",
        "features": ["multi-tenant", "centralized-processing", "real-time-analytics"],
        "docs": "/docs"
    }

@app.post("/api/organizations")
async def create_organization(org: OrganizationCreate):
    """Create a new organization"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Generate API key
        api_key = f"retail_{''.join([c for c in org.name.lower() if c.isalnum()])}_{''.join(str(datetime.now().timestamp()).split('.'))}"
        
        cursor = await db.execute("""
            INSERT INTO organizations (name, subscription_plan, api_key)
            VALUES (?, ?, ?)
        """, (org.name, org.subscription_plan, api_key))
        
        org_id = cursor.lastrowid
        await db.commit()
        
        return {
            "organization_id": org_id,
            "api_key": api_key,
            "message": "Organization created successfully"
        }

@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    """Sign up a new user"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if user exists
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Get default organization (for demo)
        cursor = await db.execute("SELECT id FROM organizations LIMIT 1")
        org = await cursor.fetchone()
        if not org:
            raise HTTPException(status_code=400, detail="No organization available")
        
        # Hash password and create user
        password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor = await db.execute("""
            INSERT INTO users (organization_id, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, (org[0], user.email, password_hash, user.full_name, user.role))
        
        user_id = cursor.lastrowid
        await db.commit()
        
        # Create access token
        token_data = {"user_id": user_id, "email": user.email, "org_id": org[0]}
        access_token = create_access_token(token_data)
        
        return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login user"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, password_hash, organization_id FROM users WHERE email = ?
        """, (credentials.email,))
        user = await cursor.fetchone()
        
        if not user or not bcrypt.checkpw(credentials.password.encode('utf-8'), user[1].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        await db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (datetime.now(), user[0]))
        await db.commit()
        
        # Create access token
        token_data = {"user_id": user[0], "email": credentials.email, "org_id": user[2]}
        access_token = create_access_token(token_data)
        
        return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "organization": current_user["organization_name"]
    }

@app.get("/api/stores")
async def get_stores(current_user: dict = Depends(get_current_user)):
    """Get stores for current organization"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM stores WHERE organization_id = ? ORDER BY name
        """, (current_user["organization_id"],))
        stores = await cursor.fetchall()
        
        return [dict(store) for store in stores]

@app.post("/api/stores")
async def create_store(store: StoreCreate, current_user: dict = Depends(get_current_user)):
    """Create a new store"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO stores (organization_id, store_identifier, name, location, timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (current_user["organization_id"], store.store_identifier, store.name, store.location, store.timezone))
        
        store_id = cursor.lastrowid
        await db.commit()
        
        return {
            "store_id": store_id,
            "message": "Store created successfully"
        }

@app.get("/api/cameras")
async def get_cameras(current_user: dict = Depends(get_current_user)):
    """Get all cameras for user's organization"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT c.*, s.store_identifier, s.name as store_name
            FROM cameras c
            JOIN stores s ON c.store_id = s.id
            WHERE s.organization_id = ?
            ORDER BY s.store_identifier, c.camera_identifier
        """, (current_user["organization_id"],))
        cameras = await cursor.fetchall()
        
        result = []
        for camera in cameras:
            camera_dict = dict(camera)
            camera_dict["publish_url"] = f"rtsp://{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}/{camera['media_server_path']}"
            result.append(camera_dict)
        
        return result

@app.post("/api/cameras")
async def create_camera(camera: CameraCreate, store_id: int, current_user: dict = Depends(get_current_user)):
    """Create a new camera for centralized processing"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Verify store belongs to organization
        cursor = await db.execute("""
            SELECT store_identifier FROM stores WHERE id = ? AND organization_id = ?
        """, (store_id, current_user["organization_id"]))
        store = await cursor.fetchone()
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Create media server path
        media_server_path = f"store_{store[0]}_camera_{camera.camera_identifier}"
        
        # Insert camera
        cursor = await db.execute("""
            INSERT INTO cameras (store_id, camera_identifier, name, zone_type, location_description, 
                               media_server_path, media_server_ip, media_server_port, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'waiting_for_stream')
        """, (store_id, camera.camera_identifier, camera.name, camera.zone_type, 
              camera.location_description, media_server_path, MEDIA_SERVER_IP, MEDIA_SERVER_PORT))
        
        camera_id = cursor.lastrowid
        await db.commit()
        
        # Start centralized processor
        if CENTRALIZED_PROCESSOR_AVAILABLE:
            try:
                processor = start_centralized_processor(
                    store[0], camera.camera_identifier, camera.zone_type, MEDIA_SERVER_IP
                )
                logger.info(f"✅ Started centralized processor for store {store[0]} camera {camera.camera_identifier}")
                
                # Update status
                await db.execute("UPDATE cameras SET status = 'active' WHERE id = ?", (camera_id,))
                await db.commit()
                
            except Exception as e:
                logger.error(f"❌ Failed to start processor: {e}")
        
        publish_url = f"rtsp://{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}/{media_server_path}"
        
        return {
            "camera_id": camera_id,
            "media_server_path": media_server_path,
            "publish_url": publish_url,
            "message": f"Camera created. Client should publish to: {publish_url}"
        }

@app.get("/api/analytics/live")
async def get_live_analytics(current_user: dict = Depends(get_current_user)):
    """Get live analytics from all processors"""
    if not CENTRALIZED_PROCESSOR_AVAILABLE:
        return {"processors": [], "summary": "Centralized processing not available"}
    
    processors_status = get_all_processors_status()
    analytics_summary = get_all_analytics_summary()
    
    return {
        "processors": processors_status,
        "analytics_summary": analytics_summary,
        "total_active_cameras": len([p for p in processors_status.values() if p.get("is_running")])
    }

@app.get("/api/client-instructions/{store_identifier}")
async def generate_client_instructions(store_identifier: str, current_user: dict = Depends(get_current_user)):
    """Generate setup instructions for a client store"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get store info
        cursor = await db.execute("""
            SELECT s.*, COUNT(c.id) as camera_count
            FROM stores s
            LEFT JOIN cameras c ON s.id = c.store_id
            WHERE s.store_identifier = ? AND s.organization_id = ?
            GROUP BY s.id
        """, (store_identifier, current_user["organization_id"]))
        store_info = await cursor.fetchone()
        
        if not store_info:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Generate instructions
        instructions = {
            "store_id": store_identifier,
            "store_name": store_info[2],
            "camera_count": store_info[6],
            "server_ip": MEDIA_SERVER_IP,
            "server_port": MEDIA_SERVER_PORT,
            "publish_urls": [
                f"rtsp://{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}/store_{store_identifier}_camera_{i}"
                for i in range(1, store_info[6] + 1)
            ],
            "setup_checklist": [
                "Configure each camera to publish to the provided RTSP URLs",
                "Ensure cameras are set to 720p or 1080p resolution",
                "Set frame rate to 15 FPS for optimal bandwidth usage",
                "Test local camera streams before publishing",
                "Verify outbound RTSP traffic is allowed on your network",
                "Contact support if streams don't appear in dashboard within 10 minutes"
            ]
        }
        
        return instructions

# Health and monitoring endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "centralized-retail-analytics",
        "media_server": f"{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}"
    }

@app.get("/api/system/status")
async def system_status():
    """Get system status"""
    processors_status = get_all_processors_status() if CENTRALIZED_PROCESSOR_AVAILABLE else {}
    
    return {
        "media_server": {
            "ip": MEDIA_SERVER_IP,
            "port": MEDIA_SERVER_PORT,
            "status": "running"  # TODO: Check actual MediaMTX status
        },
        "processors": {
            "available": CENTRALIZED_PROCESSOR_AVAILABLE,
            "active_count": len(processors_status),
            "details": processors_status
        },
        "database": {
            "path": DB_PATH,
            "status": "connected"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)