"""
FINAL PRODUCTION RTSP CAMERA SYSTEM
Complete camera management and person detection pipeline
"""
import cv2
import numpy as np
import asyncio
import asyncpg
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict
import uuid
import os

logger = logging.getLogger(__name__)

class PersonTracker:
    """Track unique persons across frames"""
    
    def __init__(self, max_disappeared: int = 30):
        self.next_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        
    def register(self, centroid):
        """Register a new person"""
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1
        
    def deregister(self, object_id):
        """Remove a person from tracking"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        
    def update(self, detections):
        """Update tracked persons with new detections"""
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return {}
            
        input_centroids = np.array([self.compute_centroid(det) for det in detections])
        
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_centroids = list(self.objects.values())
            object_ids = list(self.objects.keys())
            
            # Compute distances between existing and input centroids
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)
            
            # Find minimum distances
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            used_row_idxs = set()
            used_col_idxs = set()
            
            for (row, col) in zip(rows, cols):
                if row in used_row_idxs or col in used_col_idxs:
                    continue
                    
                if D[row, col] > 50:  # Maximum distance threshold
                    continue
                    
                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                
                used_row_idxs.add(row)
                used_col_idxs.add(col)
                
            unused_rows = set(range(0, D.shape[0])).difference(used_row_idxs)
            unused_cols = set(range(0, D.shape[1])).difference(used_col_idxs)
            
            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(input_centroids[col])
                    
        return self.objects
    
    def compute_centroid(self, detection):
        """Compute centroid of detection bbox"""
        x1, y1, x2, y2 = detection
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2])

class RTSPCameraProcessor:
    """Process RTSP camera stream for person detection"""
    
    def __init__(self, camera_id: int, rtsp_url: str, store_id: int, zone_type: str, database_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.store_id = store_id
        self.zone_type = zone_type
        self.database_url = database_url
        self.is_running = False
        self.thread = None
        
        # Load YOLO model
        try:
            self.model = YOLO('yolov8n.pt')  # Use nano model for faster processing
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
            
        # Initialize tracker
        self.tracker = PersonTracker()
        self.visitor_sessions = {}  # Track visitor sessions
        
        # Analytics data
        self.current_visitors = set()
        self.hourly_visitor_count = 0
        self.last_analytics_update = datetime.now()
        
    async def get_db_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.database_url)
    
    def start_processing(self):
        """Start camera processing in background thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self.process_stream)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started processing camera {self.camera_id}")
    
    def stop_processing(self):
        """Stop camera processing"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped processing camera {self.camera_id}")
    
    def process_stream(self):
        """Main processing loop for RTSP stream"""
        cap = None
        retry_count = 0
        max_retries = 5
        
        while self.is_running and retry_count < max_retries:
            try:
                # Connect to RTSP stream
                cap = cv2.VideoCapture(self.rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for real-time processing
                
                if not cap.isOpened():
                    raise Exception(f"Cannot connect to RTSP stream: {self.rtsp_url}")
                
                asyncio.run(self.update_camera_status("online"))
                retry_count = 0
                
                frame_skip = 2  # Process every 2nd frame for performance
                frame_count = 0
                
                while self.is_running and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        logger.warning(f"Failed to read frame from camera {self.camera_id}")
                        break
                    
                    frame_count += 1
                    if frame_count % frame_skip != 0:
                        continue
                    
                    # Process frame for person detection
                    self.process_frame(frame)
                    
                    # Update analytics every minute
                    if (datetime.now() - self.last_analytics_update).seconds >= 60:
                        asyncio.run(self.update_analytics())
                        self.last_analytics_update = datetime.now()
                    
                    time.sleep(0.1)  # Small delay to prevent CPU overload
                    
            except Exception as e:
                logger.error(f"Error processing camera {self.camera_id}: {e}")
                asyncio.run(self.update_camera_status("error", str(e)))
                retry_count += 1
                time.sleep(5)  # Wait before retry
                
            finally:
                if cap:
                    cap.release()
        
        asyncio.run(self.update_camera_status("offline"))
    
    def process_frame(self, frame):
        """Process single frame for person detection"""
        if self.model is None:
            return
            
        try:
            # Run YOLO inference
            results = self.model(frame, conf=0.5, classes=[0])  # Class 0 is person
            
            detections = []
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                
                # Filter high confidence detections
                for i, conf in enumerate(confidences):
                    if conf > 0.7:  # High confidence threshold
                        detections.append(boxes[i])
            
            # Update tracker
            tracked_objects = self.tracker.update(detections)
            
            # Process tracked persons
            current_time = datetime.now()
            active_visitors = set()
            
            for person_id, centroid in tracked_objects.items():
                visitor_uuid = f"visitor_{self.camera_id}_{person_id}"
                active_visitors.add(visitor_uuid)
                
                # Track visitor session
                if visitor_uuid not in self.visitor_sessions:
                    self.visitor_sessions[visitor_uuid] = {
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'dwell_time': 0
                    }
                    # Record new visitor detection
                    asyncio.run(self.record_visitor_detection(visitor_uuid, current_time))
                else:
                    # Update existing session
                    session = self.visitor_sessions[visitor_uuid]
                    dwell_seconds = int((current_time - session['last_seen']).total_seconds())
                    session['last_seen'] = current_time
                    session['dwell_time'] += dwell_seconds
                    
                    # Update dwell time in database
                    asyncio.run(self.update_visitor_dwell_time(visitor_uuid, dwell_seconds))
            
            # Remove inactive visitors
            inactive_visitors = set(self.visitor_sessions.keys()) - active_visitors
            for visitor_uuid in inactive_visitors:
                del self.visitor_sessions[visitor_uuid]
            
            # Queue detection
            if len(detections) >= 3:  # Potential queue
                queue_length = len(detections)
                avg_wait_time = queue_length * 30.0  # Simple estimation
                asyncio.run(self.record_queue_event(queue_length, avg_wait_time))
            
            # Update current visitor count
            self.current_visitors = active_visitors
            self.hourly_visitor_count = len(active_visitors)
            
        except Exception as e:
            logger.error(f"Error processing frame for camera {self.camera_id}: {e}")
    
    async def record_visitor_detection(self, visitor_uuid: str, timestamp: datetime):
        """Record new visitor detection in database"""
        try:
            conn = await self.get_db_connection()
            await conn.execute("""
                INSERT INTO visitors (
                    store_id, camera_id, visitor_uuid, first_seen_at, 
                    last_seen_at, zone_type, date, total_dwell_time_seconds
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (visitor_uuid, camera_id, date) 
                DO UPDATE SET 
                    last_seen_at = EXCLUDED.last_seen_at
            """, self.store_id, self.camera_id, visitor_uuid, timestamp, 
                 timestamp, self.zone_type, timestamp.date(), 0)
            await conn.close()
        except Exception as e:
            logger.error(f"Error recording visitor detection: {e}")
    
    async def update_visitor_dwell_time(self, visitor_uuid: str, additional_seconds: int):
        """Update visitor's dwell time"""
        try:
            conn = await self.get_db_connection()
            await conn.execute("""
                UPDATE visitors 
                SET last_seen_at = CURRENT_TIMESTAMP,
                    total_dwell_time_seconds = total_dwell_time_seconds + $1
                WHERE visitor_uuid = $2 AND camera_id = $3 AND date = CURRENT_DATE
            """, additional_seconds, visitor_uuid, self.camera_id)
            await conn.close()
        except Exception as e:
            logger.error(f"Error updating dwell time: {e}")
    
    async def record_queue_event(self, queue_length: int, avg_wait_time: float):
        """Record queue detection event"""
        try:
            conn = await self.get_db_connection()
            await conn.execute("""
                INSERT INTO queue_events (camera_id, store_id, timestamp, queue_length, avg_wait_time_seconds, zone_type)
                VALUES ($1, $2, CURRENT_TIMESTAMP, $3, $4, $5)
            """, self.camera_id, self.store_id, queue_length, avg_wait_time, self.zone_type)
            await conn.close()
        except Exception as e:
            logger.error(f"Error recording queue event: {e}")
    
    async def update_camera_status(self, status: str, error_message: Optional[str] = None):
        """Update camera status in database"""
        try:
            conn = await self.get_db_connection()
            await conn.execute("""
                UPDATE cameras 
                SET status = $1, error_message = $2, last_detection_at = CURRENT_TIMESTAMP
                WHERE id = $3
            """, status, error_message, self.camera_id)
            await conn.close()
        except Exception as e:
            logger.error(f"Error updating camera status: {e}")
    
    async def update_analytics(self):
        """Update analytics data"""
        try:
            from analytics_engine_final import AnalyticsEngine
            analytics = AnalyticsEngine(self.database_url)
            await analytics.calculate_hourly_analytics(self.store_id)
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

class CameraManager:
    """Manage multiple RTSP cameras for a store"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.active_processors = {}
        self.is_running = False
    
    async def get_db_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.database_url)
    
    async def start_all_cameras(self, store_id: int):
        """Start processing all active cameras for a store"""
        try:
            conn = await self.get_db_connection()
            cameras = await conn.fetch("""
                SELECT id, rtsp_url, zone_type, name 
                FROM cameras 
                WHERE store_id = $1 AND is_active = true
            """, store_id)
            await conn.close()
            
            for camera in cameras:
                await self.start_camera(camera['id'], camera['rtsp_url'], store_id, camera['zone_type'])
            
            self.is_running = True
            logger.info(f"Started {len(cameras)} cameras for store {store_id}")
            
        except Exception as e:
            logger.error(f"Error starting cameras for store {store_id}: {e}")
    
    async def start_camera(self, camera_id: int, rtsp_url: str, store_id: int, zone_type: str):
        """Start processing for a specific camera"""
        if camera_id in self.active_processors:
            self.stop_camera(camera_id)
        
        processor = RTSPCameraProcessor(camera_id, rtsp_url, store_id, zone_type, self.database_url)
        processor.start_processing()
        self.active_processors[camera_id] = processor
        
        logger.info(f"Started camera {camera_id} for store {store_id}")
    
    def stop_camera(self, camera_id: int):
        """Stop processing for a specific camera"""
        if camera_id in self.active_processors:
            self.active_processors[camera_id].stop_processing()
            del self.active_processors[camera_id]
            logger.info(f"Stopped camera {camera_id}")
    
    def stop_all_cameras(self):
        """Stop all camera processing"""
        for camera_id in list(self.active_processors.keys()):
            self.stop_camera(camera_id)
        self.is_running = False
        logger.info("Stopped all cameras")
    
    async def get_camera_status(self, store_id: int) -> List[Dict]:
        """Get status of all cameras for a store"""
        try:
            conn = await self.get_db_connection()
            cameras = await conn.fetch("""
                SELECT id, name, rtsp_url, zone_type, status, last_detection_at, error_message
                FROM cameras 
                WHERE store_id = $1
                ORDER BY name
            """, store_id)
            await conn.close()
            
            camera_status = []
            for camera in cameras:
                is_processing = camera['id'] in self.active_processors
                current_visitors = 0
                
                if is_processing:
                    processor = self.active_processors[camera['id']]
                    current_visitors = len(processor.current_visitors)
                
                camera_status.append({
                    "id": camera['id'],
                    "name": camera['name'],
                    "zone_type": camera['zone_type'],
                    "status": camera['status'],
                    "is_processing": is_processing,
                    "current_visitors": current_visitors,
                    "last_detection": camera['last_detection_at'].isoformat() if camera['last_detection_at'] else None,
                    "error_message": camera['error_message']
                })
            
            return camera_status
            
        except Exception as e:
            logger.error(f"Error getting camera status: {e}")
            return []

# Global camera manager instance
camera_manager = None

def get_camera_manager(database_url: str) -> CameraManager:
    """Get global camera manager instance"""
    global camera_manager
    if camera_manager is None:
        camera_manager = CameraManager(database_url)
    return camera_manager

async def add_camera_to_store(store_id: int, name: str, rtsp_url: str, zone_type: str, 
                             location_description: str, database_url: str) -> int:
    """Add new camera to store and start processing"""
    try:
        conn = await asyncpg.connect(database_url)
        camera_id = await conn.fetchval("""
            INSERT INTO cameras (store_id, name, rtsp_url, zone_type, location_description, is_active)
            VALUES ($1, $2, $3, $4, $5, true)
            RETURNING id
        """, store_id, name, rtsp_url, zone_type, location_description)
        await conn.close()
        
        # Start processing the new camera
        manager = get_camera_manager(database_url)
        await manager.start_camera(camera_id, rtsp_url, store_id, zone_type)
        
        return camera_id
        
    except Exception as e:
        logger.error(f"Error adding camera: {e}")
        raise

async def remove_camera_from_store(camera_id: int, database_url: str):
    """Remove camera from store and stop processing"""
    try:
        # Stop processing first
        manager = get_camera_manager(database_url)
        manager.stop_camera(camera_id)
        
        # Remove from database
        conn = await asyncpg.connect(database_url)
        await conn.execute("UPDATE cameras SET is_active = false WHERE id = $1", camera_id)
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error removing camera: {e}")
        raise