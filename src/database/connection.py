import os
import logging
import oracledb
from config import (
    ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN,
    ORACLE_POOL_MIN, ORACLE_POOL_MAX, ORACLE_POOL_INCREMENT, ORACLE_POOL_PING_INTERVAL
)

logger = logging.getLogger(__name__)

# Global state
_db_pool = None
_db_ready = False

def init_database():
    """Initialize Oracle database connection pool and create tables."""
    global _db_pool, _db_ready
    
    try:
        logger.info("Initializing Oracle database connection pool...")
        logger.info(f"Connecting to: {ORACLE_DSN} as user: {ORACLE_USER}")
        
        # Check for Oracle client environment variables that might interfere with thin mode
        if 'ORACLE_HOME' in os.environ:
            logger.warning("ORACLE_HOME detected, this might cause issues with thin mode")
        if 'TNS_ADMIN' in os.environ:
            logger.warning("TNS_ADMIN detected, this might cause issues with thin mode")
        
        # First test with a simple connection to ensure we're using thin mode correctly
        logger.info("Testing connection...")
        test_conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        test_conn.close()
        logger.info("Test connection successful")
        
        # Create connection pool using thin mode (no Oracle client installation required)
        _db_pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            min=ORACLE_POOL_MIN,
            max=ORACLE_POOL_MAX,
            increment=ORACLE_POOL_INCREMENT,
            ping_interval=ORACLE_POOL_PING_INTERVAL
        )
        
        # Test connection and create tables
        with _db_pool.acquire() as connection:
            # TODO make a simple select from dual to check connection pool and mark _db_ready as True
            None
        
        _db_ready = True
        logger.info("Database connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        _db_pool = None
        _db_ready = False

def get_db_pool():
    """Get the database connection pool."""
    return _db_pool

def is_db_ready():
    """Check if database is ready."""
    return _db_ready and _db_pool is not None

def cleanup_database():
    """Clean up database resources."""
    global _db_pool, _db_ready
    
    if _db_pool:
        try:
            logger.info("Closing database connection pool...")
            _db_pool.close()
            _db_pool = None
            _db_ready = False
            logger.info("Database connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")