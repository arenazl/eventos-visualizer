from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
from utils.config import settings

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base for models
Base = declarative_base()

async def init_db():
    """Initialize database and create tables"""
    try:
        from models import events, users  # Import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
            
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

async def close_db():
    """Close database connections"""
    engine.dispose()
    logger.info("✅ Database connections closed")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()