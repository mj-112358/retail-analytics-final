"""
Database models for RetailIQ Analytics System
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
import json


class Store(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    password_hash: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    business_type: Optional[str] = "retail"
    timezone: str = "UTC"
    subscription_plan: str = "basic"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


class Camera(BaseModel):
    id: Optional[int] = None
    store_id: int
    name: str
    rtsp_url: str
    zone_type: str  # entrance, aisle, checkout, dairy, etc.
    location_description: Optional[str] = None
    is_active: bool = True
    detection_settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DetectionEvent(BaseModel):
    id: Optional[int] = None
    camera_id: int
    timestamp: datetime
    person_count: int
    frame_data: Optional[bytes] = None
    confidence_scores: Optional[List[float]] = None
    bounding_boxes: Optional[List[List[int]]] = None
    created_at: Optional[datetime] = None


class VisitorSession(BaseModel):
    id: Optional[int] = None
    camera_id: int
    visitor_id: str
    first_seen: datetime
    last_seen: datetime
    total_duration: int  # seconds
    zone_type: str
    created_at: Optional[datetime] = None


class HourlyAnalytics(BaseModel):
    id: Optional[int] = None
    camera_id: int
    date: str
    hour: int  # 0-23
    total_visitors: int = 0
    unique_visitors: int = 0
    avg_dwell_time: float = 0.0
    peak_concurrent_visitors: int = 0
    zone_type: str
    created_at: Optional[datetime] = None


class DailyAnalytics(BaseModel):
    id: Optional[int] = None
    store_id: int
    date: str
    total_footfall: int = 0
    unique_visitors: int = 0
    avg_dwell_time: float = 0.0
    peak_hour: int = 0
    peak_hour_count: int = 0
    zone_analytics: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class QueueAnalytics(BaseModel):
    id: Optional[int] = None
    camera_id: int
    timestamp: datetime
    queue_length: int
    estimated_wait_time: Optional[float] = None
    service_time: Optional[float] = None
    created_at: Optional[datetime] = None


class ProductInteraction(BaseModel):
    id: Optional[int] = None
    camera_id: int
    timestamp: datetime
    interaction_type: str  # 'approach', 'pickup', 'putback'
    duration: Optional[float] = None
    product_area: str
    visitor_id: str
    created_at: Optional[datetime] = None


class Promotion(BaseModel):
    id: Optional[int] = None
    store_id: int
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    promotion_type: str  # 'discount', 'festival', 'seasonal'
    target_zones: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class AIInsight(BaseModel):
    id: Optional[int] = None
    store_id: int
    insight_type: str  # 'general', 'promotional', 'festival'
    period_start: str
    period_end: str
    metrics_data: Dict[str, Any]
    insights_text: str
    recommendations: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None


class SystemHealth(BaseModel):
    id: Optional[int] = None
    camera_id: int
    status: str  # 'online', 'offline', 'error'
    last_detection_time: Optional[datetime] = None
    error_message: Optional[str] = None
    fps: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    created_at: Optional[datetime] = None


# Request/Response models
class StoreCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    business_type: Optional[str] = "retail"


class StoreLogin(BaseModel):
    email: EmailStr
    password: str


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    zone_type: str
    location_description: Optional[str] = None
    detection_settings: Optional[Dict[str, Any]] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    zone_type: Optional[str] = None
    location_description: Optional[str] = None
    is_active: Optional[bool] = None
    detection_settings: Optional[Dict[str, Any]] = None


class InsightRequest(BaseModel):
    period_start: str
    period_end: str
    insight_type: str = "general"
    include_promo: bool = False
    promo_start: Optional[str] = None
    promo_end: Optional[str] = None


class DashboardMetrics(BaseModel):
    live_visitors: int
    total_footfall_today: int
    unique_visitors_today: int
    avg_dwell_time: float
    peak_hour: int
    peak_hour_count: int
    hourly_counts: Dict[str, int]
    zone_breakdown: Dict[str, Dict[str, Any]]
    queue_status: List[Dict[str, Any]]
    camera_health: List[Dict[str, Any]]


class AnalyticsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None