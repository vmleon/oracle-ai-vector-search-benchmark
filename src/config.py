import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
HOST = os.getenv('VECTOR_HOST', '0.0.0.0')
PORT = int(os.getenv('VECTOR_PORT', '8000'))
DEBUG = os.getenv('VECTOR_DEBUG', 'True').lower() in ('true', '1', 'yes')
MAX_FILE_SIZE = int(os.getenv('VECTOR_MAX_FILE_SIZE', '16777216'))  # 16MB default
TEMP_DIR = os.getenv('VECTOR_TEMP_DIR', tempfile.gettempdir())
CORS_ORIGINS = os.getenv('VECTOR_CORS_ORIGINS', '*').split(',')

# Model Configuration
MODEL_NAME = os.getenv('VECTOR_MODEL', 'intfloat/e5-mistral-7b-instruct')
ENFORCE_EAGER = os.getenv('VECTOR_ENFORCE_EAGER', 'True').lower() in ('true', '1', 'yes')

# Document Processing Configuration
CHUNK_SIZE = int(os.getenv('VECTOR_CHUNK_SIZE', '512'))
CHUNK_OVERLAP = int(os.getenv('VECTOR_CHUNK_OVERLAP', '50'))

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