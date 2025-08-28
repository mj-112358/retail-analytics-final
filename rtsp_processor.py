"""
RTSP Stream Processor with YOLO Detection
Based on the yolo-rtsp-security-cam reference implementation
"""
import cv2
import numpy as np
import time
import logging
from datetime import datetime
from ultralytics import YOLO
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class RTSPProcessor:
    def __init__(self, rtsp_url, camera_id, zone_type="general"):
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.zone_type = zone_type
        self.is_running = False
        self.cap = None
        self.model = None
        
        # Motion detection parameters
        self.threshold = 350
        self.start_frames = 3
        self.tail_length = 8
        
        # Detection state
        self.motion_frames = 0
        self.last_motion_time = None
        self.is_recording = False
        
        # Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # People count tracking
        self.people_count = 0
        self.last_detection_time = None
        
    def load_yolo_model(self):
        """Load YOLO model (lazy loading)"""
        try:
            if self.model is None:
                logger.info(f"🤖 Loading YOLO model for camera {self.camera_id}")
                self.model = YOLO('yolov8n.pt')
                logger.info(f"✅ YOLO model loaded successfully for camera {self.camera_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            return False
    
    def connect_to_stream(self):
        """Connect to RTSP stream with improved settings"""
        try:
            logger.info(f"🔗 Connecting to RTSP stream: {self.rtsp_url}")
            
            # Release existing capture if any
            if self.cap:
                self.cap.release()
            
            # Create capture with better settings for RTSP
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            # Set RTSP-specific properties
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffering
            self.cap.set(cv2.CAP_PROP_FPS, 15)        # Lower FPS for stability
            
            # Test if we can read a frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error(f"❌ Failed to read initial frame from RTSP stream")
                if self.cap:
                    self.cap.release()
                return False
                
            logger.info(f"✅ Successfully connected to RTSP stream (Frame size: {frame.shape})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error connecting to RTSP stream: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def detect_motion(self, frame):
        """Detect motion in frame"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(gray)
            
            # Calculate motion amount
            motion_amount = np.sum(fg_mask) / 255
            
            return motion_amount > self.threshold
        except Exception as e:
            logger.error(f"Motion detection error: {e}")
            return False
    
    def detect_people(self, frame):
        """Detect people using YOLO"""
        try:
            if self.model is None:
                if not self.load_yolo_model():
                    return 0
            
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            # Count people (class 0 in COCO dataset)
            people_count = 0
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Class 0 is 'person' in COCO dataset
                        if class_id == 0 and confidence > 0.5:
                            people_count += 1
            
            return people_count
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return 0
    
    def process_frame(self, frame):
        """Process a single frame"""
        current_time = datetime.now()
        
        # First detect motion
        has_motion = self.detect_motion(frame)
        
        if has_motion:
            self.motion_frames += 1
            self.last_motion_time = current_time
            
            # If we have enough consecutive motion frames, start/continue recording
            if self.motion_frames >= self.start_frames:
                if not self.is_recording:
                    logger.info(f"📹 Recording started for camera {self.camera_id}")
                    self.is_recording = True
                
                # Run YOLO detection on motion frames
                people_count = self.detect_people(frame)
                if people_count > 0:
                    self.people_count = people_count
                    self.last_detection_time = current_time
                    logger.info(f"👥 Detected {people_count} people in camera {self.camera_id}")
        else:
            self.motion_frames = 0
            
            # Check if we should stop recording
            if self.is_recording and self.last_motion_time:
                time_since_motion = (current_time - self.last_motion_time).total_seconds()
                if time_since_motion >= self.tail_length:
                    logger.info(f"📹 Recording stopped for camera {self.camera_id}")
                    self.is_recording = False
        
        return {
            'has_motion': has_motion,
            'is_recording': self.is_recording,
            'people_count': self.people_count,
            'last_detection_time': self.last_detection_time.isoformat() if self.last_detection_time else None
        }
    
    async def start_processing(self):
        """Start processing RTSP stream"""
        self.is_running = True
        
        # Connect to stream
        if not self.connect_to_stream():
            return False
        
        logger.info(f"🚀 Started RTSP processing for camera {self.camera_id}")
        
        # Process frames in thread pool to avoid blocking
        executor = ThreadPoolExecutor(max_workers=1)
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"⚠️ Failed to read frame, attempting to reconnect...")
                    if not self.connect_to_stream():
                        await asyncio.sleep(5)  # Wait before retry
                        continue
                    continue
                
                # Process frame in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(executor, self.process_frame, frame)
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error processing frame: {e}")
                await asyncio.sleep(1)
        
        # Cleanup
        if self.cap:
            self.cap.release()
        executor.shutdown(wait=True)
        logger.info(f"🛑 RTSP processing stopped for camera {self.camera_id}")
    
    def stop_processing(self):
        """Stop processing RTSP stream"""
        self.is_running = False
    
    def get_status(self):
        """Get current processing status"""
        return {
            'camera_id': self.camera_id,
            'is_running': self.is_running,
            'is_recording': self.is_recording,
            'people_count': self.people_count,
            'last_detection_time': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'zone_type': self.zone_type
        }

# Global registry for active processors
active_processors = {}

def start_rtsp_processor(camera_id: int, rtsp_url: str, zone_type: str = "general"):
    """Start RTSP processor for a camera"""
    if camera_id in active_processors:
        logger.warning(f"RTSP processor already running for camera {camera_id}")
        return active_processors[camera_id]
    
    processor = RTSPProcessor(rtsp_url, camera_id, zone_type)
    active_processors[camera_id] = processor
    
    # Start processing in background
    asyncio.create_task(processor.start_processing())
    
    return processor

def stop_rtsp_processor(camera_id: int):
    """Stop RTSP processor for a camera"""
    if camera_id in active_processors:
        processor = active_processors[camera_id]
        processor.stop_processing()
        del active_processors[camera_id]
        logger.info(f"Stopped RTSP processor for camera {camera_id}")

def get_processor_status(camera_id: int = None):
    """Get status of RTSP processors"""
    if camera_id:
        return active_processors.get(camera_id, {}).get_status() if camera_id in active_processors else None
    else:
        return {cid: processor.get_status() for cid, processor in active_processors.items()}