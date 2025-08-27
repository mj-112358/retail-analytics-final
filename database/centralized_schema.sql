-- Centralized Multi-Tenant Database Schema
-- Supports multiple client stores with centralized analytics

-- Companies/Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subscription_plan TEXT DEFAULT 'basic',
    api_key TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Stores table (updated for multi-tenant)
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER REFERENCES organizations(id),
    store_identifier TEXT NOT NULL, -- Client's own store ID
    name TEXT NOT NULL,
    location TEXT,
    timezone TEXT DEFAULT 'UTC',
    business_hours_start INTEGER DEFAULT 9,
    business_hours_end INTEGER DEFAULT 21,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(organization_id, store_identifier)
);

-- Users table (updated for multi-tenant)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER REFERENCES organizations(id),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'manager', -- 'admin', 'manager', 'viewer'
    store_access TEXT, -- JSON array of store IDs user can access
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Cameras table (updated for centralized architecture)
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES stores(id),
    camera_identifier INTEGER NOT NULL, -- Client's camera number
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    location_description TEXT,
    
    -- Centralized stream info
    media_server_path TEXT, -- store_123_camera_1
    media_server_ip TEXT DEFAULT 'localhost',
    media_server_port INTEGER DEFAULT 8554,
    
    -- Client publishing info
    client_publish_instructions TEXT, -- Instructions for client
    
    status TEXT DEFAULT 'offline',
    features TEXT DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_detection_at TIMESTAMP,
    
    UNIQUE(store_id, camera_identifier)
);

-- Real-time detections table (optimized for high volume)
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES stores(id),
    camera_id INTEGER REFERENCES cameras(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    people_count INTEGER NOT NULL DEFAULT 0,
    zone_type TEXT,
    confidence_score REAL,
    processing_time_ms INTEGER,
    
    -- Indexed for fast queries
    hour INTEGER, -- 0-23
    day_of_week INTEGER, -- 0-6 (Monday=0)
    is_weekend BOOLEAN,
    date_only DATE
);

-- Hourly aggregations (for faster dashboard queries)
CREATE TABLE IF NOT EXISTS hourly_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES stores(id),
    camera_id INTEGER REFERENCES cameras(id),
    date_hour TEXT, -- '2024-08-26 14:00'
    zone_type TEXT,
    
    total_detections INTEGER DEFAULT 0,
    max_people INTEGER DEFAULT 0,
    avg_people REAL DEFAULT 0.0,
    unique_sessions INTEGER DEFAULT 0,
    total_dwell_time_seconds INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, camera_id, date_hour)
);

-- Daily summaries
CREATE TABLE IF NOT EXISTS daily_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES stores(id),
    date_only DATE,
    
    total_footfall INTEGER DEFAULT 0,
    peak_hour INTEGER,
    peak_people_count INTEGER DEFAULT 0,
    avg_dwell_time_minutes REAL DEFAULT 0.0,
    total_zones_active INTEGER DEFAULT 0,
    busiest_zone TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, date_only)
);

-- AI Insights (centralized across all stores)
CREATE TABLE IF NOT EXISTS ai_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER REFERENCES organizations(id),
    store_id INTEGER REFERENCES stores(id), -- NULL for org-wide insights
    insight_type TEXT NOT NULL, -- 'daily', 'weekly', 'promo', 'comparative'
    
    period_start DATE,
    period_end DATE,
    
    insights_text TEXT NOT NULL,
    metrics_analyzed TEXT, -- JSON of metrics used
    recommendations TEXT, -- JSON array of recommendations
    
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by TEXT DEFAULT 'openai-gpt'
);

-- Stream publishing status (for monitoring client connections)
CREATE TABLE IF NOT EXISTS stream_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER REFERENCES stores(id),
    camera_id INTEGER REFERENCES cameras(id),
    
    is_publishing BOOLEAN DEFAULT FALSE,
    last_frame_received TIMESTAMP,
    connection_quality TEXT, -- 'excellent', 'good', 'poor', 'disconnected'
    frames_per_second REAL,
    bandwidth_mbps REAL,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_detections_store_time ON detections(store_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_detections_camera_time ON detections(camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_detections_date_hour ON detections(date_only, hour);
CREATE INDEX IF NOT EXISTS idx_hourly_store_date ON hourly_analytics(store_id, date_hour DESC);
CREATE INDEX IF NOT EXISTS idx_daily_store_date ON daily_analytics(store_id, date_only DESC);
CREATE INDEX IF NOT EXISTS idx_cameras_store ON cameras(store_id);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

-- Views for common queries
CREATE VIEW IF NOT EXISTS store_overview AS
SELECT 
    s.id,
    s.store_identifier,
    s.name,
    s.location,
    o.name as organization_name,
    COUNT(c.id) as total_cameras,
    COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_cameras,
    s.created_at
FROM stores s
JOIN organizations o ON s.organization_id = o.id
LEFT JOIN cameras c ON s.id = c.store_id
GROUP BY s.id;

CREATE VIEW IF NOT EXISTS live_camera_status AS
SELECT 
    c.id,
    c.name,
    c.zone_type,
    s.store_identifier,
    s.name as store_name,
    c.status,
    ss.is_publishing,
    ss.last_frame_received,
    ss.connection_quality,
    c.media_server_path
FROM cameras c
JOIN stores s ON c.store_id = s.id
LEFT JOIN stream_status ss ON c.id = ss.camera_id;

-- Sample data for testing
INSERT OR IGNORE INTO organizations (name, subscription_plan, api_key) VALUES 
('Demo Retail Chain', 'premium', 'demo_api_key_12345'),
('Local Grocery Co', 'basic', 'local_api_key_67890');

INSERT OR IGNORE INTO stores (organization_id, store_identifier, name, location) VALUES 
(1, 'store_001', 'Downtown Flagship', 'Downtown Mall, NY'),
(1, 'store_002', 'Suburban Branch', 'Westfield Plaza, CA'),
(2, 'store_101', 'Main Street Grocery', 'Main Street, TX');