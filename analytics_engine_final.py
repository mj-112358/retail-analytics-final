"""
FINAL PRODUCTION ANALYTICS ENGINE
Complete metrics calculation and data processing
"""
import asyncio
import asyncpg
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import uuid

logger = logging.getLogger(__name__)

@dataclass
class VisitorData:
    """Visitor tracking data"""
    visitor_uuid: str
    camera_id: int
    store_id: int
    first_seen: datetime
    last_seen: datetime
    zone_type: str
    dwell_time_seconds: int
    entry_point: Optional[str] = None
    exit_point: Optional[str] = None

@dataclass
class ZoneMetrics:
    """Zone-specific metrics"""
    zone_type: str
    total_visitors: int
    unique_visitors: int
    avg_dwell_time_seconds: float
    peak_occupancy: int
    queue_wait_time_avg: float
    product_interactions: int

@dataclass
class StoreAnalytics:
    """Complete store analytics"""
    store_id: int
    date: date
    total_footfall: int
    unique_visitors: int
    avg_dwell_time_seconds: float
    peak_hour: int
    peak_hour_visitors: int
    zone_metrics: Dict[str, ZoneMetrics]
    hourly_breakdown: List[Dict]
    conversion_rate: float

class AnalyticsEngine:
    """Main analytics processing engine"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
    async def get_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.database_url)
    
    async def record_visitor_detection(self, 
                                     camera_id: int, 
                                     store_id: int, 
                                     detection_data: Dict) -> str:
        """Record a new visitor detection"""
        conn = await self.get_connection()
        try:
            # Generate unique visitor ID for this session
            visitor_uuid = str(uuid.uuid4())
            current_time = datetime.now()
            
            # Insert visitor record
            await conn.execute("""
                INSERT INTO visitors (
                    store_id, camera_id, visitor_uuid, first_seen_at, 
                    last_seen_at, zone_type, date, total_dwell_time_seconds
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (visitor_uuid, camera_id, date) 
                DO UPDATE SET 
                    last_seen_at = EXCLUDED.last_seen_at,
                    total_dwell_time_seconds = EXCLUDED.total_dwell_time_seconds
            """, store_id, camera_id, visitor_uuid, current_time, current_time,
                detection_data.get('zone_type', 'unknown'), current_time.date(), 0)
            
            return visitor_uuid
            
        except Exception as e:
            logger.error(f"Error recording visitor detection: {e}")
            raise
        finally:
            await conn.close()
    
    async def update_visitor_dwell_time(self, 
                                       visitor_uuid: str, 
                                       camera_id: int, 
                                       additional_seconds: int):
        """Update visitor's dwell time"""
        conn = await self.get_connection()
        try:
            await conn.execute("""
                UPDATE visitors 
                SET last_seen_at = CURRENT_TIMESTAMP,
                    total_dwell_time_seconds = total_dwell_time_seconds + $1
                WHERE visitor_uuid = $2 AND camera_id = $3 AND date = CURRENT_DATE
            """, additional_seconds, visitor_uuid, camera_id)
            
        except Exception as e:
            logger.error(f"Error updating dwell time: {e}")
        finally:
            await conn.close()
    
    async def record_queue_event(self, 
                                camera_id: int, 
                                store_id: int, 
                                queue_length: int, 
                                avg_wait_time: float,
                                zone_type: str):
        """Record queue detection event"""
        conn = await self.get_connection()
        try:
            await conn.execute("""
                INSERT INTO queue_events (camera_id, store_id, timestamp, queue_length, avg_wait_time_seconds, zone_type)
                VALUES ($1, $2, CURRENT_TIMESTAMP, $3, $4, $5)
            """, camera_id, store_id, queue_length, avg_wait_time, zone_type)
            
        except Exception as e:
            logger.error(f"Error recording queue event: {e}")
        finally:
            await conn.close()
    
    async def record_product_interaction(self, 
                                       visitor_uuid: str,
                                       camera_id: int, 
                                       store_id: int,
                                       interaction_type: str,
                                       product_area: str,
                                       duration_seconds: int):
        """Record product interaction event"""
        conn = await self.get_connection()
        try:
            await conn.execute("""
                INSERT INTO product_interactions (
                    visitor_uuid, camera_id, store_id, timestamp, 
                    interaction_type, product_area, duration_seconds
                ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4, $5, $6)
            """, visitor_uuid, camera_id, store_id, interaction_type, product_area, duration_seconds)
            
        except Exception as e:
            logger.error(f"Error recording product interaction: {e}")
        finally:
            await conn.close()
    
    async def calculate_hourly_analytics(self, store_id: int, target_date: date = None):
        """Calculate and store hourly analytics"""
        if target_date is None:
            target_date = date.today()
            
        conn = await self.get_connection()
        try:
            # Get all cameras for the store
            cameras = await conn.fetch("""
                SELECT id, zone_type FROM cameras 
                WHERE store_id = $1 AND is_active = true
            """, store_id)
            
            for camera in cameras:
                camera_id = camera['id']
                zone_type = camera['zone_type']
                
                # Calculate hourly metrics for each hour
                for hour in range(24):
                    start_time = datetime.combine(target_date, datetime.min.time().replace(hour=hour))
                    end_time = start_time + timedelta(hours=1)
                    
                    # Count visitors in this hour
                    visitor_stats = await conn.fetchrow("""
                        SELECT 
                            COUNT(*) as total_visitors,
                            COUNT(DISTINCT visitor_uuid) as unique_visitors,
                            AVG(total_dwell_time_seconds) as avg_dwell_time,
                            MAX(total_dwell_time_seconds) as max_dwell_time
                        FROM visitors 
                        WHERE camera_id = $1 AND date = $2 
                        AND (first_seen_at >= $3 AND first_seen_at < $4)
                    """, camera_id, target_date, start_time, end_time)
                    
                    # Get queue metrics for this hour
                    queue_stats = await conn.fetchrow("""
                        SELECT 
                            AVG(avg_wait_time_seconds) as avg_queue_wait,
                            MAX(queue_length) as peak_occupancy
                        FROM queue_events 
                        WHERE camera_id = $1 AND timestamp >= $2 AND timestamp < $3
                    """, camera_id, start_time, end_time)
                    
                    # Get product interaction count
                    interaction_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM product_interactions 
                        WHERE camera_id = $1 AND timestamp >= $2 AND timestamp < $3
                    """, camera_id, start_time, end_time)
                    
                    # Insert/update hourly analytics
                    await conn.execute("""
                        INSERT INTO hourly_analytics (
                            store_id, camera_id, date, hour, zone_type,
                            total_visitors, unique_visitors, avg_dwell_time_seconds,
                            peak_occupancy, queue_wait_time_avg_seconds, product_interactions
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (store_id, camera_id, date, hour)
                        DO UPDATE SET
                            total_visitors = EXCLUDED.total_visitors,
                            unique_visitors = EXCLUDED.unique_visitors,
                            avg_dwell_time_seconds = EXCLUDED.avg_dwell_time_seconds,
                            peak_occupancy = EXCLUDED.peak_occupancy,
                            queue_wait_time_avg_seconds = EXCLUDED.queue_wait_time_avg_seconds,
                            product_interactions = EXCLUDED.product_interactions
                    """, store_id, camera_id, target_date, hour, zone_type,
                         visitor_stats['total_visitors'] or 0,
                         visitor_stats['unique_visitors'] or 0,
                         visitor_stats['avg_dwell_time'] or 0,
                         queue_stats['peak_occupancy'] or 0,
                         queue_stats['avg_queue_wait'] or 0,
                         interaction_count or 0)
            
        except Exception as e:
            logger.error(f"Error calculating hourly analytics: {e}")
            raise
        finally:
            await conn.close()
    
    async def calculate_daily_analytics(self, store_id: int, target_date: date = None):
        """Calculate and store daily analytics for a store"""
        if target_date is None:
            target_date = date.today()
            
        conn = await self.get_connection()
        try:
            # Get overall store metrics
            store_stats = await conn.fetchrow("""
                SELECT 
                    SUM(total_visitors) as total_footfall,
                    COUNT(DISTINCT visitor_uuid) as unique_visitors,
                    AVG(avg_dwell_time_seconds) as avg_dwell_time
                FROM (
                    SELECT ha.total_visitors, v.visitor_uuid, ha.avg_dwell_time_seconds
                    FROM hourly_analytics ha
                    LEFT JOIN visitors v ON ha.camera_id = v.camera_id AND ha.date = v.date
                    WHERE ha.store_id = $1 AND ha.date = $2
                ) combined_stats
            """, store_id, target_date)
            
            # Find peak hour
            peak_hour_data = await conn.fetchrow("""
                SELECT hour, SUM(total_visitors) as hour_visitors
                FROM hourly_analytics 
                WHERE store_id = $1 AND date = $2
                GROUP BY hour
                ORDER BY hour_visitors DESC
                LIMIT 1
            """, store_id, target_date)
            
            # Get zone-wise breakdown
            zone_metrics = {}
            zones = await conn.fetch("""
                SELECT DISTINCT zone_type FROM cameras WHERE store_id = $1
            """, store_id)
            
            for zone in zones:
                zone_type = zone['zone_type']
                zone_data = await conn.fetchrow("""
                    SELECT 
                        SUM(total_visitors) as visitors,
                        AVG(avg_dwell_time_seconds) as avg_dwell_time,
                        SUM(product_interactions) as interactions,
                        AVG(queue_wait_time_avg_seconds) as avg_queue_wait
                    FROM hourly_analytics 
                    WHERE store_id = $1 AND date = $2 AND zone_type = $3
                """, store_id, target_date, zone_type)
                
                zone_metrics[zone_type] = {
                    "visitors": zone_data['visitors'] or 0,
                    "avg_dwell_time": zone_data['avg_dwell_time'] or 0,
                    "interactions": zone_data['interactions'] or 0,
                    "avg_queue_wait": zone_data['avg_queue_wait'] or 0
                }
            
            # Calculate conversion rate (simplified: interactions / visitors)
            total_interactions = sum(zone['interactions'] for zone in zone_metrics.values())
            conversion_rate = (total_interactions / (store_stats['total_footfall'] or 1)) * 100
            
            # Insert/update daily analytics
            await conn.execute("""
                INSERT INTO daily_analytics (
                    store_id, date, total_footfall, unique_visitors, 
                    avg_dwell_time_seconds, peak_hour, peak_hour_visitors,
                    zone_metrics, conversion_rate
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (store_id, date)
                DO UPDATE SET
                    total_footfall = EXCLUDED.total_footfall,
                    unique_visitors = EXCLUDED.unique_visitors,
                    avg_dwell_time_seconds = EXCLUDED.avg_dwell_time_seconds,
                    peak_hour = EXCLUDED.peak_hour,
                    peak_hour_visitors = EXCLUDED.peak_hour_visitors,
                    zone_metrics = EXCLUDED.zone_metrics,
                    conversion_rate = EXCLUDED.conversion_rate
            """, store_id, target_date,
                 store_stats['total_footfall'] or 0,
                 store_stats['unique_visitors'] or 0,
                 store_stats['avg_dwell_time'] or 0,
                 peak_hour_data['hour'] if peak_hour_data else 12,
                 peak_hour_data['hour_visitors'] if peak_hour_data else 0,
                 json.dumps(zone_metrics),
                 conversion_rate)
            
        except Exception as e:
            logger.error(f"Error calculating daily analytics: {e}")
            raise
        finally:
            await conn.close()
    
    async def get_store_analytics(self, store_id: int, 
                                start_date: date = None, 
                                end_date: date = None) -> Dict:
        """Get comprehensive store analytics"""
        if start_date is None:
            start_date = date.today() - timedelta(days=7)
        if end_date is None:
            end_date = date.today()
            
        conn = await self.get_connection()
        try:
            # Get daily analytics for the period
            daily_data = await conn.fetch("""
                SELECT * FROM daily_analytics 
                WHERE store_id = $1 AND date >= $2 AND date <= $3
                ORDER BY date
            """, store_id, start_date, end_date)
            
            # Get hourly breakdown for today
            today_hourly = await conn.fetch("""
                SELECT hour, SUM(total_visitors) as visitors, AVG(avg_dwell_time_seconds) as avg_dwell_time
                FROM hourly_analytics 
                WHERE store_id = $1 AND date = $2
                GROUP BY hour
                ORDER BY hour
            """, store_id, date.today())
            
            # Get zone-wise current metrics
            zone_data = await conn.fetch("""
                SELECT 
                    zone_type,
                    SUM(total_visitors) as total_visitors,
                    AVG(avg_dwell_time_seconds) as avg_dwell_time,
                    SUM(product_interactions) as interactions
                FROM hourly_analytics 
                WHERE store_id = $1 AND date = $2
                GROUP BY zone_type
            """, store_id, date.today())
            
            # Get active cameras
            cameras = await conn.fetch("""
                SELECT id, name, zone_type, status, last_detection_at
                FROM cameras 
                WHERE store_id = $1
                ORDER BY name
            """, store_id)
            
            return {
                "store_id": store_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "daily_analytics": [dict(row) for row in daily_data],
                "today_hourly": [
                    {
                        "hour": f"{row['hour']:02d}:00",
                        "visitors": row['visitors'] or 0,
                        "avg_dwell_time": row['avg_dwell_time'] or 0
                    } for row in today_hourly
                ],
                "zone_metrics": [
                    {
                        "zone_type": row['zone_type'],
                        "visitors": row['total_visitors'] or 0,
                        "avg_dwell_time": row['avg_dwell_time'] or 0,
                        "interactions": row['interactions'] or 0
                    } for row in zone_data
                ],
                "cameras": [
                    {
                        "id": row['id'],
                        "name": row['name'],
                        "zone_type": row['zone_type'],
                        "status": row['status'],
                        "last_detection": row['last_detection_at'].isoformat() if row['last_detection_at'] else None
                    } for row in cameras
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting store analytics: {e}")
            raise
        finally:
            await conn.close()
    
    async def get_metrics_for_ai_analysis(self, 
                                        store_id: int, 
                                        start_date: date, 
                                        end_date: date,
                                        include_comparison: bool = True) -> Dict:
        """Get structured metrics data for OpenAI analysis"""
        conn = await self.get_connection()
        try:
            # Current period metrics
            current_metrics = await conn.fetchrow("""
                SELECT 
                    AVG(total_footfall) as avg_daily_footfall,
                    AVG(unique_visitors) as avg_daily_unique_visitors,
                    AVG(avg_dwell_time_seconds) as avg_dwell_time,
                    AVG(conversion_rate) as avg_conversion_rate,
                    COUNT(*) as total_days
                FROM daily_analytics 
                WHERE store_id = $1 AND date >= $2 AND date <= $3
            """, store_id, start_date, end_date)
            
            # Peak hours analysis
            peak_hours = await conn.fetch("""
                SELECT 
                    hour,
                    AVG(total_visitors) as avg_visitors,
                    COUNT(*) as frequency
                FROM hourly_analytics 
                WHERE store_id = $1 AND date >= $2 AND date <= $3
                GROUP BY hour
                ORDER BY avg_visitors DESC
                LIMIT 3
            """, store_id, start_date, end_date)
            
            # Zone performance
            zone_performance = await conn.fetch("""
                SELECT 
                    zone_type,
                    AVG(total_visitors) as avg_visitors,
                    AVG(avg_dwell_time_seconds) as avg_dwell_time,
                    AVG(product_interactions) as avg_interactions
                FROM hourly_analytics 
                WHERE store_id = $1 AND date >= $2 AND date <= $3
                GROUP BY zone_type
                ORDER BY avg_visitors DESC
            """, store_id, start_date, end_date)
            
            metrics = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_days": current_metrics['total_days'] or 0
                },
                "overall_metrics": {
                    "avg_daily_footfall": round(current_metrics['avg_daily_footfall'] or 0, 1),
                    "avg_daily_unique_visitors": round(current_metrics['avg_daily_unique_visitors'] or 0, 1),
                    "avg_dwell_time_minutes": round((current_metrics['avg_dwell_time'] or 0) / 60, 1),
                    "conversion_rate_percent": round(current_metrics['avg_conversion_rate'] or 0, 2)
                },
                "peak_hours": [
                    {
                        "hour": f"{row['hour']:02d}:00",
                        "avg_visitors": round(row['avg_visitors'] or 0, 1)
                    } for row in peak_hours
                ],
                "zone_performance": [
                    {
                        "zone": row['zone_type'],
                        "avg_visitors": round(row['avg_visitors'] or 0, 1),
                        "avg_dwell_time_minutes": round((row['avg_dwell_time'] or 0) / 60, 1),
                        "avg_interactions": round(row['avg_interactions'] or 0, 1)
                    } for row in zone_performance
                ]
            }
            
            # Add comparison data if requested
            if include_comparison:
                # Get previous period for comparison (same duration)
                period_length = (end_date - start_date).days
                comparison_start = start_date - timedelta(days=period_length)
                comparison_end = start_date - timedelta(days=1)
                
                comparison_metrics = await conn.fetchrow("""
                    SELECT 
                        AVG(total_footfall) as avg_daily_footfall,
                        AVG(unique_visitors) as avg_daily_unique_visitors,
                        AVG(avg_dwell_time_seconds) as avg_dwell_time,
                        AVG(conversion_rate) as avg_conversion_rate
                    FROM daily_analytics 
                    WHERE store_id = $1 AND date >= $2 AND date <= $3
                """, store_id, comparison_start, comparison_end)
                
                if comparison_metrics and comparison_metrics['avg_daily_footfall']:
                    metrics["comparison"] = {
                        "period": {
                            "start_date": comparison_start.isoformat(),
                            "end_date": comparison_end.isoformat()
                        },
                        "metrics": {
                            "avg_daily_footfall": round(comparison_metrics['avg_daily_footfall'] or 0, 1),
                            "avg_daily_unique_visitors": round(comparison_metrics['avg_daily_unique_visitors'] or 0, 1),
                            "avg_dwell_time_minutes": round((comparison_metrics['avg_dwell_time'] or 0) / 60, 1),
                            "conversion_rate_percent": round(comparison_metrics['avg_conversion_rate'] or 0, 2)
                        }
                    }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting AI analysis metrics: {e}")
            raise
        finally:
            await conn.close()

# Background task for periodic analytics calculation
async def run_analytics_calculation(analytics_engine: AnalyticsEngine, store_id: int):
    """Background task to calculate analytics periodically"""
    try:
        logger.info(f"Starting analytics calculation for store {store_id}")
        
        # Calculate hourly analytics
        await analytics_engine.calculate_hourly_analytics(store_id)
        
        # Calculate daily analytics
        await analytics_engine.calculate_daily_analytics(store_id)
        
        logger.info(f"Analytics calculation completed for store {store_id}")
        
    except Exception as e:
        logger.error(f"Error in analytics calculation: {e}")

# Initialize analytics engine
def create_analytics_engine(database_url: str) -> AnalyticsEngine:
    """Create analytics engine instance"""
    return AnalyticsEngine(database_url)