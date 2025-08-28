"""
SQLAlchemy Database Configuration for RetailIQ Analytics
Production-ready PostgreSQL setup with connection pooling
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# For async operations (convert postgresql:// to postgresql+asyncpg://)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if DATABASE_URL else None

# Create sync engine with SSL and connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=False  # Set to True for SQL debugging
)

# Create async engine for FastAPI
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

def get_db():
    """Dependency for sync database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Dependency for async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Test database connection
def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ Database connected successfully!")
            print(f"PostgreSQL version: {version}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False