"""
Database connection and management for RetailIQ Analytics
Supports both SQLite (development) and PostgreSQL (production)
"""
import sqlite3
import os
import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
import bcrypt
from database.models import *

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "retailiq.db", auto_init: bool = True):
        # Check if we should use PostgreSQL
        database_url = os.getenv("DATABASE_URL")
        if database_url and database_url.startswith("postgresql://"):
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")
            self.use_postgres = True
            self.database_url = database_url
            logger.info("Using PostgreSQL database")
        else:
            self.use_postgres = False
            self.db_path = db_path
            logger.info(f"Using SQLite database: {db_path}")
        
        if auto_init:
            self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
            else:
                logger.error(f"Schema file not found: {schema_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _dict_from_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary"""
        return {key: row[key] for key in row.keys()}
    
    # Store management
    def create_store(self, store_data: StoreCreate) -> Optional[int]:
        """Create a new store"""
        password_hash = bcrypt.hashpw(store_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(
                    """INSERT INTO stores (name, email, password_hash, phone, address, business_type)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (store_data.name, store_data.email, password_hash, 
                     store_data.phone, store_data.address, store_data.business_type)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    
    def authenticate_store(self, email: str, password: str) -> Optional[Store]:
        """Authenticate store login"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stores WHERE email = ? AND is_active = 1",
                (email,)
            )
            row = cursor.fetchone()
            
            if row and bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
                return Store(**self._dict_from_row(row))
            return None
    
    def get_store(self, store_id: int) -> Optional[Store]:
        """Get store by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stores WHERE id = ? AND is_active = 1",
                (store_id,)
            )
            row = cursor.fetchone()
            return Store(**self._dict_from_row(row)) if row else None
    
    # Camera management
    def create_camera(self, camera_data: CameraCreate, store_id: int) -> Optional[int]:
        """Create a new camera"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO cameras (store_id, name, rtsp_url, zone_type, location_description, detection_settings)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (store_id, camera_data.name, camera_data.rtsp_url, camera_data.zone_type,
                 camera_data.location_description, json.dumps(camera_data.detection_settings))
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_cameras(self, store_id: int) -> List[Camera]:
        """Get all cameras for a store"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras WHERE store_id = ? ORDER BY created_at",
                (store_id,)
            )
            cameras = []
            for row in cursor.fetchall():
                camera_dict = self._dict_from_row(row)
                if camera_dict['detection_settings']:
                    camera_dict['detection_settings'] = json.loads(camera_dict['detection_settings'])
                cameras.append(Camera(**camera_dict))
            return cameras
    
    def get_camera(self, camera_id: int, store_id: int) -> Optional[Camera]:
        """Get specific camera"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras WHERE id = ? AND store_id = ?",
                (camera_id, store_id)
            )
            row = cursor.fetchone()
            if row:
                camera_dict = self._dict_from_row(row)
                if camera_dict['detection_settings']:
                    camera_dict['detection_settings'] = json.loads(camera_dict['detection_settings'])
                return Camera(**camera_dict)
            return None
    
    def update_camera(self, camera_id: int, store_id: int, updates: CameraUpdate) -> bool:
        """Update camera settings"""
        update_fields = []
        values = []
        
        for field, value in updates.dict(exclude_unset=True).items():
            if field == 'detection_settings' and value is not None:
                value = json.dumps(value)
            update_fields.append(f"{field} = ?")
            values.append(value)
        
        if not update_fields:
            return True
        
        values.extend([datetime.now(), camera_id, store_id])
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"""UPDATE cameras SET {', '.join(update_fields)}, updated_at = ?
                    WHERE id = ? AND store_id = ?""",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_camera(self, camera_id: int, store_id: int) -> bool:
        """Delete camera"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cameras WHERE id = ? AND store_id = ?",
                (camera_id, store_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # Detection events
    def save_detection_event(self, event: DetectionEvent) -> Optional[int]:
        """Save detection event"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO detection_events 
                   (camera_id, timestamp, person_count, confidence_scores, bounding_boxes)
                   VALUES (?, ?, ?, ?, ?)""",
                (event.camera_id, event.timestamp, event.person_count,
                 json.dumps(event.confidence_scores) if event.confidence_scores else None,
                 json.dumps(event.bounding_boxes) if event.bounding_boxes else None)
            )
            conn.commit()
            return cursor.lastrowid
    
    # Analytics
    def get_hourly_analytics(self, camera_id: int, date_str: str) -> List[HourlyAnalytics]:
        """Get hourly analytics for a camera on specific date"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM hourly_analytics WHERE camera_id = ? AND date = ? ORDER BY hour",
                (camera_id, date_str)
            )
            return [HourlyAnalytics(**self._dict_from_row(row)) for row in cursor.fetchall()]
    
    def update_hourly_analytics(self, camera_id: int, date_str: str, hour: int, metrics: Dict[str, Any]):
        """Update hourly analytics"""
        with self.get_connection() as conn:
            # Get camera zone type
            cursor = conn.execute("SELECT zone_type FROM cameras WHERE id = ?", (camera_id,))
            zone_row = cursor.fetchone()
            zone_type = zone_row['zone_type'] if zone_row else 'general'
            
            conn.execute(
                """INSERT OR REPLACE INTO hourly_analytics 
                   (camera_id, date, hour, total_visitors, unique_visitors, avg_dwell_time, 
                    peak_concurrent_visitors, zone_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (camera_id, date_str, hour, metrics.get('total_visitors', 0),
                 metrics.get('unique_visitors', 0), metrics.get('avg_dwell_time', 0),
                 metrics.get('peak_concurrent_visitors', 0), zone_type)
            )
            conn.commit()
    
    def get_daily_analytics(self, store_id: int, date_str: str) -> Optional[DailyAnalytics]:
        """Get daily analytics for store"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM daily_analytics WHERE store_id = ? AND date = ?",
                (store_id, date_str)
            )
            row = cursor.fetchone()
            if row:
                daily_dict = self._dict_from_row(row)
                if daily_dict['zone_analytics']:
                    daily_dict['zone_analytics'] = json.loads(daily_dict['zone_analytics'])
                return DailyAnalytics(**daily_dict)
            return None
    
    def update_daily_analytics(self, store_id: int, date_str: str, metrics: Dict[str, Any]):
        """Update daily analytics"""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO daily_analytics 
                   (store_id, date, total_footfall, unique_visitors, avg_dwell_time, 
                    peak_hour, peak_hour_count, zone_analytics)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (store_id, date_str, metrics.get('total_footfall', 0),
                 metrics.get('unique_visitors', 0), metrics.get('avg_dwell_time', 0),
                 metrics.get('peak_hour', 0), metrics.get('peak_hour_count', 0),
                 json.dumps(metrics.get('zone_analytics', {})))
            )
            conn.commit()
    
    # Queue analytics
    def save_queue_analytics(self, queue_data: QueueAnalytics) -> Optional[int]:
        """Save queue analytics"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO queue_analytics 
                   (camera_id, timestamp, queue_length, estimated_wait_time, service_time)
                   VALUES (?, ?, ?, ?, ?)""",
                (queue_data.camera_id, queue_data.timestamp, queue_data.queue_length,
                 queue_data.estimated_wait_time, queue_data.service_time)
            )
            conn.commit()
            return cursor.lastrowid
    
    # Product interactions
    def save_product_interaction(self, interaction: ProductInteraction) -> Optional[int]:
        """Save product interaction"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO product_interactions 
                   (camera_id, timestamp, interaction_type, duration, product_area, visitor_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (interaction.camera_id, interaction.timestamp, interaction.interaction_type,
                 interaction.duration, interaction.product_area, interaction.visitor_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    # Promotions
    def create_promotion(self, promo_data: Promotion) -> Optional[int]:
        """Create promotion"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO promotions 
                   (store_id, name, description, start_date, end_date, promotion_type, target_zones)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (promo_data.store_id, promo_data.name, promo_data.description,
                 promo_data.start_date, promo_data.end_date, promo_data.promotion_type,
                 json.dumps(promo_data.target_zones))
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_promotions(self, store_id: int, date_range: Optional[tuple] = None) -> List[Promotion]:
        """Get promotions for store"""
        query = "SELECT * FROM promotions WHERE store_id = ?"
        params = [store_id]
        
        if date_range:
            query += " AND start_date <= ? AND end_date >= ?"
            params.extend(date_range)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            promos = []
            for row in cursor.fetchall():
                promo_dict = self._dict_from_row(row)
                if promo_dict['target_zones']:
                    promo_dict['target_zones'] = json.loads(promo_dict['target_zones'])
                promos.append(Promotion(**promo_dict))
            return promos
    
    # AI Insights
    def save_ai_insight(self, insight: AIInsight) -> Optional[int]:
        """Save AI insight"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO ai_insights 
                   (store_id, insight_type, period_start, period_end, metrics_data, 
                    insights_text, recommendations, confidence_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (insight.store_id, insight.insight_type, insight.period_start, insight.period_end,
                 json.dumps(insight.metrics_data), insight.insights_text,
                 json.dumps(insight.recommendations) if insight.recommendations else None,
                 insight.confidence_score)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_ai_insights(self, store_id: int, limit: int = 10) -> List[AIInsight]:
        """Get recent AI insights"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM ai_insights WHERE store_id = ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (store_id, limit)
            )
            insights = []
            for row in cursor.fetchall():
                insight_dict = self._dict_from_row(row)
                insight_dict['metrics_data'] = json.loads(insight_dict['metrics_data'])
                if insight_dict['recommendations']:
                    insight_dict['recommendations'] = json.loads(insight_dict['recommendations'])
                insights.append(AIInsight(**insight_dict))
            return insights
    
    # System health
    def update_system_health(self, camera_id: int, health_data: Dict[str, Any]):
        """Update system health status"""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO system_health 
                   (camera_id, status, last_detection_time, error_message, fps, cpu_usage, memory_usage)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (camera_id, health_data.get('status'), health_data.get('last_detection_time'),
                 health_data.get('error_message'), health_data.get('fps'),
                 health_data.get('cpu_usage'), health_data.get('memory_usage'))
            )
            conn.commit()
    
    def get_system_health(self, store_id: int) -> List[Dict[str, Any]]:
        """Get system health for all cameras"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT c.id, c.name, c.zone_type, h.status, h.last_detection_time, 
                          h.error_message, h.fps, h.cpu_usage, h.memory_usage
                   FROM cameras c
                   LEFT JOIN system_health h ON c.id = h.camera_id
                   WHERE c.store_id = ? AND c.is_active = 1""",
                (store_id,)
            )
            return [self._dict_from_row(row) for row in cursor.fetchall()]
    
    # Dashboard metrics
    def get_dashboard_metrics(self, store_id: int, date_str: str) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        with self.get_connection() as conn:
            # Get current visitors count
            cursor = conn.execute(
                """SELECT SUM(de.person_count) as live_visitors
                   FROM detection_events de
                   JOIN cameras c ON de.camera_id = c.id
                   WHERE c.store_id = ? AND de.timestamp >= datetime('now', '-5 minutes')""",
                (store_id,)
            )
            live_visitors = cursor.fetchone()['live_visitors'] or 0
            
            # Get daily analytics
            daily_analytics = self.get_daily_analytics(store_id, date_str)
            
            # Get hourly breakdown
            cursor = conn.execute(
                """SELECT hour, SUM(total_visitors) as count
                   FROM hourly_analytics ha
                   JOIN cameras c ON ha.camera_id = c.id
                   WHERE c.store_id = ? AND ha.date = ?
                   GROUP BY hour ORDER BY hour""",
                (store_id, date_str)
            )
            hourly_counts = {str(row['hour']): row['count'] for row in cursor.fetchall()}
            
            # Get zone breakdown
            cursor = conn.execute(
                """SELECT c.zone_type, SUM(ha.total_visitors) as footfall,
                          SUM(ha.unique_visitors) as unique_visitors,
                          AVG(ha.avg_dwell_time) as avg_dwell_time
                   FROM hourly_analytics ha
                   JOIN cameras c ON ha.camera_id = c.id
                   WHERE c.store_id = ? AND ha.date = ?
                   GROUP BY c.zone_type""",
                (store_id, date_str)
            )
            zone_breakdown = {}
            for row in cursor.fetchall():
                zone_breakdown[row['zone_type']] = {
                    'footfall': row['footfall'],
                    'unique_visitors': row['unique_visitors'],
                    'avg_dwell_time': row['avg_dwell_time']
                }
            
            # Get queue status (for checkout zones)
            cursor = conn.execute(
                """SELECT c.name, qa.queue_length, qa.estimated_wait_time
                   FROM queue_analytics qa
                   JOIN cameras c ON qa.camera_id = c.id
                   WHERE c.store_id = ? AND c.zone_type = 'checkout' 
                         AND qa.timestamp >= datetime('now', '-10 minutes')
                   ORDER BY qa.timestamp DESC""",
                (store_id,)
            )
            queue_status = [self._dict_from_row(row) for row in cursor.fetchall()]
            
            return {
                'live_visitors': live_visitors,
                'total_footfall_today': daily_analytics.total_footfall if daily_analytics else 0,
                'unique_visitors_today': daily_analytics.unique_visitors if daily_analytics else 0,
                'avg_dwell_time': daily_analytics.avg_dwell_time if daily_analytics else 0,
                'peak_hour': daily_analytics.peak_hour if daily_analytics else 0,
                'peak_hour_count': daily_analytics.peak_hour_count if daily_analytics else 0,
                'hourly_counts': hourly_counts,
                'zone_breakdown': zone_breakdown,
                'queue_status': queue_status,
                'camera_health': self.get_system_health(store_id)
            }


# Note: db_manager is initialized in main.py lifespan function