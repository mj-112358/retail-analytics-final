"""
Centralized Retail Analytics with WebSocket Push Model
Camera clients initiate connections and push video streams to server
"""
import os
import logging
import asyncio
import json
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import socketio
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite
import bcrypt
import jwt
from ultralytics import YOLO
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database and settings
DB_PATH = "centralized_retail_analytics.db"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"

# Load YOLO model
try:
    yolo_model = YOLO('yolov8n.pt')
    logger.info("✅ YOLO model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load YOLO model: {e}")
    yolo_model = None

# FastAPI app
app = FastAPI(
    title="Centralized Retail Analytics API (WebSocket)",
    description="Push model retail analytics with WebSocket camera connections",
    version="2.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Global storage for active camera streams and analytics
active_cameras: Dict[str, Dict[str, Any]] = {}
camera_analytics: Dict[str, Dict[str, Any]] = {}

# Database initialization (same as before)
async def init_database():
    """Initialize database with required tables"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Organizations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    subscription_plan TEXT DEFAULT 'basic',
                    api_key TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Stores table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER,
                    store_identifier TEXT NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    timezone TEXT DEFAULT 'UTC',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id),
                    UNIQUE(organization_id, store_identifier)
                )
            """)
            
            # Cameras table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id INTEGER,
                    camera_identifier INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    zone_type TEXT DEFAULT 'entrance',
                    location_description TEXT,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    websocket_session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id) REFERENCES stores (id),
                    UNIQUE(store_id, camera_identifier)
                )
            """)
            
            # Detection data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    person_count INTEGER DEFAULT 0,
                    confidence_scores TEXT,
                    bounding_boxes TEXT,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            """)
            
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'manager',
                    last_login_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id)
                )
            """)
            
            # Create default organization if none exists
            cursor = await db.execute("SELECT COUNT(*) FROM organizations")
            count = await cursor.fetchone()
            if count[0] == 0:
                await db.execute("""
                    INSERT INTO organizations (name, subscription_plan, api_key)
                    VALUES ('Demo Organization', 'premium', 'demo_api_key_12345')
                """)
                logger.info("✅ Created default demo organization")
            
            await db.commit()
            logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

# Authentication functions (same as before)
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

# YOLO processing function
def process_frame_with_yolo(frame_data: str) -> Dict[str, Any]:
    """Process base64 frame with YOLO detection"""
    try:
        if not yolo_model:
            return {"person_count": 0, "error": "YOLO model not available"}
        
        # Decode base64 image
        image_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"person_count": 0, "error": "Failed to decode frame"}
        
        # Run YOLO detection
        results = yolo_model(frame, classes=[0])  # Class 0 is 'person'
        
        person_count = 0
        confidences = []
        boxes = []
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if box.cls == 0:  # Person class
                        person_count += 1
                        confidences.append(float(box.conf))
                        boxes.append(box.xyxy.tolist()[0])
        
        return {
            "person_count": person_count,
            "confidence_scores": confidences,
            "bounding_boxes": boxes,
            "processed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"YOLO processing error: {e}")
        return {"person_count": 0, "error": str(e)}

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    """Handle camera client connection"""
    logger.info(f"🔌 Camera client connected: {sid}")
    await sio.emit('connection_established', {'status': 'connected', 'session_id': sid}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle camera client disconnection"""
    logger.info(f"🔌 Camera client disconnected: {sid}")
    
    # Update camera status in database
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE cameras 
            SET status = 'offline', websocket_session_id = NULL, last_seen = ?
            WHERE websocket_session_id = ?
        """, (datetime.now(), sid))
        await db.commit()
    
    # Remove from active cameras
    cameras_to_remove = [cam_id for cam_id, data in active_cameras.items() if data.get('session_id') == sid]
    for cam_id in cameras_to_remove:
        del active_cameras[cam_id]
        if cam_id in camera_analytics:
            del camera_analytics[cam_id]

@sio.event
async def camera_register(sid, data):
    """Register a camera with store and camera ID"""
    try:
        store_id = data.get('store_id')
        camera_id = data.get('camera_id')
        
        if not store_id or not camera_id:
            await sio.emit('error', {'message': 'Missing store_id or camera_id'}, room=sid)
            return
        
        # Update camera in database
        async with aiosqlite.connect(DB_PATH) as db:
            # Find camera by store identifier and camera identifier
            cursor = await db.execute("""
                SELECT c.id, c.name, c.zone_type, s.store_identifier
                FROM cameras c
                JOIN stores s ON c.store_id = s.id
                WHERE s.store_identifier = ? AND c.camera_identifier = ?
            """, (store_id, camera_id))
            camera_info = await cursor.fetchone()
            
            if not camera_info:
                await sio.emit('error', {'message': f'Camera not found: store_{store_id}_camera_{camera_id}'}, room=sid)
                return
            
            # Update camera status
            await db.execute("""
                UPDATE cameras 
                SET status = 'online', websocket_session_id = ?, last_seen = ?
                WHERE id = ?
            """, (sid, datetime.now(), camera_info[0]))
            await db.commit()
        
        # Add to active cameras
        camera_key = f"store_{store_id}_camera_{camera_id}"
        active_cameras[camera_key] = {
            'session_id': sid,
            'store_id': store_id,
            'camera_id': camera_id,
            'db_id': camera_info[0],
            'name': camera_info[1],
            'zone_type': camera_info[2],
            'connected_at': datetime.now()
        }
        
        # Initialize analytics
        camera_analytics[camera_key] = {
            'total_detections': 0,
            'last_person_count': 0,
            'last_update': datetime.now()
        }
        
        logger.info(f"✅ Camera registered: {camera_key} (session: {sid})")
        await sio.emit('registration_success', {
            'camera_key': camera_key,
            'message': 'Camera registered successfully'
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Camera registration error: {e}")
        await sio.emit('error', {'message': f'Registration failed: {str(e)}'}, room=sid)

@sio.event
async def camera_stream(sid, data):
    """Process incoming camera stream frame"""
    try:
        camera_id = data.get('camera_id')
        stream_data = data.get('stream_data')
        
        if not camera_id or not stream_data:
            return
        
        # Find active camera
        active_camera = None
        for cam_key, cam_data in active_cameras.items():
            if cam_data['session_id'] == sid:
                active_camera = cam_data
                camera_key = cam_key
                break
        
        if not active_camera:
            await sio.emit('error', {'message': 'Camera not registered'}, room=sid)
            return
        
        # Process frame with YOLO
        detection_result = process_frame_with_yolo(stream_data)
        
        # Update analytics
        if camera_key in camera_analytics:
            camera_analytics[camera_key]['last_person_count'] = detection_result['person_count']
            camera_analytics[camera_key]['last_update'] = datetime.now()
            camera_analytics[camera_key]['total_detections'] += detection_result['person_count']
        
        # Store detection in database
        if detection_result['person_count'] > 0:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("""
                    INSERT INTO detections (camera_id, person_count, confidence_scores, bounding_boxes)
                    VALUES (?, ?, ?, ?)
                """, (
                    active_camera['db_id'],
                    detection_result['person_count'],
                    json.dumps(detection_result.get('confidence_scores', [])),
                    json.dumps(detection_result.get('bounding_boxes', []))
                ))
                await db.commit()
        
        # Send acknowledgment back to camera
        await sio.emit('frame_processed', {
            'person_count': detection_result['person_count'],
            'timestamp': detection_result['processed_at']
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Stream processing error: {e}")

# FastAPI Endpoints
@app.get("/")
async def root():
    return {
        "service": "Centralized Retail Analytics (WebSocket Push Model)",
        "status": "running",
        "version": "2.1.0",
        "model": "push-websocket",
        "active_cameras": len(active_cameras),
        "docs": "/docs"
    }

@app.get("/api/system/status")
async def system_status():
    """Get system status including active WebSocket cameras"""
    return {
        "websocket_server": {
            "status": "running",
            "active_connections": len(active_cameras)
        },
        "active_cameras": {
            camera_key: {
                "store_id": data['store_id'],
                "camera_id": data['camera_id'],
                "name": data['name'],
                "zone_type": data['zone_type'],
                "connected_at": data['connected_at'].isoformat(),
                "session_id": data['session_id'][:8] + "..."  # Truncate for security
            }
            for camera_key, data in active_cameras.items()
        },
        "analytics_summary": camera_analytics,
        "yolo_model": "available" if yolo_model else "unavailable",
        "database": {"path": DB_PATH, "status": "connected"}
    }

@app.get("/api/analytics/live")
async def get_live_analytics():
    """Get live analytics from WebSocket cameras"""
    total_people = sum(analytics.get('last_person_count', 0) for analytics in camera_analytics.values())
    
    return {
        "total_active_cameras": len(active_cameras),
        "total_people_detected": total_people,
        "camera_details": {
            camera_key: {
                "current_count": analytics.get('last_person_count', 0),
                "total_detections": analytics.get('total_detections', 0),
                "last_update": analytics.get('last_update', datetime.now()).isoformat(),
                "camera_info": active_cameras.get(camera_key, {})
            }
            for camera_key, analytics in camera_analytics.items()
        },
        "model": "push-websocket"
    }

# Authentication endpoints (same as before but simplified)
@app.post("/api/auth/login")
async def login(credentials: dict):
    """Simple login for testing"""
    # For demo purposes, accept any email/password
    token_data = {"email": credentials.get("email", "demo@test.com"), "user_id": 1, "org_id": 1}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "centralized-retail-analytics-websocket",
        "active_cameras": len(active_cameras),
        "websocket_enabled": True
    }

@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("🚀 Centralized RetailIQ Analytics (WebSocket Push Model) - Ready")

if __name__ == "__main__":
    uvicorn.run("centralized_websocket_main:socket_app", host="0.0.0.0", port=5000, reload=True)