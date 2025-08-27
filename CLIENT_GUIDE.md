# 📋 Client Setup Guide
## For Store Owners & Managers

---

## 🎯 What You're Getting

### Your Retail Analytics System Includes:
- **Real-time people counting** in your store
- **Zone-based analytics** (entrance, checkout, departments)
- **Peak hour analysis** and foot traffic patterns
- **AI-powered insights** for business optimization
- **Web dashboard** accessible from anywhere
- **Professional support** and setup assistance

### What You Need to Provide:
- **Internet connection** with sufficient upload bandwidth
- **IP cameras** or smartphones with camera capability
- **Basic network configuration** (we guide you through this)
- **Store layout information** for optimal camera placement

---

## 🏗️ Setup Process Overview

### Phase 1: Pre-Setup (Day 0)
1. **You receive** setup instructions via email
2. **We create** your unique store account
3. **You prepare** network and camera locations

### Phase 2: Camera Configuration (Day 1)
1. **You configure** cameras to connect to our system
2. **We verify** connections and data flow
3. **You test** the web dashboard

### Phase 3: Optimization (Day 2-7)
1. **We fine-tune** detection settings
2. **You define** store zones and areas
3. **System learns** your store's patterns

---

## 📷 Camera Setup Options

### Option A: Professional IP Cameras (Recommended)

#### **Popular Compatible Brands:**
- **Hikvision** (DS-2CD series)
- **Dahua** (IPC-HFW series)  
- **Axis** (M series)
- **Reolink** (RLC series)
- **Amcrest** (IP cameras)

#### **Camera Requirements:**
- **Resolution**: 1080p (1920x1080) or 720p (1280x720)
- **Frame Rate**: 15 FPS minimum
- **Codec**: H.264
- **Network**: Ethernet or WiFi
- **Features**: RTSP streaming support

#### **Recommended Camera Specifications:**
```
Resolution: 1920x1080 (1080p)
Frame Rate: 15-30 FPS
Bitrate: 2-4 Mbps
Codec: H.264
Audio: Not required (disable to save bandwidth)
Night Vision: Helpful but not required
Pan/Tilt/Zoom: Not required for people counting
```

### Option B: Smartphone Cameras (Budget Option)

#### **For Android:**
1. **Install "IP Webcam" app** (free)
2. **Configure streaming settings**:
   - Resolution: 1280x720
   - Quality: 70%
   - FPS: 15
3. **Start streaming** to our server

#### **For iPhone/iPad:**
1. **Install "EpocCam" app** ($8)
2. **Configure streaming settings**
3. **Connect to our system**

### Option C: Computer Webcams

#### **Using OBS Studio (Free Software):**
1. **Download OBS Studio**
2. **Add webcam source**
3. **Configure RTSP output**
4. **Stream to our server**

---

## 🌐 Network Requirements

### Internet Connection Requirements:

#### **Bandwidth Calculator:**
- **Per camera**: 2-4 Mbps upload speed
- **1 camera**: 4 Mbps upload minimum
- **2 cameras**: 8 Mbps upload minimum  
- **4 cameras**: 16 Mbps upload minimum
- **Add 50% buffer** for reliability

#### **Network Setup:**
```bash
# Test your upload speed (run this on your computer)
# Go to: https://www.speedtest.net/
# Note your UPLOAD speed (not download)

# Recommended upload speeds:
1 camera  → 5 Mbps upload
2 cameras → 10 Mbps upload  
4 cameras → 20 Mbps upload
```

#### **Router Configuration:**
- **Port forwarding**: Not required (cameras connect outbound)
- **Firewall**: Allow outbound RTSP traffic on port 8554
- **WiFi**: 5GHz recommended for cameras (less congested)
- **Ethernet**: Preferred for cameras (more stable)

### Bandwidth Optimization Tips:
1. **Lower resolution** if bandwidth is limited (720p instead of 1080p)
2. **Reduce frame rate** to 10-15 FPS
3. **Adjust quality** settings on cameras
4. **Use wired connections** when possible

---

## 🛠️ Step-by-Step Camera Configuration

### Step 1: Locate Camera IP Address
```bash
# Most cameras get IP from DHCP
# Check your router's admin panel for connected devices
# Or use IP scanner apps:
# - "Fing" (mobile app)
# - "Advanced IP Scanner" (Windows)
# - "LanScan" (macOS)
```

