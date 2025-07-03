from datetime import datetime
from flask import Blueprint, jsonify
from database import is_db_ready, get_db_pool

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness probe - checks if the application is running"""
    return jsonify({
        'status': 'alive',
        'service': 'chunker_service',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness probe - checks if the application is ready to serve requests"""
    health_status = {
        'status': 'ready',
        'service': 'chunker_service',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'services': {
            'database': False
        }
    }
    
    # Check database status
    if not is_db_ready():
        health_status['status'] = 'not ready'
        health_status['reason'] = 'database not ready'
        return jsonify(health_status), 503
    
    try:
        # Test database connection
        db_pool = get_db_pool()
        with db_pool.acquire() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            health_status['services']['database'] = True
    except Exception as e:
        health_status['status'] = 'not ready'
        health_status['reason'] = f'database error: {str(e)}'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200