"""
Push Model Camera Client
Cameras initiate connection and push video streams to centralized server
"""
import cv2
import socketio
import asyncio
import base64
import json
import time
import logging
import numpy as np
from datetime import datetime
from typing import Optional
import argparse
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PushCameraClient:
    def __init__(self, server_url: str, store_id: str, camera_id: int, rtsp_url: str):
        """
        Initialize push camera client
        
        Args:
            server_url: WebSocket server URL (e.g., "http://localhost:3000")
            store_id: Store identifier
            camera_id: Camera number
            rtsp_url: Local camera RTSP URL
        """
        self.server_url = server_url
        self.store_id = store_id
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        self.is_connected = False
        self.is_registered = False
        self.frame_count = 0
        
        # Setup event handlers
        self.setup_events()
    
    def setup_events(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            logger.info(f"🔌 Connected to server: {self.server_url}")
            self.is_connected = True
            
            # Register camera with server
            await self.register_camera()
        
        @self.sio.event
        async def disconnect():
            logger.info("🔌 Disconnected from server")
            self.is_connected = False
            self.is_registered = False
        
        @self.sio.event
        async def connection_established(data):
            logger.info(f"✅ Connection established: {data}")
        
        @self.sio.event
        async def registration_success(data):
            logger.info(f"✅ Camera registered successfully: {data}")
            self.is_registered = True
        
        @self.sio.event
        async def frame_processed(data):
            """Receive acknowledgment for processed frame"""
            if self.frame_count % 30 == 0:  # Log every 30 frames
                logger.info(f"📊 Frame processed - People detected: {data.get('person_count', 0)}")
        
        @self.sio.event
        async def error(data):
            logger.error(f"❌ Server error: {data}")
    
    async def register_camera(self):
        """Register this camera with the server"""
        registration_data = {
            'store_id': self.store_id,
            'camera_id': self.camera_id
        }
        
        logger.info(f"📝 Registering camera: store_{self.store_id}_camera_{self.camera_id}")
        await self.sio.emit('camera_register', registration_data)
    
    async def connect_to_server(self, max_retries: int = 5):
        """Connect to WebSocket server with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Connecting to server (attempt {attempt + 1}/{max_retries})")
                await self.sio.connect(self.server_url)
                return True
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # Wait 5 seconds before retry
        
        logger.error("❌ Failed to connect to server after all retries")
        return False
    
    def test_camera_connection(self) -> bool:
        """Test if camera RTSP URL is accessible"""
        try:
            cap = cv2.VideoCapture(self.rtsp_url)
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                logger.info(f"✅ Camera connection test successful: {self.rtsp_url}")
                return True
            else:
                logger.warning(f"⚠️ Camera connection test failed: {self.rtsp_url}")
                return False
        except Exception as e:
            logger.error(f"❌ Camera connection test error: {e}")
            return False
    
    async def start_streaming(self, fps: int = 15):
        """Start streaming video to server"""
        if not self.is_connected:
            logger.error("❌ Not connected to server")
            return
        
        # Wait for registration
        retry_count = 0
        while not self.is_registered and retry_count < 10:
            await asyncio.sleep(1)
            retry_count += 1
        
        if not self.is_registered:
            logger.error("❌ Camera registration failed")
            return
        
        # Test camera connection first
        if not self.test_camera_connection():
            logger.error("❌ Camera not accessible, switching to test pattern")
            await self.stream_test_pattern(fps)
            return
        
        # Start actual camera streaming
        await self.stream_camera(fps)
    
    async def stream_camera(self, fps: int = 15):
        """Stream from actual camera"""
        cap = cv2.VideoCapture(self.rtsp_url)
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        frame_delay = 1.0 / fps
        logger.info(f"🎥 Starting camera stream: {self.rtsp_url} at {fps} FPS")
        
        try:
            while self.is_connected and self.is_registered:
                start_time = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    logger.warning("⚠️ Failed to read frame from camera, retrying...")
                    await asyncio.sleep(1)
                    continue
                
                # Resize frame to reduce bandwidth
                frame = cv2.resize(frame, (640, 480))
                
                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = base64.b64encode(buffer).decode('utf-8')
                
                # Send to server
                stream_data = {
                    'camera_id': f"store_{self.store_id}_camera_{self.camera_id}",
                    'stream_data': frame_bytes,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.sio.emit('camera_stream', stream_data)
                self.frame_count += 1
                
                # Frame rate control
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_delay - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
        finally:
            cap.release()
            logger.info("🎥 Camera stream ended")
    
    async def stream_test_pattern(self, fps: int = 15):
        """Stream test pattern when camera is not available"""
        frame_delay = 1.0 / fps
        logger.info(f"🎨 Starting test pattern stream at {fps} FPS")
        
        try:
            while self.is_connected and self.is_registered:
                start_time = time.time()
                
                # Generate test pattern
                frame = self.generate_test_frame()
                
                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = base64.b64encode(buffer).decode('utf-8')
                
                # Send to server
                stream_data = {
                    'camera_id': f"store_{self.store_id}_camera_{self.camera_id}",
                    'stream_data': frame_bytes,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.sio.emit('camera_stream', stream_data)
                self.frame_count += 1
                
                # Frame rate control
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_delay - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"❌ Test pattern streaming error: {e}")
    
    def generate_test_frame(self):
        """Generate a test frame with moving elements"""
        import math
        
        # Create base frame (640x480, 3 channels)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200  # Light gray background
        
        # Add moving elements to simulate people
        t = time.time()
        
        # Simulate 2-3 people moving around
        for i in range(3):
            x = int(320 + 100 * math.sin(t + i * 2.1))
            y = int(240 + 50 * math.cos(t * 0.8 + i * 1.5))
            
            # Draw person-like shape
            cv2.circle(frame, (x, y), 20, (100, 150, 100), -1)
            cv2.rectangle(frame, (x-10, y+10), (x+10, y+60), (80, 120, 80), -1)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Test Pattern - {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Store: {self.store_id} | Camera: {self.camera_id}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Frames: {self.frame_count}", (10, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.is_connected:
            await self.sio.disconnect()

def fix_rtsp_url(rtsp_url: str) -> str:
    """Fix common RTSP URL encoding issues"""
    # Handle @ symbols in username/password
    if '@' in rtsp_url and rtsp_url.count('@') > 1:
        # Fix double @ symbols from encoding issues
        parts = rtsp_url.split('@')
        if len(parts) >= 3:
            # Reconstruct: rtsp://user:pass@ip:port/path
            protocol_user_pass = '@'.join(parts[:-2])
            ip_port_path = '@'.join(parts[-2:])
            rtsp_url = f"{protocol_user_pass}@{ip_port_path}"
    
    # URL encode special characters in credentials
    if '://' in rtsp_url and '@' in rtsp_url:
        protocol = rtsp_url.split('://')[0]
        rest = rtsp_url.split('://')[1]
        
        if '@' in rest:
            credentials = rest.split('@')[0]
            ip_part = rest.split('@')[1]
            
            # URL encode credentials
            if ':' in credentials:
                user, password = credentials.split(':', 1)
                user_encoded = urllib.parse.quote(user, safe='')
                password_encoded = urllib.parse.quote(password, safe='')
                credentials_encoded = f"{user_encoded}:{password_encoded}"
            else:
                credentials_encoded = urllib.parse.quote(credentials, safe='')
            
            rtsp_url = f"{protocol}://{credentials_encoded}@{ip_part}"
    
    return rtsp_url

async def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Push Model Camera Client')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--store', required=True, help='Store ID')
    parser.add_argument('--camera', type=int, required=True, help='Camera ID')
    parser.add_argument('--rtsp', help='RTSP URL (optional, uses test pattern if not provided)')
    parser.add_argument('--fps', type=int, default=10, help='Frames per second (default: 10)')
    
    args = parser.parse_args()
    
    # Use provided RTSP URL or default test pattern
    rtsp_url = args.rtsp or "test_pattern"
    
    if rtsp_url != "test_pattern":
        rtsp_url = fix_rtsp_url(rtsp_url)
        logger.info(f"🎯 Using RTSP URL: {rtsp_url}")
    else:
        logger.info("🎨 Using test pattern (no camera specified)")
    
    # Create and start camera client
    client = PushCameraClient(args.server, args.store, args.camera, rtsp_url)
    
    try:
        # Connect to server
        if await client.connect_to_server():
            logger.info("🚀 Starting video stream...")
            await client.start_streaming(args.fps)
        else:
            logger.error("❌ Failed to connect to server")
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())