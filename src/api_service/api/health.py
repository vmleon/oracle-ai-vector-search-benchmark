import os
from datetime import datetime
from flask import Blueprint, jsonify
from database import get_db_pool, is_db_ready
from database.operations import get_document_counts_by_status, get_chunks_by_embedding_status
from services.queue import get_all_queue_depths

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check for API service"""
    return jsonify({
        'status': 'healthy',
        'service': 'api_service',
        'timestamp': os.times().system
    }), 200

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness probe - checks if the application is running"""
    return jsonify({
        'status': 'alive',
        'service': 'api_service',
        'timestamp': os.times().system
    }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness probe - checks if the application is ready to serve requests"""
    health_status = {
        'status': 'ready',
        'service': 'api_service',
        'timestamp': os.times().system,
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

@health_bp.route('/status', methods=['GET']) 
def status_check():
    """System status with queue depths, document and chunk counts"""
    try:
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Get queue depths
        queue_depths = get_all_queue_depths()
        
        # Get document counts
        document_stats = get_document_counts_by_status()
        
        # Get chunk counts
        chunk_stats = get_chunks_by_embedding_status()
        
        status_response = {
            'timestamp': timestamp,
            'queues': queue_depths,
            'documents': document_stats,
            'chunks': chunk_stats
        }
        
        return jsonify(status_response), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get status: {str(e)}',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500