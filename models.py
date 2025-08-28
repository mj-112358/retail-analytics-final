"""
SQLAlchemy Database Models for RetailIQ Analytics
Comprehensive models for all retail analytics features
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid as uuid_pkg

from database import Base

class User(Base):
    """User accounts - store owners/managers"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store_name = Column(String, nullable=False)
    phone = Column(String)
    subscription_tier = Column(String, default='basic')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    stores = relationship("Store", back_populates="user", cascade="all, delete-orphan")

class Store(Base):
    """Individual store locations"""
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(Text)
    store_type = Column(String, default='retail')
    timezone = Column(String, default='UTC')
    operating_hours = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="stores")
    cameras = relationship("Camera", back_populates="store", cascade="all, delete-orphan")
    daily_analytics = relationship("DailyAnalytics", back_populates="store", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="store", cascade="all, delete-orphan")

class ZoneType(Base):
    """Predefined zone types for retail analytics"""
    __tablename__ = "zone_types"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text)
    expected_dwell_time_seconds = Column(Integer, default=120)
    is_checkout_zone = Column(Boolean, default=False)
    is_entrance_zone = Column(Boolean, default=False)
    
    # Relationships
    cameras = relationship("Camera", back_populates="zone_type")

class Camera(Base):
    """RTSP camera configurations"""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    zone_type_id = Column(Integer, ForeignKey("zone_types.id"))
    location_description = Column(Text)
    resolution = Column(String, default='1920x1080')
    fps = Column(Integer, default=30)
    detection_enabled = Column(Boolean, default=True)
    recording_enabled = Column(Boolean, default=False)
    status = Column(String, default='offline')  # offline, online, error, starting
    last_detection_at = Column(DateTime)
    last_heartbeat_at = Column(DateTime)
    configuration = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    store = relationship("Store", back_populates="cameras")
    zone_type = relationship("ZoneType", back_populates="cameras")
    visitors = relationship("Visitor", back_populates="camera", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="camera", cascade="all, delete-orphan")
    queue_events = relationship("QueueEvent", back_populates="camera", cascade="all, delete-orphan")

class DetectionSession(Base):
    """Track RTSP processing sessions"""
    __tablename__ = "detection_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    session_uuid = Column(UUID(as_uuid=True), default=uuid_pkg.uuid4)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime)
    frames_processed = Column(Integer, default=0)
    detections_count = Column(Integer, default=0)
    status = Column(String, default='active')  # active, completed, error, stopped
    error_message = Column(Text)

class Visitor(Base):
    """Individual visitor tracking with dwell time analysis"""
    __tablename__ = "visitors"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    visitor_uuid = Column(UUID(as_uuid=True), default=uuid_pkg.uuid4)
    session_id = Column(Integer, ForeignKey("detection_sessions.id"))
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    total_dwell_time_seconds = Column(Integer, default=0)
    zone_type_id = Column(Integer, ForeignKey("zone_types.id"))
    confidence_score = Column(Float, default=0.0)
    is_unique = Column(Boolean, default=True)
    tracking_data = Column(JSON, default=dict)  # bbox history, movement path
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="visitors")
    product_interactions = relationship("ProductInteraction", back_populates="visitor", cascade="all, delete-orphan")

class Detection(Base):
    """Individual object detections from YOLO"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    visitor_id = Column(Integer, ForeignKey("visitors.id"))
    detection_time = Column(DateTime, nullable=False)
    object_class = Column(String, default='person')
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float)
    bbox_y1 = Column(Float)
    bbox_x2 = Column(Float)
    bbox_y2 = Column(Float)
    tracking_id = Column(Integer)
    frame_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="detections")

class HourlyAnalytics(Base):
    """Hourly aggregated metrics per camera/zone"""
    __tablename__ = "hourly_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    zone_type_id = Column(Integer, ForeignKey("zone_types.id"))
    date = Column(Date, nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23
    total_visitors = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_dwell_time_seconds = Column(Float, default=0)
    peak_occupancy = Column(Integer, default=0)
    total_detections = Column(Integer, default=0)
    queue_events = Column(Integer, default=0)
    product_interactions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DailyAnalytics(Base):
    """Daily aggregated metrics per store"""
    __tablename__ = "daily_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_footfall = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_dwell_time_seconds = Column(Float, default=0)
    peak_hour = Column(Integer)
    peak_hour_visitors = Column(Integer, default=0)
    total_zones_active = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0)
    revenue = Column(Float, default=0)
    weather_condition = Column(String)
    special_events = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    store = relationship("Store", back_populates="daily_analytics")

class QueueEvent(Base):
    """Checkout and service queue monitoring"""
    __tablename__ = "queue_events"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    zone_type_id = Column(Integer, ForeignKey("zone_types.id"))
    timestamp = Column(DateTime, nullable=False)
    queue_length = Column(Integer, nullable=False)
    estimated_wait_time_seconds = Column(Float)
    avg_service_time_seconds = Column(Float)
    queue_abandoned_count = Column(Integer, default=0)
    staff_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="queue_events")

class ProductInteraction(Base):
    """Detailed customer-product interaction tracking"""
    __tablename__ = "product_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    interaction_type = Column(String)  # pickup, examine, return, purchase_intent
    product_area = Column(String)
    shelf_section = Column(String)
    duration_seconds = Column(Integer)
    interaction_intensity = Column(Float, default=1.0)  # 1.0 = normal, >1.0 = high interest
    bbox_data = Column(JSON)  # bounding box of interaction area
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    visitor = relationship("Visitor", back_populates="product_interactions")

class Promotion(Base):
    """Marketing campaigns and events tracking"""
    __tablename__ = "promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    promotion_type = Column(String)  # discount, bogo, seasonal, festival
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    target_zones = Column(ARRAY(String))  # array of zone codes
    discount_percentage = Column(Float)
    expected_impact_percentage = Column(Float)
    actual_impact_percentage = Column(Float)
    budget = Column(Float)
    roi = Column(Float)
    status = Column(String, default='planned')  # planned, active, completed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    store = relationship("Store", back_populates="promotions")

class AIInsight(Base):
    """OpenAI generated insights and recommendations"""
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    insight_type = Column(String, nullable=False)  # general, promo_effectiveness, festival_spike
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    metrics_summary = Column(JSON)
    insights_text = Column(Text, nullable=False)
    recommendations = Column(ARRAY(String))
    key_findings = Column(ARRAY(String))
    confidence_score = Column(Float, default=0.0)
    effectiveness_score = Column(Float)
    generated_by = Column(String, default='openai-gpt-4')
    prompt_version = Column(String, default='v1.0')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class HeatmapData(Base):
    """Zone popularity and traffic patterns"""
    __tablename__ = "heatmap_data"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    zone_type_id = Column(Integer, ForeignKey("zone_types.id"))
    date = Column(Date, nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23
    grid_x = Column(Integer, nullable=False)  # heat map grid coordinates
    grid_y = Column(Integer, nullable=False)
    visitor_count = Column(Integer, default=0)
    avg_dwell_time_seconds = Column(Float, default=0)
    total_interactions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SystemAlert(Base):
    """Automated notifications and alerts"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    alert_type = Column(String, nullable=False)  # queue_buildup, camera_offline, unusual_activity
    severity = Column(String, default='medium')  # low, medium, high, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    alert_data = Column(JSON, default=dict)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)