from flask import Blueprint, jsonify
from database import is_db_ready

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'chunker_service',
        'database': 'connected' if is_db_ready() else 'disconnected'
    })

@health_bp.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint."""
    if not is_db_ready():
        return jsonify({
            'status': 'not ready',
            'reason': 'database not connected'
        }), 503
    
    return jsonify({
        'status': 'ready',
        'service': 'chunker_service'
    })