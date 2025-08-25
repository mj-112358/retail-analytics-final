-- RetailIQ Analytics Database Schema
-- Production-ready schema for stores, cameras, and analytics

-- Users and Stores
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    business_type VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Camera configurations
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    rtsp_url VARCHAR(500) NOT NULL,
    zone_type VARCHAR(100) NOT NULL, -- entrance, aisle, checkout, dairy, etc.
    location_description TEXT,
    is_active BOOLEAN DEFAULT 1,
    detection_settings JSON, -- Settings for detection algorithms
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE
);

-- Real-time detection events
CREATE TABLE IF NOT EXISTS detection_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    person_count INTEGER NOT NULL,
    frame_data BLOB, -- Optional: store frame for debugging
    confidence_scores JSON, -- Array of confidence scores
    bounding_boxes JSON, -- Array of bounding box coordinates
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

-- Visitor tracking (for unique visitor calculation)
CREATE TABLE IF NOT EXISTS visitor_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    visitor_id VARCHAR(100) NOT NULL, -- Generated unique ID
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    total_duration INTEGER NOT NULL, -- Duration in seconds
    zone_type VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

-- Hourly analytics aggregation
CREATE TABLE IF NOT EXISTS hourly_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    date DATE NOT NULL,
    hour INTEGER NOT NULL, -- 0-23
    total_visitors INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time REAL DEFAULT 0,
    peak_concurrent_visitors INTEGER DEFAULT 0,
    zone_type VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE,
    UNIQUE(camera_id, date, hour)
);

-- Daily analytics aggregation
CREATE TABLE IF NOT EXISTS daily_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_footfall INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time REAL DEFAULT 0,
    peak_hour INTEGER DEFAULT 0,
    peak_hour_count INTEGER DEFAULT 0,
    zone_analytics JSON, -- Per-zone breakdown
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE,
    UNIQUE(store_id, date)
);

-- Queue analytics (for checkout zones)
CREATE TABLE IF NOT EXISTS queue_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    queue_length INTEGER NOT NULL,
    estimated_wait_time REAL, -- In seconds
    service_time REAL, -- Average service time
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

-- Product interaction tracking
CREATE TABLE IF NOT EXISTS product_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    interaction_type VARCHAR(50), -- 'approach', 'pickup', 'putback'
    duration REAL, -- Duration of interaction
    product_area VARCHAR(100), -- Which area/product category
    visitor_id VARCHAR(100), -- Link to visitor session
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

-- Promotional campaigns
CREATE TABLE IF NOT EXISTS promotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    promotion_type VARCHAR(100), -- 'discount', 'festival', 'seasonal'
    target_zones JSON, -- Array of zone types
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE
);

-- AI-generated insights
CREATE TABLE IF NOT EXISTS ai_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    insight_type VARCHAR(100), -- 'general', 'promotional', 'festival'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    metrics_data JSON NOT NULL, -- Input metrics used for analysis
    insights_text TEXT NOT NULL, -- Generated insights
    recommendations JSON, -- Structured recommendations
    confidence_score REAL, -- AI confidence in insights
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE
);

-- System monitoring and health
CREATE TABLE IF NOT EXISTS system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'online', 'offline', 'error'
    last_detection_time DATETIME,
    error_message TEXT,
    fps REAL, -- Current processing FPS
    cpu_usage REAL,
    memory_usage REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_detection_events_camera_timestamp 
ON detection_events(camera_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_visitor_sessions_camera_zone 
ON visitor_sessions(camera_id, zone_type);

CREATE INDEX IF NOT EXISTS idx_hourly_analytics_camera_date 
ON hourly_analytics(camera_id, date);

CREATE INDEX IF NOT EXISTS idx_daily_analytics_store_date 
ON daily_analytics(store_id, date);

CREATE INDEX IF NOT EXISTS idx_queue_analytics_camera_timestamp 
ON queue_analytics(camera_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_product_interactions_camera_timestamp 
ON product_interactions(camera_id, timestamp);

-- Initial data
INSERT OR IGNORE INTO stores (id, name, email, password_hash, business_type) 
VALUES (1, 'Demo Store', 'demo@retailiq.com', '$2b$12$LQv3c1yqBwfVSNHc3XqcE.0P7s2wGKp4PKw4QdJ9Z2B9ZGJz5g6K6', 'retail');