"""
Create Database Tables and Initialize Default Data
Run this script to set up your PostgreSQL database
"""
import os
from database import engine, Base, test_connection
from models import *
from sqlalchemy import text

def create_all_tables():
    """Create all database tables"""
    try:
        # Test connection first
        if not test_connection():
            print("❌ Cannot connect to database. Please check your DATABASE_URL.")
            return False
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Initialize default zone types
        initialize_zone_types()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def initialize_zone_types():
    """Initialize default retail zone types"""
    try:
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Check if zone types already exist
        existing = db.query(ZoneType).first()
        if existing:
            print("✅ Zone types already initialized")
            db.close()
            return
        
        # Default zone types for retail analytics
        default_zones = [
            {
                'zone_code': 'entrance',
                'display_name': 'Store Entrance/Exit',
                'description': 'Main entry and exit points',
                'expected_dwell_time_seconds': 30,
                'is_entrance_zone': True
            },
            {
                'zone_code': 'checkout',
                'display_name': 'Checkout/Payment Area',
                'description': 'Cashier and self-checkout areas',
                'expected_dwell_time_seconds': 180,
                'is_checkout_zone': True
            },
            {
                'zone_code': 'dairy_section',
                'display_name': 'Dairy Section',
                'description': 'Milk, cheese, and dairy products',
                'expected_dwell_time_seconds': 120
            },
            {
                'zone_code': 'electronics',
                'display_name': 'Electronics Department',
                'description': 'TVs, phones, computers',
                'expected_dwell_time_seconds': 300
            },
            {
                'zone_code': 'clothing',
                'display_name': 'Clothing Department',
                'description': 'Apparel and fashion items',
                'expected_dwell_time_seconds': 240
            },
            {
                'zone_code': 'grocery',
                'display_name': 'Grocery Aisles',
                'description': 'Food and household items',
                'expected_dwell_time_seconds': 90
            },
            {
                'zone_code': 'pharmacy',
                'display_name': 'Pharmacy Counter',
                'description': 'Medicine and health products',
                'expected_dwell_time_seconds': 150
            },
            {
                'zone_code': 'customer_service',
                'display_name': 'Customer Service Area',
                'description': 'Help desk and returns',
                'expected_dwell_time_seconds': 600
            },
            {
                'zone_code': 'general',
                'display_name': 'General Store Area',
                'description': 'Mixed merchandise area',
                'expected_dwell_time_seconds': 120
            },
            {
                'zone_code': 'bakery',
                'display_name': 'Bakery Section',
                'description': 'Fresh bread and baked goods',
                'expected_dwell_time_seconds': 100
            },
            {
                'zone_code': 'produce',
                'display_name': 'Produce Section',
                'description': 'Fresh fruits and vegetables',
                'expected_dwell_time_seconds': 150
            },
            {
                'zone_code': 'deli',
                'display_name': 'Deli Counter',
                'description': 'Fresh meat and prepared foods',
                'expected_dwell_time_seconds': 200
            }
        ]
        
        for zone_data in default_zones:
            zone = ZoneType(**zone_data)
            db.add(zone)
        
        db.commit()
        db.close()
        print("✅ Default zone types initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing zone types: {e}")

def verify_setup():
    """Verify database setup"""
    try:
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Count tables
        tables = [
            'users', 'stores', 'zone_types', 'cameras', 'detection_sessions',
            'visitors', 'detections', 'hourly_analytics', 'daily_analytics',
            'queue_events', 'product_interactions', 'promotions', 'ai_insights',
            'heatmap_data', 'system_alerts'
        ]
        
        print("\n📊 Database Verification:")
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                print(f"✅ {table}: {result[0]} records")
            except Exception as e:
                print(f"❌ {table}: Error - {e}")
        
        # Check zone types specifically
        zone_count = db.query(ZoneType).count()
        print(f"\n🏷️ Zone Types Available: {zone_count}")
        
        if zone_count > 0:
            zones = db.query(ZoneType).all()
            for zone in zones:
                print(f"   - {zone.zone_code}: {zone.display_name}")
        
        db.close()
        print("\n🎉 Database setup verification completed!")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")

if __name__ == "__main__":
    print("🚀 Setting up RetailIQ Analytics Database...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set your PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://username:password@host:port/database'")
        exit(1)
    
    # Create tables
    if create_all_tables():
        print("\n🔍 Verifying setup...")
        verify_setup()
        print("\n✅ Database setup completed successfully!")
        print("Your RetailIQ Analytics database is ready for use!")
    else:
        print("\n❌ Database setup failed. Please check your configuration.")
        exit(1)