### Step 2: Access Camera Configuration

#### **Via Web Browser:**
1. **Open browser** and go to: `http://CAMERA_IP`
2. **Login** with camera credentials (usually admin/admin or admin/password)
3. **Navigate to** Network or Streaming settings

#### **Example for Hikvision:**
1. Go to `http://camera_ip`
2. Login → Configuration → Network → Advanced → RTSP
3. Set **RTSP Port**: 554
4. **Enable RTSP**
5. Note the **stream path** (usually `/Streaming/Channels/101`)

#### **Example for Dahua:**
1. Go to `http://camera_ip`  
2. Setup → Network → RTSP
3. **Enable RTSP service**
4. Note **stream path** (usually `/cam/realmonitor?channel=1&subtype=0`)

### Step 3: Configure RTSP Publishing

#### **What We'll Provide You:**
```
Your Store ID: 123
Server Address: retailanalytics.com
RTSP Port: 8554

Your Camera URLs:
Camera 1: rtsp://retailanalytics.com:8554/store_123_camera_1  
Camera 2: rtsp://retailanalytics.com:8554/store_123_camera_2
Camera 3: rtsp://retailanalytics.com:8554/store_123_camera_3
Camera 4: rtsp://retailanalytics.com:8554/store_123_camera_4
```

#### **Configure Each Camera:**
1. **Access camera settings**
2. **Find "RTSP" or "Streaming" section**
3. **Set Publish URL** to your assigned URL above
4. **Apply settings** and restart camera

### Step 4: Verify Connection

#### **Test Stream Locally First:**
```bash
# Use VLC Media Player to test:
# 1. Open VLC
# 2. Media → Open Network Stream  
# 3. Enter: rtsp://camera_ip:554/stream_path
# 4. Should see live video

# Example:
rtsp://192.168.1.100:554/Streaming/Channels/101
```

#### **Test Connection to Our Server:**
1. **Configure camera** with our RTSP URL
2. **Wait 2-3 minutes** for connection
3. **Check our dashboard** at retailanalytics.com
4. **Contact support** if camera doesn't appear within 10 minutes

---

## 🎯 Optimal Camera Placement

### Camera Position Guidelines:

#### **Entrance/Exit Cameras:**
- **Height**: 8-10 feet above ground
- **Angle**: 30-45 degrees downward
- **Coverage**: Full doorway width plus 2 feet on each side
- **Avoid**: Direct sunlight, backlighting from windows

#### **Zone Monitoring Cameras:**
- **Height**: 10-12 feet for wide coverage
- **Angle**: Looking down at customer paths
- **Coverage**: High-traffic aisles and departments  
- **Multiple cameras**: For large areas, overlap coverage 20%

#### **Checkout Area Cameras:**
- **Height**: 8 feet above queue area
- **Angle**: 45 degrees to capture waiting customers
- **Coverage**: Entire queue/checkout zone
- **Privacy**: Avoid pointing at cash registers or customer payment areas

### Store Layout Examples:

#### **Small Store (1-2 cameras):**
```
[Entrance Camera] → Door → [Store Interior]
                     ↓
                [Optional: Checkout Camera]
```

#### **Medium Store (3-4 cameras):**
```
[Entrance] → [Grocery Aisles] → [Electronics] → [Checkout]
    ↓             ↓                ↓            ↓
[Camera 1]   [Camera 2]      [Camera 3]   [Camera 4]
```

#### **Large Store (5+ cameras):**
```
[Entrance] → [Dept A] → [Dept B] → [Dept C] → [Checkout]
    ↓          ↓          ↓          ↓          ↓
[Camera 1] [Camera 2] [Camera 3] [Camera 4] [Camera 5]
             ↓          ↓          ↓
         [Camera 6] [Camera 7] [Camera 8]
```

---

## 📱 Dashboard Access & Usage

### Accessing Your Dashboard:
1. **Go to**: https://retailanalytics.com
2. **Login** with credentials provided
3. **Select your store** (if managing multiple locations)

### Dashboard Features:

#### **Live View:**
- **Real-time people count** in each zone
- **Camera status** (online/offline)
- **Current activity level**

