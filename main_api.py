"""
RETAIL ANALYTICS API - Lightweight Version
FastAPI backend without GPU dependencies - optimized for DigitalOcean App Platform
"""
import os
import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import bcrypt
import jwt
import openai
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

# Import our database components
from database import get_db, test_connection
from models import (
    User, Store, Camera, ZoneType, Visitor, Detection, HourlyAnalytics,
    DailyAnalytics, QueueEvent, ProductInteraction, Promotion, AIInsight,
    DetectionSession, HeatmapData, SystemAlert
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key-here")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-jwt-signing")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", 8080))

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY
if OPENAI_API_KEY == "your-openai-key-here":
    logger.warning("⚠️ OpenAI API key not set! Set OPENAI_API_KEY environment variable for AI insights.")

# Create FastAPI app
app = FastAPI(
    title="RetailIQ Analytics - API Only",
    description="Lightweight API backend without GPU dependencies",
    version="5.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + [
        "https://*.vercel.app",
        "https://*.digitalocean.app",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for API
class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    store_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    zone_type: str
    location_description: Optional[str] = None

class InsightRequest(BaseModel):
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    insight_type: str = "general"
    include_promo: bool = False
    promo_start: Optional[str] = None
    promo_end: Optional[str] = None
    promo_name: Optional[str] = None
    festival_name: Optional[str] = None

class PromotionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    promotion_type: str = "discount"
    start_date: str
    end_date: str
    target_zones: List[str] = []
    discount_percentage: Optional[float] = None
    expected_impact_percentage: Optional[float] = None

# Mock visitor data creation for demo purposes
class MockVisitorGenerator:
    """Generate realistic visitor data for demo/testing"""
    
    @staticmethod
    def create_mock_visitor_data(camera_id: int, store_id: int, zone_type: str, count: int = 1):
        """Create mock visitor entries for testing without real RTSP processing"""
        from datetime import datetime, timedelta
        import random
        
        now = datetime.now()
        today = now.date()
        
        # Zone-specific dwell times (seconds)
        zone_dwell_times = {
            'entrance': (20, 60),
            'checkout': (120, 300),
            'dairy_section': (60, 180),
            'electronics': (180, 600),
            'clothing': (120, 480),
            'grocery': (45, 150),
            'pharmacy': (90, 300),
            'general': (60, 200)
        }
        
        dwell_range = zone_dwell_times.get(zone_type, (60, 200))
        
        mock_visitors = []
        for i in range(count):
            # Random time within the last few hours
            hours_ago = random.randint(0, 12)
            visitor_time = now - timedelta(hours=hours_ago)
            dwell_seconds = random.randint(dwell_range[0], dwell_range[1])
            
            mock_visitors.append({
                'timestamp': visitor_time,
                'dwell_time': dwell_seconds,
                'confidence': random.uniform(0.75, 0.95)
            })
        
        return mock_visitors

# Authentication Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Extract user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    # Test database connection
    try:
        if not test_connection():
            logger.error("❌ Database connection failed on startup")
        else:
            logger.info("✅ Database connection verified")
    except Exception as e:
        logger.warning(f"⚠️ Database connection test failed: {e}")
    
    logger.info("🚀 RetailIQ Analytics API - Lightweight Version Ready")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down RetailIQ Analytics API")

# Basic endpoints
@app.get("/")
async def root():
    return {
        "service": "RetailIQ Analytics API - Lightweight",
        "status": "running",
        "version": "5.0.0",
        "environment": ENVIRONMENT,
        "database": "PostgreSQL with SQLAlchemy",
        "note": "GPU processing handled by separate worker service",
        "features": {
            "authentication": True,
            "camera_management": True,
            "analytics_api": True,
            "ai_insights": True,
            "promotional_analysis": True,
            "dashboard_metrics": True,
            "gpu_processing": "External worker service"
        }
    }

@app.get("/health")
async def health_check():
    """Enhanced health check"""
    try:
        db_status = "healthy" if test_connection() else "unhealthy"
    except:
        db_status = "unknown"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "environment": ENVIRONMENT,
        "port": PORT,
        "service_type": "api_only"
    }

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": "RetailIQ Analytics API - Lightweight"}

