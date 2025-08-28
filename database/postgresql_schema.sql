-- COMPREHENSIVE RETAIL ANALYTICS DATABASE SCHEMA
-- Production-ready PostgreSQL schema with all detection features
-- Supports multiple stores, cameras, zones, and advanced analytics

-- Connect to your database using provided connection details
-- Create main database
CREATE DATABASE retail_analytics;

-- Connect to the database
\c retail_analytics;

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table - Store owners/managers
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stores table - Individual store locations
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    store_type VARCHAR(100) DEFAULT 'retail',
    timezone VARCHAR(50) DEFAULT 'UTC',
    operating_hours JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zone types lookup table
CREATE TABLE zone_types (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    expected_dwell_time_seconds INTEGER DEFAULT 120,
    is_checkout_zone BOOLEAN DEFAULT false,
    is_entrance_zone BOOLEAN DEFAULT false
);

-- Insert default zone types
INSERT INTO zone_types (zone_code, display_name, description, expected_dwell_time_seconds, is_checkout_zone, is_entrance_zone) VALUES
('entrance', 'Store Entrance/Exit', 'Main entry and exit points', 30, false, true),
('checkout', 'Checkout/Payment Area', 'Cashier and self-checkout areas', 180, true, false),
('dairy_section', 'Dairy Section', 'Milk, cheese, and dairy products', 120, false, false),
('electronics', 'Electronics Department', 'TVs, phones, computers', 300, false, false),
('clothing', 'Clothing Department', 'Apparel and fashion items', 240, false, false),
('grocery', 'Grocery Aisles', 'Food and household items', 90, false, false),
('pharmacy', 'Pharmacy Counter', 'Medicine and health products', 150, false, false),
('customer_service', 'Customer Service Area', 'Help desk and returns', 600, false, false),
('general', 'General Store Area', 'Mixed merchandise area', 120, false, false),
('bakery', 'Bakery Section', 'Fresh bread and baked goods', 100, false, false),
('produce', 'Produce Section', 'Fresh fruits and vegetables', 150, false, false),
('deli', 'Deli Counter', 'Fresh meat and prepared foods', 200, false, false);

-- Cameras table - RTSP camera configurations
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    rtsp_url VARCHAR(1000) NOT NULL,
    zone_type_id INTEGER REFERENCES zone_types(id),
    location_description TEXT,
    resolution VARCHAR(20) DEFAULT '1920x1080',
    fps INTEGER DEFAULT 30,
    detection_enabled BOOLEAN DEFAULT true,
    recording_enabled BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'offline', -- offline, online, error, starting
    last_detection_at TIMESTAMP,
    last_heartbeat_at TIMESTAMP,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detection sessions table - Track processing sessions
CREATE TABLE detection_sessions (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    session_uuid UUID DEFAULT uuid_generate_v4(),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    frames_processed INTEGER DEFAULT 0,
    detections_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, error, stopped
    error_message TEXT
);

-- Visitors table - Individual visitor tracking
CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    visitor_uuid UUID DEFAULT uuid_generate_v4(),
    session_id INTEGER REFERENCES detection_sessions(id),
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    total_dwell_time_seconds INTEGER DEFAULT 0,
    zone_type_id INTEGER REFERENCES zone_types(id),
    confidence_score FLOAT DEFAULT 0.0,
    is_unique BOOLEAN DEFAULT true,
    tracking_data JSONB DEFAULT '{}', -- bbox history, movement path
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detections table - Individual object detections
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    visitor_id INTEGER REFERENCES visitors(id) ON DELETE SET NULL,
    detection_time TIMESTAMP NOT NULL,
    object_class VARCHAR(50) NOT NULL DEFAULT 'person',
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT,
    bbox_y1 FLOAT,
    bbox_x2 FLOAT,
    bbox_y2 FLOAT,
    tracking_id INTEGER,
    frame_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hourly analytics table - Aggregated hourly metrics
CREATE TABLE hourly_analytics (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    zone_type_id INTEGER REFERENCES zone_types(id),
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    total_visitors INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time_seconds FLOAT DEFAULT 0,
    peak_occupancy INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    queue_events INTEGER DEFAULT 0,
    product_interactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, camera_id, zone_type_id, date, hour)
);

-- Daily analytics table - Aggregated daily metrics per store
CREATE TABLE daily_analytics (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_footfall INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_dwell_time_seconds FLOAT DEFAULT 0,
    peak_hour INTEGER,
    peak_hour_visitors INTEGER DEFAULT 0,
    total_zones_active INTEGER DEFAULT 0,
    conversion_rate FLOAT DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    weather_condition VARCHAR(100),
    special_events TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, date)
);

