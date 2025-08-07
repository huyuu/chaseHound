"""
Simple authentication middleware for ChaseHound
"""

import os
import hashlib
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from environment
        expected_key = os.getenv('CHASEHOUND_API_KEY')
        if not expected_key:
            # If no API key set, allow access (development mode)
            return f(*args, **kwargs)
        
        # Check API key in headers
        provided_key = request.headers.get('X-API-Key')
        if not provided_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Compare keys securely
        expected_hash = hashlib.sha256(expected_key.encode()).hexdigest()
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        
        if expected_hash != provided_hash:
            return jsonify({'error': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function 