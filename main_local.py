#!/usr/bin/env python3
"""
Local Development Version of Retail Analytics
Simplified for testing RTSP functionality with SQLite
"""
import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load local environment
load_dotenv('.env.local')

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiosqlite
import cv2
import numpy as np
from ultralytics import YOLO

# Initialize FastAPI
app = FastAPI(
    title="RetailIQ Analytics - Local Development",
    description="Local testing environment for RTSP camera processing",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Handle preflight requests
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
        content={}
    )

# Initialize YOLO model
yolo_model = None
try:
    yolo_model = YOLO('yolov8n.pt')  # Will download if not exists
    print("✅ YOLO model loaded successfully")
except Exception as e:
    print(f"⚠️  YOLO model loading error: {e}")

# Database path
DB_PATH = "local_retail_analytics.db"

# Pydantic models
class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    zone_type: str = "general"

class CameraResponse(BaseModel):
    id: int
    name: str
    rtsp_url: str
    zone_type: str
    status: str
    last_detection_at: str = None

# Database helper
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

# Root endpoint
@app.get("/")
async def root():
    return {"message": "RetailIQ Analytics - Local Development", "status": "running"}

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "local_development",
        "yolo_loaded": yolo_model is not None,
        "database": Path(DB_PATH).exists()
    }

# API health endpoint
@app.get("/api/health")
async def api_health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "local_development",
        "yolo_loaded": yolo_model is not None,
        "database": Path(DB_PATH).exists()
    }

# Simple auth endpoints for local testing
@app.post("/api/auth/signup")
async def signup(user_data: dict):
    """Simple signup for local testing"""
    return {
        "message": "Account created successfully",
        "user": {
            "id": 1,
            "name": user_data.get("name", "Test User"),
            "email": user_data.get("email", "test@example.com"),
            "store_name": user_data.get("store_name", "Test Store")
        },
        "token": "local-test-token"
    }

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Simple login for local testing"""
    return {
        "message": "Login successful",
        "user": {
            "id": 1,
            "name": "Test User",
            "email": credentials.get("email", "test@example.com"),
            "store_name": "Test Store"
        },
        "token": "local-test-token"
    }

@app.get("/api/auth/me")
async def get_profile():
    """Get user profile for local testing"""
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "store_name": "Test Store"
    }

@app.post("/api/auth/verify-token")
async def verify_token(data: dict):
    """Verify token for local testing - always return success"""
    return {
        "success": True,
        "message": "Token is valid",
        "user": {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "store_name": "Test Store"
        }
    }

# Dashboard endpoints for local testing
@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(date: str = None):
    """Mock dashboard metrics for local testing"""
    return {
        "total_visitors": 45,
        "current_visitors": 8,
        "avg_dwell_time": 4.2,
        "peak_hour": "14:00",
        "total_cameras": 2,
        "active_cameras": 2,
        "queue_alerts": 0,
        "hourly_data": [
            {"hour": "09:00", "visitors": 12},
            {"hour": "10:00", "visitors": 18},
            {"hour": "11:00", "visitors": 25},
            {"hour": "12:00", "visitors": 32},
            {"hour": "13:00", "visitors": 28},
            {"hour": "14:00", "visitors": 45},
            {"hour": "15:00", "visitors": 38}
        ]
    }

@app.post("/api/dashboard/insights")
async def generate_insights(data: dict):
    """Mock AI insights for local testing"""
    return {
        "insights": "Your store shows strong afternoon traffic patterns. Peak hours are between 2-4 PM with 45 visitors. Consider staffing adjustments during these times.",
        "recommendations": [
            "Add more staff during 2-4 PM peak hours",
            "Monitor dairy section for high dwell times",
            "Consider promotional displays near entrance"
        ],
        "promotion_effectiveness": 78,
        "timestamp": datetime.now().isoformat()
    }

# Simple camera processing function
class RTSPProcessor:
    def __init__(self):
        self.active_streams = {}
    
    async def process_rtsp_stream(self, camera_id: int, rtsp_url: str):
        """Process RTSP stream and detect persons"""
        try:
            # Decode URL-encoded characters
            import urllib.parse
            decoded_url = urllib.parse.unquote(rtsp_url)
            print(f"🔗 Attempting to connect to RTSP: {decoded_url}")
            
            # Open video stream with timeout settings
            cap = cv2.VideoCapture(decoded_url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 second timeout
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)   # 10 second read timeout
            
            if not cap.isOpened():
                print(f"❌ Failed to open RTSP stream: {decoded_url}")
                # Update camera status to error
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute(
                        "UPDATE cameras SET status = 'error', error_message = ? WHERE id = ?",
                        ("Failed to connect to RTSP stream", camera_id)
                    )
                    await db.commit()
                return
            
            print(f"✅ Started processing camera {camera_id}: {rtsp_url}")
            
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️  Failed to read frame from camera {camera_id}")
                    break
                
                # Process every 30th frame to reduce load
                if frame_count % 30 == 0 and yolo_model:
                    try:
                        # Run YOLO detection
                        results = yolo_model(frame, conf=0.5)
                        
                        # Count persons (class 0 in COCO dataset)
                        person_count = 0
                        for result in results:
                            for box in result.boxes:
                                if box.cls == 0:  # Person class
                                    person_count += 1
                        
                        if person_count > 0:
                            print(f"📹 Camera {camera_id}: Detected {person_count} person(s)")
                            
                            # Update database
                            async with aiosqlite.connect(DB_PATH) as db:
                                await db.execute(
                                    "UPDATE cameras SET last_detection_at = ?, status = 'online' WHERE id = ?",
                                    (datetime.now().isoformat(), camera_id)
                                )
                                await db.commit()
                    
                    except Exception as e:
                        print(f"⚠️  Detection error for camera {camera_id}: {e}")
                
                frame_count += 1
                await asyncio.sleep(0.1)  # Small delay
        
        except Exception as e:
            print(f"❌ RTSP processing error for camera {camera_id}: {e}")
            # Update camera status to error
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE cameras SET status = 'error', error_message = ? WHERE id = ?",
                    (str(e), camera_id)
                )
                await db.commit()
        
        finally:
            if 'cap' in locals():
                cap.release()

# Global processor
rtsp_processor = RTSPProcessor()

# Camera endpoints
@app.post("/cameras", response_model=CameraResponse)
async def create_camera(camera: CameraCreate, background_tasks: BackgroundTasks):
    """Add a new camera and start processing"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO cameras (name, rtsp_url, zone_type, status)
            VALUES (?, ?, ?, 'offline')
        """, (camera.name, camera.rtsp_url, camera.zone_type))
        
        camera_id = cursor.lastrowid
        await db.commit()
        
        # Start RTSP processing in background
        background_tasks.add_task(
            rtsp_processor.process_rtsp_stream, 
            camera_id, 
            camera.rtsp_url
        )
        
        return CameraResponse(
            id=camera_id,
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            zone_type=camera.zone_type,
            status="starting"
        )

@app.get("/cameras")
async def list_cameras():
    """List all cameras"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # Enable dict-like access
        cursor = await db.execute("SELECT * FROM cameras ORDER BY created_at DESC")
        cameras = await cursor.fetchall()
        
        return [
            CameraResponse(
                id=camera['id'],
                name=camera['name'],
                rtsp_url=camera['rtsp_url'],
                zone_type=camera['zone_type'],
                status=camera['status'] or 'offline',
                last_detection_at=camera['last_detection_at']
            )
            for camera in cameras
        ]

