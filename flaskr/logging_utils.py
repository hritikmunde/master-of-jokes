import logging
import functools
import time
from datetime import datetime
from flask import g, session, request, current_app

logger = logging.getLogger('moj')

def set_log_level(level):
    """Runtime adjustment of log level"""
    if level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        logger.setLevel(getattr(logging, level.upper()))
        current_app.logger.setLevel(getattr(logging, level.upper()))
        for handler in current_app.logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))
        logger.info(f"Log level changed to {level.upper()}")
    else:
        logger.error(f"Invalid log level: {level}")

def log_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session_id = session.get('_id', 'no-session')
        endpoint = request.endpoint if request else 'no-endpoint'
        module = func.__module__
        
        logger.debug(f'[{module}] Entering {func.__name__} - Session: {session_id} - Endpoint: {endpoint}')
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f'[{module}] Exiting {func.__name__} - Duration: {duration:.2f}s - Session: {session_id}')
            return result
        except Exception as e:
            logger.error(f'[{module}] Exception in {func.__name__}: {str(e)} - Session: {session_id}')
            raise
    
    return wrapper

def log_sql(query, params=None):
    """Log SQL queries and their parameters"""
    session_id = session.get('_id', 'no-session')
    module = 'database'
    logger.debug(f'[{module}] SQL Query (Session {session_id}):')
    logger.debug(f'[{module}] Query: {query}')
    logger.debug(f'[{module}] Parameters: {params}')

def log_db_result(result):
    """Log database query results"""
    module = 'database'
    logger.debug(f'[{module}] DB Result: {result}')

def log_request_info(response):
    """Log request information"""
    module = 'request'
    status_code = response.status_code
    
    if 200 <= status_code < 300:
        logger.info(f'[{module}] Request completed successfully: {request.method} {request.path} - {status_code}')
    elif 300 <= status_code < 500:
        logger.warning(f'[{module}] Request warning: {request.method} {request.path} - {status_code}')
    else:
        logger.error(f'[{module}] Request error: {request.method} {request.path} - {status_code}')
    
    return response

def log_auth_event(success, user_id=None, reason=None):
    """Log authentication events"""
    module = 'auth'
    if success:
        logger.info(f'[{module}] Authentication successful for user {user_id}')
    else:
        logger.warning(f'[{module}] Authentication failed{f" for user {user_id}" if user_id else ""}: {reason}')

def log_role_change(user_id, old_role, new_role):
    """Log role changes"""
    module = 'auth'
    logger.warning(f'[{module}] Role changed for user {user_id}: {old_role} -> {new_role}')

def log_auth_success(user):
    """Log successful authentication"""
    module = 'auth'
    logger.info(f'[{module}] Authentication successful for user {user["email"]}')

def log_auth_failure(email_or_nickname, reason):
    """Log authentication failure"""
    module = 'auth'
    logger.warning(f'[{module}] Authentication failed for {email_or_nickname}: {reason}')

def log_request():
    """Log incoming HTTP request details"""
    module = 'http'
    logger.info(
        f'[{module}] Request: {request.method} {request.path} - '
        f'Client: {request.remote_addr} - '
        f'Session: {session.get("_id", "no-session")}'
    )

def log_response(response):
    """Log HTTP response details"""
    module = 'http'
    if response.status_code >= 500:
        logger.error(f'[{module}] Response: {response.status_code} - {response.status}')
    elif response.status_code != 200:
        logger.warning(f'[{module}] Response: {response.status_code} - {response.status}')
    else:
        logger.info(f'[{module}] Response: {response.status_code} - {response.status}')
    return response