# Authentication endpoints
@app.post("/api/auth/signup")
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """User signup with SQLAlchemy"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user and store
    password_hash = hash_password(user_data.password)
    
    try:
        # Create user
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.name,
            store_name=user_data.store_name,
            is_active=True
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Create store
        store = Store(
            user_id=user.id,
            name=user_data.store_name,
            is_active=True
        )
        db.add(store)
        db.commit()
        
        user_response = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "store_name": user.store_name,
            "store_id": store.id
        }
        
        token = create_jwt_token(user_response)
        
        return {
            "message": "User created successfully",
            "token": token,
            "user": user_response
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@app.post("/api/auth/login")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """User login with SQLAlchemy"""
    user = db.query(User).filter(
        and_(User.email == credentials.email, User.is_active == True)
    ).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Get user's store
    store = db.query(Store).filter(Store.user_id == user.id).first()
    
    user_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "store_name": user.store_name,
        "store_id": store.id if store else None
    }
    
    token = create_jwt_token(user_data)
    
    return {
        "message": "Login successful",
        "token": token,
        "user": user_data
    }

@app.get("/api/auth/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "store_name": current_user.store_name
    }

# Camera management endpoints
@app.get("/cameras")
async def list_cameras(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's cameras with information"""
    # Get user's store
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        return []
    
    # Get cameras with zone information and today's visitor count
    cameras = db.query(Camera, ZoneType, func.count(Visitor.id).label('visitors_today')).join(
        ZoneType, Camera.zone_type_id == ZoneType.id, isouter=True
    ).join(
        Visitor, and_(
            Camera.id == Visitor.camera_id,
            Visitor.date == date.today()
        ), isouter=True
    ).filter(
        and_(Camera.store_id == store.id, Camera.is_active == True)
    ).group_by(Camera.id, ZoneType.id).order_by(desc(Camera.created_at)).all()
    
    return [
        {
            "id": camera.Camera.id,
            "name": camera.Camera.name,
            "rtsp_url": camera.Camera.rtsp_url,
            "zone_type": camera.ZoneType.zone_code if camera.ZoneType else "general",
            "zone_display_name": camera.ZoneType.display_name if camera.ZoneType else "General Area",
            "status": camera.Camera.status,
            "detection_enabled": camera.Camera.detection_enabled,
            "last_detection_at": camera.Camera.last_detection_at,
            "last_heartbeat_at": camera.Camera.last_heartbeat_at,
            "visitors_today": camera.visitors_today or 0,
            "location_description": camera.Camera.location_description,
            "processing_note": "GPU processing handled by worker service"
        }
        for camera in cameras
    ]

