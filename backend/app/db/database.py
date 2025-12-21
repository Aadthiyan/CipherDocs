"""
CyborgDB Database Configuration
SQLAlchemy setup with connection pooling
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DB_ECHO,  # Log SQL queries (development only)
    future=True  # Use SQLAlchemy 2.0 style
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Base class for models
Base = declarative_base()


# Event listeners for connection pool monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new connection is created"""
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool"""
    logger.debug("Database connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool"""
    logger.debug("Database connection returned to pool")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    
    Yields:
        Database session
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database
    
    Creates all tables if they don't exist.
    In production, use Alembic migrations instead.
    """
    try:
        # Import all models here to ensure they're registered with Base
        # from app.models import tenant, user, document  # Will be created in Phase 2
        
        # Create tables (development only - use Alembic in production)
        if settings.is_development():
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        else:
            logger.info("Database initialization skipped (use Alembic migrations in production)")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db():
    """
    Close database connections
    
    Called on application shutdown
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


def get_db_info() -> dict:
    """
    Get database connection pool information
    
    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow()
    }
