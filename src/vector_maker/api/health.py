import os
from flask import Blueprint, jsonify
from models import get_model, is_model_ready
from database import get_db_pool, is_db_ready
from config import MODEL_NAME

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness probe - checks if the application is running"""
    return jsonify({
        'status': 'alive',
        'timestamp': os.times().system
    }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness probe - checks if the application is ready to serve requests"""
    health_status = {
        'status': 'ready',
        'timestamp': os.times().system,
        'model': MODEL_NAME,
        'services': {
            'model': False,
            'database': False
        }
    }
    
    # Check model status
    if not is_model_ready():
        health_status['status'] = 'not ready'
        health_status['reason'] = 'model not initialized'
        return jsonify(health_status), 503
    
    try:
        # Test model with a simple embedding request
        model = get_model()
        test_output = model.embed(["test"])
        if test_output and len(test_output) > 0:
            health_status['services']['model'] = True
        else:
            health_status['status'] = 'not ready'
            health_status['reason'] = 'model test failed'
            return jsonify(health_status), 503
    except Exception as e:
        health_status['status'] = 'not ready'
        health_status['reason'] = f'model error: {str(e)}'
        return jsonify(health_status), 503
    
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