@app.get("/cameras/{camera_id}/status")
async def get_camera_status(camera_id: int):
    """Get detailed camera status"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # Enable dict-like access
        cursor = await db.execute(
            "SELECT * FROM cameras WHERE id = ?", 
            (camera_id,)
        )
        camera = await cursor.fetchone()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {
            "id": camera['id'],
            "name": camera['name'],
            "status": camera['status'],
            "last_detection_at": camera['last_detection_at'],
            "error_message": camera['error_message']
        }

@app.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: int):
    """Delete a camera"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM cameras WHERE id = ?", 
            (camera_id,)
        )
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {"message": "Camera deleted successfully"}

@app.get("/cameras/status")
async def get_cameras_detection_status():
    """Get detection status for all cameras"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # Enable dict-like access
        cursor = await db.execute("SELECT * FROM cameras")
        cameras = await cursor.fetchall()
        
        return {
            "success": True,
            "cameras": [
                {
                    "camera_id": camera['id'],
                    "name": camera['name'],
                    "detection_active": camera['status'] == 'online',
                    "enabled_features": ["person_detection", "dwell_time"]
                }
                for camera in cameras
            ]
        }

@app.get("/cameras/features")
async def get_camera_features():
    """Get available camera feature types"""
    return {
        "success": True,
        "feature_types": {
            "person_detection": {
                "name": "Person Detection",
                "description": "Detect and count people in camera feed",
                "requires_coordinates": False,
                "coordinate_type": None
            },
            "dwell_time": {
                "name": "Dwell Time Analysis",
                "description": "Track how long people stay in specific areas",
                "requires_coordinates": True,
                "coordinate_type": "polygon"
            },
            "queue_monitoring": {
                "name": "Queue Monitoring", 
                "description": "Monitor queue lengths and wait times",
                "requires_coordinates": True,
                "coordinate_type": "line"
            },
            "zone_analytics": {
                "name": "Zone Analytics",
                "description": "Analyze foot traffic in specific zones",
                "requires_coordinates": True,
                "coordinate_type": "polygon"
            }
        }
    }

# Test RTSP endpoint
@app.post("/test-rtsp")
async def test_rtsp_connection(rtsp_url: str):
    """Test RTSP connection without saving to database"""
    try:
        import urllib.parse
        decoded_url = urllib.parse.unquote(rtsp_url)
        print(f"🧪 Testing RTSP connection: {decoded_url}")
        
        cap = cv2.VideoCapture(decoded_url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second timeout for testing
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        
        if not cap.isOpened():
            return {
                "success": False, 
                "error": "Failed to connect to RTSP stream. Check URL, credentials, and network connectivity."
            }
        
        # Try to read one frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return {
                "success": False, 
                "error": "Connected to stream but failed to read frame. Stream may be inactive."
            }
        
        return {
            "success": True, 
            "message": "RTSP connection successful!",
            "frame_size": f"{frame.shape[1]}x{frame.shape[0]}",
            "url_tested": decoded_url
        }
    
    except Exception as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting RetailIQ Analytics - Local Development")
    print("📹 RTSP camera processing enabled")
    print("🎯 Ready for testing!")
    uvicorn.run(app, host="0.0.0.0", port=3002)