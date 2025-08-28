"""
Test PostgreSQL Database Connection
Quick script to verify your database connectivity
"""
import os
from sqlalchemy import create_engine, text

def test_database_connection():
    """Test database connection with detailed output"""
    
    # Get DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set!")
        print("\nPlease set it with your DigitalOcean database credentials:")
        print("export DATABASE_URL='postgresql://username:password@host:port/database?sslmode=require'")
        return False
    
    try:
        print("🔌 Testing database connection...")
        print(f"Database URL: {DATABASE_URL[:30]}...{DATABASE_URL[-20:]}")
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            # Get PostgreSQL version
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Get current database name
            result = connection.execute(text("SELECT current_database()"))
            database_name = result.fetchone()[0]
            
            # Get connection info
            result = connection.execute(text("SELECT current_user"))
            username = result.fetchone()[0]
            
            print("✅ Database connected successfully!")
            print(f"📋 Database: {database_name}")
            print(f"👤 User: {username}")
            print(f"🗄️ PostgreSQL Version: {version[:50]}...")
            
            # Test write permissions
            try:
                connection.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)"))
                connection.execute(text("DROP TABLE IF EXISTS test_table"))
                print("✅ Write permissions: OK")
            except Exception as e:
                print(f"⚠️ Write permissions: Limited - {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your DATABASE_URL format")
        print("2. Ensure SSL mode is set (add ?sslmode=require)")
        print("3. Verify database server is running")
        print("4. Check firewall settings")
        return False

if __name__ == "__main__":
    print("🧪 RetailIQ Analytics - Database Connection Test")
    print("=" * 50)
    
    success = test_database_connection()
    
    if success:
        print("\n🎉 Connection test passed!")
        print("You can now run: python create_tables.py")
    else:
        print("\n❌ Connection test failed!")
        print("Please fix the connection issues before proceeding.")
        
    print("=" * 50)