#### **Analytics:**
- **Hourly foot traffic** graphs
- **Peak hours** identification
- **Day-of-week patterns**
- **Zone comparison** charts

#### **Insights:**
- **AI-generated recommendations**
- **Traffic pattern analysis**
- **Optimization suggestions**
- **Seasonal trends**

#### **Reports:**
- **Daily summaries** (email)
- **Weekly reports** (PDF)
- **Monthly analytics** (comprehensive)
- **Custom date ranges**

---

## 🆘 Troubleshooting Guide

### Camera Won't Connect

#### **Check These First:**
1. **Camera has internet connection**
   - Test: Browse to google.com from same network
2. **RTSP URL is correct**
   - Double-check spelling and store ID
3. **Camera RTSP is enabled**
   - Check camera streaming settings
4. **Firewall allows outbound traffic**
   - Port 8554 outbound should be allowed

#### **Advanced Troubleshooting:**
```bash
# Test camera stream locally
vlc rtsp://camera_ip:554/stream_path

# Test network connectivity  
ping retailanalytics.com

# Test RTSP port
telnet retailanalytics.com 8554
```

### No Detection Data

#### **Possible Causes:**
1. **Camera angle too high/low**
   - Adjust to 30-45 degree angle
2. **Poor lighting conditions**
   - Add lighting or adjust camera settings
3. **Camera resolution too low**
   - Use 720p minimum
4. **Obstructed camera view**
   - Remove obstacles in camera field of view

### Slow Dashboard Loading

#### **Solutions:**
1. **Check internet speed** (minimum 5 Mbps download)
2. **Clear browser cache**
3. **Try different browser** (Chrome recommended)
4. **Disable browser extensions**

### High Bandwidth Usage

#### **Optimization Steps:**
1. **Reduce camera resolution** (1080p → 720p)
2. **Lower frame rate** (30fps → 15fps)
3. **Adjust camera quality** settings
4. **Check for unnecessary cameras**

---

## 📞 Support & Contact

### When to Contact Support:
- **Camera won't connect** after 10 minutes
- **No detection data** after 24 hours
- **Dashboard issues** or login problems
- **Billing or subscription** questions
- **Additional cameras** or store locations

### Support Channels:
- **Email**: support@retailanalytics.com
- **Phone**: 1-800-RETAIL-1 (1-800-738-2451)
- **Live Chat**: Available on dashboard
- **Help Center**: https://help.retailanalytics.com

### Information to Provide:
- **Store ID**: (provided in setup email)
- **Camera details**: Brand, model, IP address
- **Error messages**: Exact text of any errors
- **Network setup**: Internet provider, router type
- **Screenshots**: Of settings or error screens

### Support Hours:
- **Business Hours**: Mon-Fri 9 AM - 6 PM EST
- **Emergency**: 24/7 for system outages
- **Response Time**: Within 2 hours during business hours

---

## 💰 Billing & Subscription

### What's Included:
- **Setup assistance** and configuration help
- **Unlimited data processing** and analytics
- **Web dashboard** access
- **Email/SMS alerts**
- **Phone and email support**
- **Software updates** and improvements

### Subscription Tiers:
- **Basic**: 1-4 cameras, $99/month
- **Professional**: 5-10 cameras, $199/month  
- **Enterprise**: 11+ cameras, custom pricing

### Billing:
- **Monthly billing** cycle
- **Auto-renewal** with 30-day notice to cancel
- **Prorated charges** for mid-month changes
- **Multiple payment methods** accepted

---

## 🎉 Success Checklist

### Week 1 Goals:
- [ ] All cameras connected and streaming
- [ ] Dashboard shows live people counts
- [ ] Store zones configured correctly
- [ ] Staff trained on dashboard usage

### Month 1 Goals:  
- [ ] Baseline analytics established
- [ ] Peak hours identified
- [ ] Staff scheduling optimized based on data
- [ ] First business insights applied

### Ongoing Benefits:
- [ ] Data-driven staffing decisions
- [ ] Improved customer service during peak times
- [ ] Marketing campaign effectiveness measurement
- [ ] Store layout optimization insights
- [ ] Competitive advantage through analytics

---

**Welcome to the future of retail analytics! 🚀**

Your dedicated account manager will contact you within 24 hours to schedule your setup call and answer any questions.