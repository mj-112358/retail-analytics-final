#!/bin/bash

# Setup script for Push Model Retail Analytics
echo "🚀 Setting up Push Model Retail Analytics System"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import asyncio
from centralized_websocket_main import init_database
asyncio.run(init_database())
print('✅ Database initialized')
"

# Create demo store and cameras
echo "🏪 Setting up demo store..."
python3 -c "
import asyncio
import aiosqlite

async def setup_demo():
    async with aiosqlite.connect('centralized_retail_analytics.db') as db:
        # Create demo store
        cursor = await db.execute('''
            INSERT OR IGNORE INTO stores (organization_id, store_identifier, name, location)
            VALUES (1, 'demo', 'Demo Store', 'Test Location')
        ''')
        store_id = cursor.lastrowid or 1
        
        # Create demo cameras
        for i in range(1, 5):  # 4 cameras
            await db.execute('''
                INSERT OR IGNORE INTO cameras (store_id, camera_identifier, name, zone_type, location_description)
                VALUES (?, ?, ?, ?, ?)
            ''', (store_id, i, f'Demo Camera {i}', 'entrance' if i == 1 else 'zone', f'Location {i}'))
        
        await db.commit()
        print('✅ Demo store and cameras created')

asyncio.run(setup_demo())
"

echo "✅ Push Model System Setup Complete!"
echo ""
echo "🎯 Quick Start:"
echo "1. Start the WebSocket server:"
echo "   python3 centralized_websocket_main.py"
echo ""
echo "2. In another terminal, start a demo camera:"
echo "   python3 camera_client_push.py --server http://localhost:5000 --store demo --camera 1"
echo ""
echo "3. Or test with your RTSP camera:"
echo "   python3 camera_client_push.py --server http://localhost:5000 --store demo --camera 1 --rtsp 'rtsp://user:pass@camera_ip:554/stream'"
echo ""
echo "4. Access the system status at: http://localhost:5000/api/system/status"
echo "5. Check live analytics at: http://localhost:5000/api/analytics/live"
echo ""
echo "🔧 The system will automatically:"
echo "   - Register cameras when they connect"
echo "   - Process video frames with YOLO"
echo "   - Store detection data in database" 
echo "   - Provide real-time analytics"