@app.post("/cameras")
async def create_camera(
    camera_data: CameraCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create camera (processing will be handled by GPU worker)"""
    # Get user's store
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        raise HTTPException(status_code=400, detail="No store found for user")
    
    # Get zone type
    zone_type = db.query(ZoneType).filter(ZoneType.zone_code == camera_data.zone_type).first()
    if not zone_type:
        zone_type = db.query(ZoneType).filter(ZoneType.zone_code == 'general').first()
    
    try:
        # Create camera
        camera = Camera(
            store_id=store.id,
            name=camera_data.name,
            rtsp_url=camera_data.rtsp_url,
            zone_type_id=zone_type.id,
            location_description=camera_data.location_description,
            status='configured',  # Will be activated by GPU worker
            detection_enabled=True,
            is_active=True
        )
        db.add(camera)
        db.commit()
        
        # Add some mock visitor data for demo purposes
        background_tasks.add_task(
            create_demo_visitor_data,
            camera.id, store.id, camera_data.zone_type, db
        )
        
        return {
            "message": "Camera created successfully",
            "camera_id": camera.id,
            "zone_type": zone_type.display_name,
            "note": "GPU processing will be handled by worker service",
            "demo_data": "Mock visitor data will be generated for demonstration"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Camera creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create camera")

async def create_demo_visitor_data(camera_id: int, store_id: int, zone_type: str, db: Session):
    """Create demo visitor data for testing the system"""
    import random
    from datetime import datetime, timedelta
    
    try:
        # Get zone type ID
        zone_type_obj = db.query(ZoneType).filter(ZoneType.zone_code == zone_type).first()
        zone_type_id = zone_type_obj.id if zone_type_obj else None
        
        # Create some demo visitors for today
        today = date.today()
        now = datetime.now()
        
        # Generate 3-8 demo visitors
        visitor_count = random.randint(3, 8)
        mock_generator = MockVisitorGenerator()
        mock_visitors = mock_generator.create_mock_visitor_data(camera_id, store_id, zone_type, visitor_count)
        
        for visitor_data in mock_visitors:
            # Create visitor record
            visitor = Visitor(
                store_id=store_id,
                camera_id=camera_id,
                first_seen_at=visitor_data['timestamp'],
                last_seen_at=visitor_data['timestamp'],
                zone_type_id=zone_type_id,
                date=today,
                total_dwell_time_seconds=visitor_data['dwell_time'],
                confidence_score=visitor_data['confidence'],
                is_unique=True
            )
            db.add(visitor)
        
        # Update hourly analytics
        hour = now.hour
        hourly = db.query(HourlyAnalytics).filter(
            and_(
                HourlyAnalytics.store_id == store_id,
                HourlyAnalytics.camera_id == camera_id,
                HourlyAnalytics.zone_type_id == zone_type_id,
                HourlyAnalytics.date == today,
                HourlyAnalytics.hour == hour
            )
        ).first()
        
        if hourly:
            hourly.total_visitors += visitor_count
            hourly.unique_visitors += visitor_count
        else:
            hourly = HourlyAnalytics(
                store_id=store_id,
                camera_id=camera_id,
                zone_type_id=zone_type_id,
                date=today,
                hour=hour,
                total_visitors=visitor_count,
                unique_visitors=visitor_count,
                avg_dwell_time_seconds=sum(v['dwell_time'] for v in mock_visitors) / len(mock_visitors)
            )
            db.add(hourly)
        
        db.commit()
        logger.info(f"Created {visitor_count} demo visitors for camera {camera_id}")
        
    except Exception as e:
        logger.error(f"Error creating demo visitor data: {e}")
        db.rollback()

# Dashboard metrics endpoint
@app.get("/api/dashboard/metrics")
async def get_comprehensive_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard metrics"""
    # Get user's store
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        return {"error": "No store found"}
    
    today = date.today()
    
    # Get comprehensive metrics for today
    daily_stats = db.query(
        func.count(func.distinct(Visitor.visitor_uuid)).label('unique_visitors'),
        func.count(Visitor.visitor_uuid).label('total_footfall'),
        func.avg(Visitor.total_dwell_time_seconds).label('avg_dwell_time'),
        func.count(func.distinct(Visitor.camera_id)).label('active_cameras')
    ).join(Camera, Visitor.camera_id == Camera.id).filter(
        and_(Camera.store_id == store.id, Visitor.date == today)
    ).first()
    
    # Get zone-wise analytics
    zone_stats = db.query(
        ZoneType.zone_code,
        ZoneType.display_name,
        func.count(func.distinct(Visitor.visitor_uuid)).label('unique_visitors'),
        func.count(Visitor.visitor_uuid).label('total_visitors'),
        func.avg(Visitor.total_dwell_time_seconds).label('avg_dwell_time'),
        func.count(ProductInteraction.id).label('product_interactions')
    ).join(
        Camera, ZoneType.id == Camera.zone_type_id
    ).join(
        Visitor, and_(Camera.id == Visitor.camera_id, Visitor.date == today), isouter=True
    ).join(
        ProductInteraction, and_(
            Visitor.id == ProductInteraction.visitor_id,
            func.date(ProductInteraction.timestamp) == today
        ), isouter=True
    ).filter(Camera.store_id == store.id).group_by(
        ZoneType.zone_code, ZoneType.display_name
    ).all()
    
    # Get peak hour
    peak_hour = db.query(
        HourlyAnalytics.hour,
        func.sum(HourlyAnalytics.total_visitors).label('hour_visitors')
    ).join(Camera, HourlyAnalytics.camera_id == Camera.id).filter(
        and_(Camera.store_id == store.id, HourlyAnalytics.date == today)
    ).group_by(HourlyAnalytics.hour).order_by(
        desc('hour_visitors')
    ).first()
    
    return {
        "footfall_today": int(daily_stats.total_footfall or 0),
        "unique_visitors": int(daily_stats.unique_visitors or 0),
        "dwell_time_avg": float(daily_stats.avg_dwell_time or 0),
        "active_cameras": int(daily_stats.active_cameras or 0),
        "peak_hour": f"{peak_hour.hour:02d}:00" if peak_hour else "N/A",
        "peak_hour_visitors": int(peak_hour.hour_visitors) if peak_hour else 0,
        "total_product_interactions": sum(zone.product_interactions or 0 for zone in zone_stats),
        "zone_analytics": [
            {
                "zone_code": zone.zone_code,
                "zone_name": zone.display_name,
                "unique_visitors": zone.unique_visitors or 0,
                "total_visitors": zone.total_visitors or 0,
                "avg_dwell_time_seconds": float(zone.avg_dwell_time or 0),
                "product_interactions": zone.product_interactions or 0
            }
            for zone in zone_stats
        ],
        "processing_note": "Real-time processing handled by GPU worker service"
    }

# AI Insights endpoint (simplified for API-only version)
@app.post("/api/dashboard/insights")
async def generate_insights(
    request: InsightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI insights using existing visitor data"""
    if OPENAI_API_KEY == "your-openai-key-here":
        return {
            "insights": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
            "recommendations": ["Configure OpenAI API key to get real insights"],
            "confidence_score": 0
        }
    
    # Get user's store
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        raise HTTPException(status_code=400, detail="No store found")
    
    # Set date range
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    if request.period_start and request.period_end:
        try:
            start_date = datetime.fromisoformat(request.period_start.replace('Z', '')).date()
            end_date = datetime.fromisoformat(request.period_end.replace('Z', '')).date()
        except:
            pass
    
    # Get analytics data from database
    analytics_data = db.query(
        func.count(func.distinct(Visitor.visitor_uuid)).label('total_unique_visitors'),
        func.count(Visitor.visitor_uuid).label('total_footfall'),
        func.avg(Visitor.total_dwell_time_seconds).label('avg_dwell_time'),
        func.count(func.distinct(Visitor.camera_id)).label('active_cameras')
    ).join(Camera, Visitor.camera_id == Camera.id).filter(
        and_(Camera.store_id == store.id, Visitor.date.between(start_date, end_date))
    ).first()
    
    # Create prompt for OpenAI
    prompt = f"""
You are a retail analytics expert analyzing store performance data.

STORE PERFORMANCE SUMMARY ({start_date} to {end_date}):
- Total Unique Visitors: {analytics_data.total_unique_visitors or 0}
- Total Footfall: {analytics_data.total_footfall or 0}
- Average Dwell Time: {(analytics_data.avg_dwell_time or 0):.1f} seconds
- Active Cameras: {analytics_data.active_cameras or 0}

ANALYSIS REQUEST: {request.insight_type}

Provide comprehensive insights and 4-5 specific actionable recommendations for improving store performance.
"""
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional retail analytics consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        insights_text = response.choices[0].message.content
        
        # Generate recommendations
        recommendations_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Extract 4-5 specific actionable recommendations from this analysis as a JSON array:\n\n{insights_text}"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        try:
            recommendations = json.loads(recommendations_response.choices[0].message.content)
            if not isinstance(recommendations, list):
                recommendations = [recommendations_response.choices[0].message.content]
        except:
            recommendations = [
                "Optimize peak hour staffing based on traffic patterns",
                "Improve product placement in high-traffic zones", 
                "Enhance customer flow in underperforming areas",
                "Consider promotional strategies for low-traffic periods"
            ]
        
        return {
            "insights": insights_text,
            "recommendations": recommendations,
            "confidence_score": 85.0,
            "metrics_summary": {
                "total_visitors": analytics_data.total_unique_visitors or 0,
                "total_footfall": analytics_data.total_footfall or 0,
                "avg_dwell_time": float(analytics_data.avg_dwell_time or 0),
                "active_cameras": analytics_data.active_cameras or 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "insights": f"Error generating insights: {str(e)}",
            "recommendations": ["Check OpenAI API configuration"],
            "confidence_score": 0
        }

# Zone types endpoint
@app.get("/cameras/zone-types")
async def get_zone_types(db: Session = Depends(get_db)):
    """Get available retail zone types"""
    zones = db.query(ZoneType).all()
    
    return {
        "zone_types": {
            zone.zone_code: zone.display_name for zone in zones
        },
        "recommended_zones": [
            "entrance", "checkout", "dairy_section", "electronics", 
            "clothing", "grocery", "general"
        ],
        "detailed_zones": [
            {
                "code": zone.zone_code,
                "name": zone.display_name,
                "description": zone.description,
                "expected_dwell_time": zone.expected_dwell_time_seconds,
                "is_checkout": zone.is_checkout_zone,
                "is_entrance": zone.is_entrance_zone
            }
            for zone in zones
        ]
    }

# System status endpoint
@app.get("/api/system/status")
async def get_system_status(db: Session = Depends(get_db)):
    """Get comprehensive system status"""
    
    try:
        # Count total records
        total_users = db.query(User).count()
        total_cameras = db.query(Camera).count()
        total_visitors_today = db.query(Visitor).filter(Visitor.date == date.today()).count()
    except:
        total_users = total_cameras = total_visitors_today = 0
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "5.0.0",
        "environment": ENVIRONMENT,
        "database": "PostgreSQL with SQLAlchemy",
        "service_type": "api_only",
        "features": {
            "authentication": True,
            "camera_management": True,
            "analytics_api": True,
            "ai_insights": True,
            "promotional_analysis": True,
            "dashboard_metrics": True,
            "gpu_processing": "External worker service"
        },
        "statistics": {
            "total_users": total_users,
            "total_cameras": total_cameras,
            "visitors_today": total_visitors_today
        },
        "deployment": "DigitalOcean App Platform optimized"
    }

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    
    logger.info("🚀 Starting RetailIQ Analytics - Lightweight API")
    logger.info("📊 Database analytics and AI insights ready")
    logger.info("🎮 GPU processing handled by separate worker service")
    logger.info(f"🌐 Server starting on {args.host}:{args.port}")
    
    uvicorn.run(app, host=args.host, port=args.port, workers=1)