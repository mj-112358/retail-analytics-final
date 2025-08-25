#!/usr/bin/env python3
"""
RTSP Connection Tester
Debug RTSP connectivity issues step by step
"""
import cv2
import socket
import urllib.parse

def test_network_connectivity(host, port):
    """Test if the camera IP and port are reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connectivity to {host}:{port} - SUCCESS")
            return True
        else:
            print(f"❌ Network connectivity to {host}:{port} - FAILED")
            return False
    except Exception as e:
        print(f"❌ Network test error: {e}")
        return False

def test_rtsp_connection(rtsp_url):
    """Test RTSP connection with detailed logging"""
    try:
        decoded_url = urllib.parse.unquote(rtsp_url)
        print(f"\n🔗 Testing RTSP URL: {decoded_url}")
        
        # Extract host and port for network test
        if "://" in decoded_url:
            parts = decoded_url.split("://")[1]  # Remove rtsp://
            if "@" in parts:
                # Split at last @ to handle passwords with @
                auth_and_host = parts.rsplit("@", 1)
                host_and_path = auth_and_host[1]
            else:
                host_and_path = parts
                
            # Extract host and port from host:port/path
            if "/" in host_and_path:
                host_port = host_and_path.split("/")[0]
            else:
                host_port = host_and_path
                
            if ":" in host_port:
                host = host_port.split(":")[0]
                port = int(host_port.split(":")[1])
            else:
                host = host_port
                port = 554  # Default RTSP port
                
            print(f"🌐 Parsed - Host: {host}, Port: {port}")
                
            # Test network connectivity first
            if not test_network_connectivity(host, port):
                return False
        
        print(f"🎥 Attempting OpenCV connection...")
        cap = cv2.VideoCapture(decoded_url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        
        print(f"📡 Connection status: {cap.isOpened()}")
        
        if cap.isOpened():
            print("✅ RTSP stream opened successfully")
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame read successful - Size: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return True
            else:
                print("❌ Failed to read frame from stream")
        else:
            print("❌ Failed to open RTSP stream")
        
        cap.release()
        return False
        
    except Exception as e:
        print(f"❌ RTSP test error: {e}")
        return False

if __name__ == "__main__":
    # Test the RTSP URL from your form
    rtsp_url = "rtsp://pinkcity:pinkcity%40123@192.168.10.212:554/stream1"
    
    # Let's also test with a public RTSP stream to verify the system works
    public_test_url = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    
    print("🧪 RTSP Connection Diagnostic Tool")
    print("=" * 50)
    
    print("Test 1: Your camera RTSP URL")
    success1 = test_rtsp_connection(rtsp_url)
    
    print("\n" + "=" * 50)
    print("Test 2: Public test RTSP stream")
    success2 = test_rtsp_connection(public_test_url)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Your camera: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test stream: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success2 and not success1:
        print("\n💡 The RTSP system works fine! Your camera is the issue:")
        print("1. Verify the camera IP address is correct")
        print("2. Check camera username/password") 
        print("3. Ensure camera is powered on and connected to network")
        print("4. Test from the same network as the camera")
        print("5. Try using the public test URL in the app to verify person detection works")
    elif not success2:
        print("\n⚠️  RTSP system may have issues. Check OpenCV installation.")