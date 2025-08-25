"""
FINAL PRODUCTION FASTAPI APPLICATION
Complete retail analytics system for real customers
"""
import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our production modules
from auth_final import (
    signup_user, login_user, refresh_access_token,
    get_current_user, get_current_store, 
    UserSignup, UserLogin, TokenResponse
)
from analytics_engine_final import create_analytics_engine, run_analytics_calculation
from openai_insights_final import generate_store_insights, create_insights_generator
from rtsp_camera_system_final import (
    get_camera_manager, add_camera_to_store, remove_camera_from_store
)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create FastAPI app
app = FastAPI(
    title="RetailIQ Analytics - Production API",
    description="Complete retail analytics system with RTSP camera processing and AI insights",
    version="2.0.0"
)

# CORS Configuration for production
FRONTEND_URLS = [
    os.getenv("CORS_ORIGINS", "https://retail-analytics-final-git-main-mrityunjays-projects-6c42d667.vercel.app").split(","),
    "https://*.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173"
]

# Flatten the list if CORS_ORIGINS contains multiple URLs
FRONTEND_URLS = [url.strip() for sublist in FRONTEND_URLS for url in (sublist if isinstance(sublist, list) else [sublist])]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
analytics_engine = create_analytics_engine(DATABASE_URL)
insights_generator = create_insights_generator(DATABASE_URL)
camera_manager = get_camera_manager(DATABASE_URL)

# Pydantic Models
class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    zone_type: str
    location_description: Optional[str] = None
    
    @validator('zone_type')
    def validate_zone_type(cls, v):
        allowed_zones = ['entrance', 'checkout', 'electronics', 'clothing', 'grocery', 'dairy', 'pharmacy', 'general']
        if v not in allowed_zones:
            raise ValueError(f'Zone type must be one of: {", ".join(allowed_zones)}')
        return v

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    zone_type: Optional[str] = None
    location_description: Optional[str] = None
    is_active: Optional[bool] = None

class PromotionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    promotion_type: str
    target_zones: List[str] = []
    expected_impact_percentage: Optional[float] = None

class InsightRequest(BaseModel):
    period_start: date
    period_end: date
    insight_type: str  # "weekly", "monthly", "promo_effectiveness", "festival_analysis"
    promotion_id: Optional[int] = None
    festival_name: Optional[str] = None

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    """Simple health check endpoint for Railway deployment"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "RetailIQ Analytics API",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RetailIQ Analytics - Production API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Real-time RTSP camera processing",
            "Person detection and tracking",
            "Zone-wise analytics",
            "AI-powered insights",
            "Promotion effectiveness analysis",
            "Queue monitoring",
            "Dwell time analysis"
        ]
    }

# Authentication Endpoints
@app.post("/api/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserSignup):
    """Register new user and store"""
    return await signup_user(user_data)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user"""
    return await login_user(login_data)

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    """Refresh access token"""
    data = await request.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    return await refresh_access_token(refresh_token)

@app.get("/api/auth/me")
async def get_profile(current_user: Dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "user": current_user,
        "message": "Profile retrieved successfully"
    }

# Camera Management Endpoints
@app.get("/api/cameras")
async def get_cameras(store_id: int = Depends(get_current_store)):
    """Get all cameras for the store"""
    try:
        cameras = await camera_manager.get_camera_status(store_id)
        return {
            "success": True,
            "cameras": cameras,
            "total": len(cameras)
        }
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cameras")

@app.post("/api/cameras")
async def create_camera(
    camera_data: CameraCreate,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_store)
):
    """Add new camera to store"""
    try:
        camera_id = await add_camera_to_store(
            store_id=store_id,
            name=camera_data.name,
            rtsp_url=camera_data.rtsp_url,
            zone_type=camera_data.zone_type,
            location_description=camera_data.location_description or "",
            database_url=DATABASE_URL
        )
        
        # Start analytics calculation in background
        background_tasks.add_task(run_analytics_calculation, analytics_engine, store_id)
        
        return {
            "success": True,
            "message": "Camera added successfully",
            "camera_id": camera_id
        }
    except Exception as e:
        logger.error(f"Error adding camera: {e}")
        raise HTTPException(status_code=500, detail="Failed to add camera")

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(
    camera_id: int,
    store_id: int = Depends(get_current_store)
):
    """Remove camera from store"""
    try:
        await remove_camera_from_store(camera_id, DATABASE_URL)
        return {
            "success": True,
            "message": "Camera removed successfully"
        }
    except Exception as e:
        logger.error(f"Error removing camera: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove camera")

