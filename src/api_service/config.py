import os
from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
HOST = os.getenv('API_HOST', '0.0.0.0')
PORT = int(os.getenv('API_PORT', '8000'))
DEBUG = os.getenv('API_DEBUG', 'True').lower() in ('true', '1', 'yes')
MAX_FILE_SIZE = int(os.getenv('API_MAX_FILE_SIZE', '16777216'))  # 16MB default
CORS_ORIGINS = os.getenv('API_CORS_ORIGINS', '*').split(',')

# Document Storage Configuration
DOCUMENTS_STORAGE_PATH = os.getenv('DOCUMENTS_STORAGE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared', 'documents'))


# Oracle Database Configuration
ORACLE_USER = os.getenv('ORACLE_USER', 'SYSTEM')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', os.getenv('ORACLE_DB_PASSWORD', 'password'))
ORACLE_HOST = os.getenv('ORACLE_HOST', 'localhost')
ORACLE_PORT = int(os.getenv('ORACLE_PORT', '1521'))
ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME', 'FREEPDB1')
ORACLE_DSN = os.getenv('ORACLE_DSN') or f'{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}'

# Connection Pool Configuration
ORACLE_POOL_MIN = int(os.getenv('ORACLE_POOL_MIN', '2'))
ORACLE_POOL_MAX = int(os.getenv('ORACLE_POOL_MAX', '10'))
ORACLE_POOL_INCREMENT = int(os.getenv('ORACLE_POOL_INCREMENT', '1'))
ORACLE_POOL_PING_INTERVAL = int(os.getenv('ORACLE_POOL_PING_INTERVAL', '60'))