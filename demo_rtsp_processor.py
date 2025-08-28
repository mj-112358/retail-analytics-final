"""
Demo RTSP Processor
Simulates people detection for testing when real RTSP streams aren't available
"""
import asyncio
import logging
import time
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class DemoRTSPProcessor:
    def __init__(self, rtsp_url, camera_id, zone_type="general"):
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.zone_type = zone_type
        self.is_running = False
        
        # Simulation parameters
        self.people_count = 0
        self.last_detection_time = None
        self.is_recording = False
        
        # Zone-specific simulation patterns
        self.zone_patterns = {
            'entrance': {'min_people': 0, 'max_people': 8, 'activity_freq': 0.3},
            'checkout': {'min_people': 1, 'max_people': 12, 'activity_freq': 0.4},
            'dairy_section': {'min_people': 0, 'max_people': 6, 'activity_freq': 0.2},
            'electronics': {'min_people': 0, 'max_people': 4, 'activity_freq': 0.15},
            'clothing': {'min_people': 0, 'max_people': 5, 'activity_freq': 0.25},
            'grocery': {'min_people': 0, 'max_people': 7, 'activity_freq': 0.35},
            'general': {'min_people': 0, 'max_people': 5, 'activity_freq': 0.2}
        }
    
    def simulate_detection(self):
        """Simulate realistic people detection based on zone type"""
        pattern = self.zone_patterns.get(self.zone_type, self.zone_patterns['general'])
        
        # Simulate activity based on time of day
        current_hour = datetime.now().hour
        
        # Peak hours: 10-12, 14-16, 18-20
        if current_hour in [10, 11, 14, 15, 18, 19]:
            activity_multiplier = 1.5
        elif current_hour in [8, 9, 12, 13, 16, 17, 20, 21]:
            activity_multiplier = 1.0
        else:
            activity_multiplier = 0.3
        
        # Random activity
        if random.random() < pattern['activity_freq'] * activity_multiplier:
            self.people_count = random.randint(pattern['min_people'], pattern['max_people'])
            self.last_detection_time = datetime.now()
            self.is_recording = True
            
            logger.info(f"👥 DEMO: Detected {self.people_count} people in camera {self.camera_id} ({self.zone_type})")
        else:
            # Gradual decrease in people count
            if self.people_count > 0 and random.random() < 0.1:
                self.people_count = max(0, self.people_count - random.randint(1, 2))
                if self.people_count == 0:
                    self.is_recording = False
        
        return {
            'has_motion': self.people_count > 0,
            'is_recording': self.is_recording,
            'people_count': self.people_count,
            'last_detection_time': self.last_detection_time.isoformat() if self.last_detection_time else None
        }
    
    async def start_processing(self):
        """Start demo processing"""
        self.is_running = True
        logger.info(f"🎭 Started DEMO RTSP processing for camera {self.camera_id} (zone: {self.zone_type})")
        logger.info(f"📹 Simulating stream: {self.rtsp_url}")
        
        while self.is_running:
            try:
                # Simulate processing every 2 seconds
                result = self.simulate_detection()
                
                # Longer interval between detections
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Demo processing error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"🛑 Demo RTSP processing stopped for camera {self.camera_id}")
    
    def stop_processing(self):
        """Stop demo processing"""
        self.is_running = False
    
    def get_status(self):
        """Get current demo status"""
        return {
            'camera_id': self.camera_id,
            'is_running': self.is_running,
            'is_recording': self.is_recording,
            'people_count': self.people_count,
            'last_detection_time': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'zone_type': self.zone_type,
            'mode': 'DEMO'
        }

# Global registry for demo processors
demo_processors = {}

def start_demo_rtsp_processor(camera_id: int, rtsp_url: str, zone_type: str = "general"):
    """Start demo RTSP processor"""
    if camera_id in demo_processors:
        logger.warning(f"Demo RTSP processor already running for camera {camera_id}")
        return demo_processors[camera_id]
    
    processor = DemoRTSPProcessor(rtsp_url, camera_id, zone_type)
    demo_processors[camera_id] = processor
    
    # Start processing in background
    asyncio.create_task(processor.start_processing())
    
    return processor

def stop_demo_rtsp_processor(camera_id: int):
    """Stop demo RTSP processor"""
    if camera_id in demo_processors:
        processor = demo_processors[camera_id]
        processor.stop_processing()
        del demo_processors[camera_id]
        logger.info(f"Stopped demo RTSP processor for camera {camera_id}")

def get_demo_processor_status(camera_id: int = None):
    """Get demo processor status"""
    if camera_id:
        return demo_processors.get(camera_id, {}).get_status() if camera_id in demo_processors else None
    else:
        return {cid: processor.get_status() for cid, processor in demo_processors.items()}