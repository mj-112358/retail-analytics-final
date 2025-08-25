-- FINAL PRODUCTION DATABASE SCHEMA
-- Complete retail analytics system for real customers

-- Users/Store Owners table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_expires_at TIMESTAMP
);

-- Stores table (one user can have multiple stores)
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    business_hours JSONB, -- {"open": "09:00", "close": "21:00", "days": ["mon", "tue", ...]}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cameras table
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- "Floor 1 - Dairy Section"
    rtsp_url VARCHAR(500) NOT NULL,
    location_description TEXT, -- "Near entrance, facing dairy products"
    zone_type VARCHAR(100) NOT NULL, -- "entrance", "checkout", "dairy", "electronics", etc.
    is_active BOOLEAN DEFAULT true,
    last_detection_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'offline', -- "online", "offline", "error"
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Camera settings
    detection_sensitivity FLOAT DEFAULT 0.5,
    person_threshold FLOAT DEFAULT 0.7,
    tracking_enabled BOOLEAN DEFAULT true
);

-- Visitors tracking (unique person detection)
CREATE TABLE IF NOT EXISTS visitors (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    visitor_uuid VARCHAR(100) NOT NULL, -- Unique identifier for tracking
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    total_dwell_time_seconds INTEGER DEFAULT 0,
    zone_type VARCHAR(100),
    date DATE NOT NULL,
    
    -- Tracking data
    entry_point VARCHAR(100),
    exit_point VARCHAR(100),
    path_data JSONB, -- Store movement path if available
    
    UNIQUE(visitor_uuid, camera_id, date)
);

-- Hourly analytics aggregation
CREATE TABLE IF NOT EXISTS hourly_analytics (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hour INTEGER NOT NULL, -- 0-23
    zone_type VARCHAR(100),
    
    -- Core metrics
    total_visitors INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time_seconds FLOAT DEFAULT 0,
    peak_occupancy INTEGER DEFAULT 0,
    
    -- Advanced metrics
    queue_wait_time_avg_seconds FLOAT DEFAULT 0,
    product_interactions INTEGER DEFAULT 0,
    conversion_events INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, camera_id, date, hour)
);

-- Daily analytics aggregation
CREATE TABLE IF NOT EXISTS daily_analytics (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Combined store metrics
    total_footfall INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time_seconds FLOAT DEFAULT 0,
    peak_hour INTEGER, -- 0-23
    peak_hour_visitors INTEGER DEFAULT 0,
    
    -- Zone-wise breakdown
    zone_metrics JSONB, -- {"entrance": {"visitors": 100, "dwell_time": 120}, ...}
    
    -- Queue and interaction metrics
    avg_queue_wait_time_seconds FLOAT DEFAULT 0,
    total_product_interactions INTEGER DEFAULT 0,
    conversion_rate FLOAT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, date)
);

-- Queue detection events
CREATE TABLE IF NOT EXISTS queue_events (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    queue_length INTEGER NOT NULL,
    avg_wait_time_seconds FLOAT,
    zone_type VARCHAR(100)
);

-- Product interaction events
CREATE TABLE IF NOT EXISTS product_interactions (
    id SERIAL PRIMARY KEY,
    visitor_uuid VARCHAR(100),
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    interaction_type VARCHAR(100), -- "pick_up", "examine", "return", "purchase"
    product_area VARCHAR(255),
    duration_seconds INTEGER
);

-- Promotions and campaigns
CREATE TABLE IF NOT EXISTS promotions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    promotion_type VARCHAR(100), -- "discount", "festival", "seasonal", "clearance"
    target_zones JSONB, -- ["electronics", "clothing"] 
    expected_impact_percentage FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Insights generated
CREATE TABLE IF NOT EXISTS ai_insights (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL, -- "weekly", "monthly", "promo_effectiveness", "festival_analysis"
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Input data summary
    metrics_summary JSONB, -- All the metrics that were sent to OpenAI
    
    -- AI Generated insights
    insights_text TEXT NOT NULL,
    recommendations JSONB, -- Structured recommendations
    confidence_score FLOAT,
    
    -- Promotion/Festival specific
    promotion_id INTEGER REFERENCES promotions(id),
    effectiveness_score FLOAT, -- For promo analysis
    
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System logs and monitoring
CREATE TABLE IF NOT EXISTS detection_logs (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100), -- "detection_started", "error", "person_detected", etc.
    details JSONB,
    processing_time_ms INTEGER
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_visitors_date ON visitors(date);
CREATE INDEX IF NOT EXISTS idx_visitors_store_date ON visitors(store_id, date);
CREATE INDEX IF NOT EXISTS idx_hourly_analytics_store_date ON hourly_analytics(store_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_store_date ON daily_analytics(store_id, date);
CREATE INDEX IF NOT EXISTS idx_queue_events_timestamp ON queue_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_product_interactions_timestamp ON product_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_cameras_store_active ON cameras(store_id, is_active);

-- Views for common queries
CREATE OR REPLACE VIEW store_dashboard_summary AS
SELECT 
    s.id as store_id,
    s.name as store_name,
    COUNT(DISTINCT c.id) as total_cameras,
    COUNT(DISTINCT CASE WHEN c.status = 'online' THEN c.id END) as active_cameras,
    COALESCE(da.total_footfall, 0) as today_footfall,
    COALESCE(da.unique_visitors, 0) as today_unique_visitors,
    COALESCE(da.peak_hour, 0) as today_peak_hour
FROM stores s
LEFT JOIN cameras c ON s.id = c.store_id
LEFT JOIN daily_analytics da ON s.id = da.store_id AND da.date = CURRENT_DATE
GROUP BY s.id, s.name, da.total_footfall, da.unique_visitors, da.peak_hour;

-- Function to update daily analytics
CREATE OR REPLACE FUNCTION update_daily_analytics(store_id_param INTEGER, date_param DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_analytics (
        store_id, date, total_footfall, unique_visitors, avg_dwell_time_seconds,
        peak_hour, peak_hour_visitors
    )
    SELECT 
        store_id_param,
        date_param,
        SUM(total_visitors) as total_footfall,
        COUNT(DISTINCT visitor_uuid) as unique_visitors,
        AVG(total_dwell_time_seconds) as avg_dwell_time_seconds,
        (SELECT hour FROM hourly_analytics 
         WHERE store_id = store_id_param AND date = date_param 
         ORDER BY total_visitors DESC LIMIT 1) as peak_hour,
        MAX(total_visitors) as peak_hour_visitors
    FROM (
        SELECT ha.total_visitors, v.visitor_uuid, v.total_dwell_time_seconds, ha.hour
        FROM hourly_analytics ha
        LEFT JOIN visitors v ON ha.camera_id = v.camera_id AND ha.date = v.date
        WHERE ha.store_id = store_id_param AND ha.date = date_param
    ) combined_data
    ON CONFLICT (store_id, date) 
    DO UPDATE SET
        total_footfall = EXCLUDED.total_footfall,
        unique_visitors = EXCLUDED.unique_visitors,
        avg_dwell_time_seconds = EXCLUDED.avg_dwell_time_seconds,
        peak_hour = EXCLUDED.peak_hour,
        peak_hour_visitors = EXCLUDED.peak_hour_visitors;
END;
$$ LANGUAGE plpgsql;