@app.get("/api/cameras/{camera_id}/status")
async def get_camera_status(
    camera_id: int,
    store_id: int = Depends(get_current_store)
):
    """Get detailed status of a specific camera"""
    try:
        cameras = await camera_manager.get_camera_status(store_id)
        camera = next((c for c in cameras if c['id'] == camera_id), None)
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {
            "success": True,
            "camera": camera
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get camera status")

# Analytics Endpoints
@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(
    days: int = 7,
    store_id: int = Depends(get_current_store)
):
    """Get comprehensive dashboard analytics"""
    try:
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()
        
        analytics_data = await analytics_engine.get_store_analytics(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": analytics_data
        }
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@app.get("/api/analytics/metrics")
async def get_current_metrics(store_id: int = Depends(get_current_store)):
    """Get current day metrics summary"""
    try:
        analytics_data = await analytics_engine.get_store_analytics(
            store_id=store_id,
            start_date=date.today(),
            end_date=date.today()
        )
        
        # Get today's data
        today_data = analytics_data['daily_analytics'][0] if analytics_data['daily_analytics'] else None
        
        if today_data:
            return {
                "success": True,
                "data": {
                    "total_visitors": today_data['total_footfall'],
                    "unique_visitors": today_data['unique_visitors'],
                    "avg_dwell_time_minutes": round(today_data['avg_dwell_time_seconds'] / 60, 1),
                    "peak_hour": f"{today_data['peak_hour']:02d}:00",
                    "peak_hour_visitors": today_data['peak_hour_visitors'],
                    "conversion_rate": round(today_data['conversion_rate'], 2),
                    "zone_metrics": today_data['zone_metrics'],
                    "hourly_data": analytics_data['today_hourly']
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "total_visitors": 0,
                    "unique_visitors": 0,
                    "avg_dwell_time_minutes": 0,
                    "peak_hour": "12:00",
                    "peak_hour_visitors": 0,
                    "conversion_rate": 0,
                    "zone_metrics": {},
                    "hourly_data": []
                }
            }
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current metrics")

# Promotion Management
@app.post("/api/promotions")
async def create_promotion(
    promotion_data: PromotionCreate,
    store_id: int = Depends(get_current_store)
):
    """Create new promotion/campaign"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        promotion_id = await conn.fetchval("""
            INSERT INTO promotions (
                store_id, name, description, start_date, end_date,
                promotion_type, target_zones, expected_impact_percentage
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, store_id, promotion_data.name, promotion_data.description,
             promotion_data.start_date, promotion_data.end_date,
             promotion_data.promotion_type, promotion_data.target_zones,
             promotion_data.expected_impact_percentage)
        await conn.close()
        
        return {
            "success": True,
            "message": "Promotion created successfully",
            "promotion_id": promotion_id
        }
    except Exception as e:
        logger.error(f"Error creating promotion: {e}")
        raise HTTPException(status_code=500, detail="Failed to create promotion")

@app.get("/api/promotions")
async def get_promotions(
    active_only: bool = False,
    store_id: int = Depends(get_current_store)
):
    """Get promotions for store"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
            SELECT id, name, description, start_date, end_date, promotion_type, 
                   target_zones, expected_impact_percentage, created_at
            FROM promotions 
            WHERE store_id = $1
        """
        params = [store_id]
        
        if active_only:
            query += " AND start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE"
        
        query += " ORDER BY created_at DESC"
        
        promotions = await conn.fetch(query, *params)
        await conn.close()
        
        return {
            "success": True,
            "promotions": [
                {
                    "id": p['id'],
                    "name": p['name'],
                    "description": p['description'],
                    "start_date": p['start_date'].isoformat(),
                    "end_date": p['end_date'].isoformat(),
                    "promotion_type": p['promotion_type'],
                    "target_zones": p['target_zones'],
                    "expected_impact_percentage": p['expected_impact_percentage']
                } for p in promotions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting promotions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve promotions")

# AI Insights Generation
@app.post("/api/insights/generate")
async def generate_insights(
    insight_request: InsightRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_store)
):
    """Generate AI insights for store performance"""
    try:
        # Get metrics data for the period
        metrics_data = await analytics_engine.get_metrics_for_ai_analysis(
            store_id=store_id,
            start_date=insight_request.period_start,
            end_date=insight_request.period_end,
            include_comparison=True
        )
        
        # Get promotion data if needed
        promotion_data = None
        if insight_request.promotion_id:
            import asyncpg
            conn = await asyncpg.connect(DATABASE_URL)
            promo = await conn.fetchrow("""
                SELECT * FROM promotions WHERE id = $1 AND store_id = $2
            """, insight_request.promotion_id, store_id)
            await conn.close()
            
            if promo:
                promotion_data = dict(promo)
        elif insight_request.festival_name:
            promotion_data = {
                "name": insight_request.festival_name,
                "event_type": "Festival",
                "start_date": insight_request.period_start,
                "end_date": insight_request.period_end,
                "expected_behavior": "Increased shopping activity"
            }
        
        # Generate insights in background
        insight_result = await generate_store_insights(
            database_url=DATABASE_URL,
            store_id=store_id,
            period_start=insight_request.period_start,
            period_end=insight_request.period_end,
            insight_type=insight_request.insight_type,
            metrics_data=metrics_data,
            promotion_data=promotion_data
        )
        
        return {
            "success": True,
            "insights": insight_result
        }
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@app.get("/api/insights/history")
async def get_insights_history(
    limit: int = 10,
    store_id: int = Depends(get_current_store)
):
    """Get recent insights history"""
    try:
        insights = await insights_generator.get_insights_history(store_id, limit)
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error getting insights history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insights history")

# System Management
@app.post("/api/system/start-analytics")
async def start_analytics_processing(
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_store)
):
    """Start analytics processing for all cameras"""
    try:
        # Start all cameras for the store
        await camera_manager.start_all_cameras(store_id)
        
        # Schedule periodic analytics calculation
        background_tasks.add_task(run_analytics_calculation, analytics_engine, store_id)
        
        return {
            "success": True,
            "message": "Analytics processing started for all cameras"
        }
    except Exception as e:
        logger.error(f"Error starting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analytics processing")

@app.post("/api/system/stop-analytics")
async def stop_analytics_processing():
    """Stop all analytics processing"""
    try:
        camera_manager.stop_all_cameras()
        return {
            "success": True,
            "message": "Analytics processing stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop analytics processing")

# Background task to ensure analytics are running
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("RetailIQ Analytics API starting up...")
    
    try:
        # Initialize database schema
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Read and execute schema
        with open('/app/database/schema_final.sql', 'r') as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)
        await conn.close()
        
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
    
    logger.info("RetailIQ Analytics API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RetailIQ Analytics API...")
    camera_manager.stop_all_cameras()
    logger.info("Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)