-- Queue events table - Checkout and service queue monitoring
CREATE TABLE queue_events (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    zone_type_id INTEGER REFERENCES zone_types(id),
    timestamp TIMESTAMP NOT NULL,
    queue_length INTEGER NOT NULL,
    estimated_wait_time_seconds FLOAT,
    avg_service_time_seconds FLOAT,
    queue_abandoned_count INTEGER DEFAULT 0,
    staff_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product interactions table - Detailed interaction tracking
CREATE TABLE product_interactions (
    id SERIAL PRIMARY KEY,
    visitor_id INTEGER REFERENCES visitors(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    interaction_type VARCHAR(100), -- pickup, examine, return, purchase_intent
    product_area VARCHAR(255),
    shelf_section VARCHAR(255),
    duration_seconds INTEGER,
    interaction_intensity FLOAT DEFAULT 1.0, -- 1.0 = normal, >1.0 = high interest
    bbox_data JSONB, -- bounding box of interaction area
    confidence_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Promotions table - Marketing campaigns and events
CREATE TABLE promotions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    promotion_type VARCHAR(100), -- discount, bogo, seasonal, festival
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_zones TEXT[], -- array of zone codes
    discount_percentage FLOAT,
    expected_impact_percentage FLOAT,
    actual_impact_percentage FLOAT,
    budget DECIMAL(10,2),
    roi DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'planned', -- planned, active, completed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI insights table - OpenAI generated insights and recommendations
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL, -- general, promo_effectiveness, festival_spike, optimization
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    metrics_summary JSONB,
    insights_text TEXT NOT NULL,
    recommendations TEXT[],
    key_findings TEXT[],
    confidence_score FLOAT DEFAULT 0.0,
    effectiveness_score FLOAT,
    generated_by VARCHAR(100) DEFAULT 'openai-gpt-4',
    prompt_version VARCHAR(50) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Heat map data table - Zone popularity and traffic patterns
CREATE TABLE heatmap_data (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    zone_type_id INTEGER REFERENCES zone_types(id),
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    grid_x INTEGER NOT NULL, -- heat map grid coordinates
    grid_y INTEGER NOT NULL,
    visitor_count INTEGER DEFAULT 0,
    avg_dwell_time_seconds FLOAT DEFAULT 0,
    total_interactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id, date, hour, grid_x, grid_y)
);

-- Staff scheduling table - Optimize staffing based on analytics
CREATE TABLE staff_schedules (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    zone_type_id INTEGER REFERENCES zone_types(id),
    required_staff INTEGER DEFAULT 1,
    actual_staff INTEGER DEFAULT 0,
    predicted_visitors INTEGER DEFAULT 0,
    efficiency_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, date, hour, zone_type_id)
);

-- System alerts table - Automated notifications and alerts
CREATE TABLE system_alerts (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE SET NULL,
    alert_type VARCHAR(100) NOT NULL, -- queue_buildup, camera_offline, unusual_activity
    severity VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    alert_data JSONB DEFAULT '{}',
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table - System and camera performance tracking
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fps_actual FLOAT,
    detection_latency_ms FLOAT,
    memory_usage_mb FLOAT,
    cpu_usage_percent FLOAT,
    frames_dropped INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    uptime_seconds INTEGER DEFAULT 0
);

-- Create indexes for better query performance
CREATE INDEX idx_visitors_store_date ON visitors(store_id, date);
CREATE INDEX idx_visitors_camera_date ON visitors(camera_id, date);
CREATE INDEX idx_detections_camera_time ON detections(camera_id, detection_time);
CREATE INDEX idx_hourly_analytics_store_date ON hourly_analytics(store_id, date);
CREATE INDEX idx_daily_analytics_store_date ON daily_analytics(store_id, date);
CREATE INDEX idx_queue_events_camera_timestamp ON queue_events(camera_id, timestamp);
CREATE INDEX idx_product_interactions_timestamp ON product_interactions(timestamp);
CREATE INDEX idx_ai_insights_store_type ON ai_insights(store_id, insight_type);
CREATE INDEX idx_promotions_store_dates ON promotions(store_id, start_date, end_date);
CREATE INDEX idx_cameras_store_active ON cameras(store_id, is_active);
CREATE INDEX idx_visitors_uuid_date ON visitors(visitor_uuid, date);
CREATE INDEX idx_heatmap_camera_date_hour ON heatmap_data(camera_id, date, hour);

-- Create triggers to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stores_updated_at BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_analytics_updated_at BEFORE UPDATE ON daily_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promotions_updated_at BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW camera_status_summary AS
SELECT 
    s.name as store_name,
    c.name as camera_name,
    zt.display_name as zone_name,
    c.status,
    c.last_detection_at,
    c.last_heartbeat_at,
    COUNT(v.id) as total_visitors_today
FROM cameras c
JOIN stores s ON c.store_id = s.id
LEFT JOIN zone_types zt ON c.zone_type_id = zt.id
LEFT JOIN visitors v ON c.id = v.camera_id AND v.date = CURRENT_DATE
GROUP BY s.name, c.name, zt.display_name, c.status, c.last_detection_at, c.last_heartbeat_at;

CREATE VIEW daily_store_summary AS
SELECT 
    s.name as store_name,
    da.date,
    da.total_footfall,
    da.unique_visitors,
    ROUND(da.avg_dwell_time_seconds / 60.0, 2) as avg_dwell_time_minutes,
    da.peak_hour,
    da.peak_hour_visitors,
    da.conversion_rate
FROM daily_analytics da
JOIN stores s ON da.store_id = s.id
ORDER BY da.date DESC;

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Insert sample data (optional - remove in production)
-- INSERT INTO users (email, password_hash, name, store_name) VALUES 
-- ('demo@retailiq.com', '$2b$12$example_hash', 'Demo User', 'Demo Retail Store');

COMMENT ON DATABASE retail_analytics IS 'Comprehensive retail analytics system with computer vision and AI insights';
COMMENT ON TABLE visitors IS 'Individual visitor tracking with dwell time and zone analytics';
COMMENT ON TABLE detections IS 'Raw object detection data from YOLO model';
COMMENT ON TABLE hourly_analytics IS 'Aggregated hourly metrics per camera/zone';
COMMENT ON TABLE daily_analytics IS 'Daily store-wide analytics and KPIs';
COMMENT ON TABLE ai_insights IS 'OpenAI generated insights and recommendations';
COMMENT ON TABLE promotions IS 'Marketing campaigns with effectiveness tracking';
COMMENT ON TABLE queue_events IS 'Queue monitoring for checkout optimization';
COMMENT ON TABLE product_interactions IS 'Detailed customer-product interaction tracking';