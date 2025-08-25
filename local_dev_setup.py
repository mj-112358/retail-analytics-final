#!/usr/bin/env python3
"""
Local Development Setup for Retail Analytics
Creates SQLite database and tables for local RTSP testing
"""
import sqlite3
import os
from pathlib import Path

def create_local_database():
    """Create local SQLite database with all required tables"""
    db_path = Path("local_retail_analytics.db")
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print("Removed existing local database")
    
    # Create new database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = Path("database/schema_final.sql")
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        # Convert PostgreSQL syntax to SQLite
        schema = schema.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        schema = schema.replace('TIMESTAMP DEFAULT NOW()', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        schema = schema.replace('::timestamp', '')
        schema = schema.replace('BOOLEAN', 'INTEGER')
        schema = schema.replace('TEXT[]', 'TEXT')
        schema = schema.replace('JSONB', 'TEXT')
        
        # Execute schema
        try:
            cursor.executescript(schema)
            print("✅ Database schema created successfully")
        except Exception as e:
            print(f"⚠️  Schema error (may be harmless): {e}")
    
    # Create a test user for local development
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, store_name)
        VALUES (?, ?, ?, ?)
    """, ('Test User', 'test@example.com', '$2b$12$test.hash.for.local.dev', 'Local Test Store'))
    
    conn.commit()
    conn.close()
    
    print("✅ Local database setup complete")
    print(f"📁 Database created at: {db_path.absolute()}")

if __name__ == "__main__":
    create_local_database()