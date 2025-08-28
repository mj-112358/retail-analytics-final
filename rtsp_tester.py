#!/usr/bin/env python3
"""
RTSP Stream Tester
Quick utility to test RTSP stream connectivity
"""
import cv2
import sys
import time

def test_rtsp_stream(rtsp_url, timeout=10):
    """
    Test RTSP stream connectivity
    Returns (success, error_message, frame_info)
    """
    print(f"🔍 Testing RTSP stream: {rtsp_url}")
    
    cap = None
    try:
        # Try to connect
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        
        if not cap.isOpened():
            return False, "Failed to open RTSP stream", None
        
        # Set properties for better RTSP handling
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        # Try to read a frame with timeout
        start_time = time.time()
        frame_read = False
        frame = None
        
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_read = True
                break
            time.sleep(0.1)
        
        if not frame_read:
            return False, f"No frame received within {timeout} seconds", None
        
        # Get frame info
        height, width = frame.shape[:2]
        frame_info = {
            'width': width,
            'height': height,
            'channels': frame.shape[2] if len(frame.shape) > 2 else 1,
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'codec': cap.get(cv2.CAP_PROP_FOURCC)
        }
        
        return True, "Stream is accessible", frame_info
        
    except Exception as e:
        return False, f"Exception occurred: {str(e)}", None
        
    finally:
        if cap:
            cap.release()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 rtsp_tester.py <rtsp_url>")
        print("Example: python3 rtsp_tester.py rtsp://user:pass@192.168.1.100:554/stream1")
        sys.exit(1)
    
    rtsp_url = sys.argv[1]
    
    success, message, frame_info = test_rtsp_stream(rtsp_url)
    
    if success:
        print(f"✅ SUCCESS: {message}")
        print(f"📹 Frame Info: {frame_info}")
    else:
        print(f"❌ FAILED: {message}")
        
        # Suggest common fixes
        print("\n💡 Common solutions:")
        print("1. Check camera IP address and port")
        print("2. Verify username and password")
        print("3. Try different stream paths (stream1, stream2, main, sub)")
        print("4. Check if camera is accessible from your network")
        print("5. Try accessing the stream with VLC Media Player first")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()