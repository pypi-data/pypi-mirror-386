"""
Flask web application for audit log dashboard.
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime
import logging
import os
import json
from pathlib import Path

from ..utils.audit_logger import AuditLogger
from .auth import AuthManager
from ..config.runtime_config import get_web_config, save_web_config

logger = logging.getLogger(__name__)


def _load_web_config() -> dict:
    """Load web configuration from runtime config."""
    return get_web_config()


def _save_web_config(config: dict) -> bool:
    """Save web configuration using runtime config."""
    try:
        save_web_config(
            port=config.get('port'),
            host=config.get('host'),
            enabled=config.get('enabled')
        )
        logger.info(f"Web configuration saved: {config}")
        return True
    except Exception as e:
        logger.error(f"Failed to save web config: {e}")
        return False


def create_app(config: dict) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config: Configuration dictionary with audit and web settings
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    app.secret_key = config.get('SECRET_KEY', os.urandom(32))
    
    # Initialize audit logger and auth manager
    audit_logger = AuditLogger(
        db_path=config['AUDIT_DB_PATH'],
        max_size_gb=config.get('AUDIT_MAX_SIZE_GB', 1.0),
        max_retention_days=config.get('AUDIT_MAX_RETENTION_DAYS', 60)
    )
    
    auth_db_path = config.get('AUTH_DB_PATH', config['AUDIT_DB_PATH'].replace('audit_logs.db', 'auth.db'))
    auth_manager = AuthManager(
        db_path=auth_db_path,
        account_service_url=config.get('ACCOUNT_SERVICE_URL', ''),
        project_id=config.get('PROJECT_ID', ''),
        api_key=config.get('API_KEY', ''),
        managed_projects=config.get('MANAGED_PROJECTS', None)
    )
    
    # Store in app config for access in routes
    app.config['audit_logger'] = audit_logger
    app.config['auth_manager'] = auth_manager
    app.config['audit_config'] = config
    app.config['WEB_HOST'] = config.get('WEB_INTERFACE_HOST', '127.0.0.1')
    app.config['WEB_PORT'] = config.get('WEB_INTERFACE_PORT', 8080)
    
    def login_required(f):
        """Decorator to require authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_token = session.get('session_token')
            if not session_token:
                return redirect(url_for('login'))
            
            username = auth_manager.validate_session(session_token)
            if not username:
                session.clear()
                return redirect(url_for('login'))
            
            # Store username in request context
            request.username = username
            return f(*args, **kwargs)
        
        return decorated_function
    
    # Routes
    @app.route('/')
    @login_required
    def index():
        """Redirect to dashboard."""
        return redirect(url_for('dashboard'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page."""
        if request.method == 'POST':
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            session_token = auth_manager.authenticate(username, password)
            
            if session_token:
                session['session_token'] = session_token
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout and clear session."""
        session_token = session.get('session_token')
        if session_token:
            auth_manager.logout(session_token)
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard page."""
        return render_template('dashboard.html', username=request.username)
    
    @app.route('/settings')
    @login_required
    def settings():
        """Settings page."""
        # Load web config from file or environment
        web_config = _load_web_config()
        
        current_config = {
            'max_size_gb': audit_logger.max_size_bytes / (1024 * 1024 * 1024),
            'max_retention_days': audit_logger.max_retention_days,
            'web_port': web_config.get('port', 8080),
            'web_host': web_config.get('host', '127.0.0.1'),
            'web_enabled': web_config.get('enabled', True)
        }
        return render_template('settings.html', username=request.username, config=current_config)
    
    # API Routes
    @app.route('/api/logs')
    @login_required
    def api_get_logs():
        """Get logs with filters and pagination."""
        # Parse filters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        users = request.args.getlist('users[]')
        groups = request.args.getlist('groups[]')
        project_ids = request.args.getlist('project_ids[]')
        statuses = request.args.getlist('statuses[]')
        
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Convert dates
        date_from = datetime.fromisoformat(date_from) if date_from else None
        date_to = datetime.fromisoformat(date_to) if date_to else None
        
        # Get logs
        logs, total = audit_logger.get_logs_summary(
            limit=per_page,
            offset=offset,
            users=users or None,
            groups=groups or None,
            project_ids=project_ids or None,
            statuses=statuses or None,
            date_from=date_from,
            date_to=date_to
        )
        
        return jsonify({
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    
    @app.route('/api/logs/<int:log_id>')
    @login_required
    def api_get_log_detail(log_id):
        """Get full details of a specific log."""
        log_detail = audit_logger.get_log_detail(log_id)
        
        if not log_detail:
            return jsonify({'error': 'Log not found'}), 404
        
        return jsonify(log_detail)
    
    @app.route('/api/analytics')
    @login_required
    def api_get_analytics():
        """Get analytics data."""
        # Parse date filters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        project_ids = request.args.getlist('project_ids[]')
        
        date_from = datetime.fromisoformat(date_from) if date_from else None
        date_to = datetime.fromisoformat(date_to) if date_to else None
        
        analytics = audit_logger.get_analytics(
            date_from=date_from,
            date_to=date_to,
            project_ids=project_ids or None
        )
        return jsonify(analytics)
    
    @app.route('/api/filters')
    @login_required
    def api_get_filters():
        """Get distinct values for filters."""
        filters = audit_logger.get_distinct_values()
        
        # Add managed projects from runtime config (even if no logs exist yet)
        from insyt_secure.config.runtime_config import _runtime_config
        managed_project_ids = []
        projects_config = _runtime_config.get('projects', {})
        for proj_id in projects_config.keys():
            if proj_id and proj_id not in filters['project_ids']:
                managed_project_ids.append(proj_id)
        
        # Combine: projects from logs + projects from config
        all_project_ids = sorted(set(filters['project_ids'] + managed_project_ids))
        filters['project_ids'] = all_project_ids
        
        return jsonify(filters)
    
    @app.route('/api/project-aliases', methods=['POST'])
    @login_required
    def api_get_project_aliases():
        """Get aliases for project IDs."""
        data = request.get_json()
        project_ids = data.get('project_ids', [])
        
        if not project_ids:
            return jsonify({'error': 'No project IDs provided'}), 400
        
        # Fetch aliases from account service
        aliases = auth_manager.fetch_project_aliases(project_ids)
        
        return jsonify({'aliases': aliases})
    
    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def api_change_password():
        """Change user password."""
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'error': 'Missing passwords'}), 400
        
        success = auth_manager.change_password(request.username, old_password, new_password)
        
        if success:
            # Clear session to force re-login
            session.clear()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Incorrect old password'}), 400
    
    @app.route('/api/reset-password/initiate', methods=['POST'])
    def api_initiate_reset():
        """Initiate password reset."""
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'error': 'Username required'}), 400
        
        code = auth_manager.initiate_password_reset(username)
        
        if code:
            return jsonify({'success': True, 'message': 'Reset code sent to project admins'})
        else:
            return jsonify({'success': False, 'error': 'Rate limit exceeded or service error'}), 429
    
    @app.route('/api/reset-password/complete', methods=['POST'])
    def api_complete_reset():
        """Complete password reset with code."""
        data = request.get_json()
        username = data.get('username')
        code = data.get('code')
        new_password = data.get('new_password')
        
        if not all([username, code, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        success = auth_manager.complete_password_reset(username, code, new_password)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid or expired code'}), 400
    
    @app.route('/api/settings/retention', methods=['POST'])
    @login_required
    def api_update_retention():
        """Update retention policy settings."""
        data = request.get_json()
        max_size_gb = data.get('max_size_gb')
        max_retention_days = data.get('max_retention_days')
        
        try:
            if max_size_gb is not None:
                max_size_gb = float(max_size_gb)
            if max_retention_days is not None:
                max_retention_days = int(max_retention_days)
            
            audit_logger.update_retention_policy(max_size_gb, max_retention_days)
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error updating retention policy: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/settings/web-config', methods=['POST'])
    @login_required
    def api_update_web_config():
        """Update web server configuration (requires restart)."""
        data = request.get_json()
        
        try:
            port = int(data.get('port', 8080))
            host = data.get('host', '127.0.0.1')
            enabled = data.get('enabled', True)
            
            # Validate port range
            if port < 1024 or port > 65535:
                return jsonify({'success': False, 'error': 'Port must be between 1024 and 65535'}), 400
            
            # Validate host
            if host not in ['127.0.0.1', '0.0.0.0']:
                return jsonify({'success': False, 'error': 'Host must be 127.0.0.1 or 0.0.0.0'}), 400
            
            # Save configuration
            new_config = {
                'port': port,
                'host': host,
                'enabled': enabled
            }
            
            if _save_web_config(new_config):
                logger.info(f"Web configuration updated: {new_config}")
                return jsonify({'success': True, 'message': 'Configuration saved. Restart web server to apply changes.'})
            else:
                return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
                
        except Exception as e:
            logger.error(f"Error updating web configuration: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Security: Reject all undefined routes
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors - reject undefined routes."""
        logger.warning(f"Rejected undefined route: {request.method} {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Not Found', 'message': 'This endpoint does not exist'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle 405 errors - reject wrong HTTP methods."""
        logger.warning(f"Rejected invalid method: {request.method} {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Method Not Allowed', 'message': f'{request.method} not allowed for this endpoint'}), 405
    
    # Security: Reject requests to unknown hosts (prevent host header injection)
    @app.before_request
    def validate_host():
        """Validate Host header to prevent host header injection attacks."""
        host = app.config['WEB_HOST']
        port = app.config['WEB_PORT']
        
        allowed_hosts = [
            'localhost',
            '127.0.0.1',
            host,  # The configured host
            f"{host}:{port}",
            f"127.0.0.1:{port}",
            f"localhost:{port}"
        ]
        
        # Get the host from request
        request_host = request.host
        
        # Allow if host is in allowed list
        if request_host in allowed_hosts:
            return None
        
        # Allow valid IP addresses (with or without port)
        import re
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$'
        if re.match(ip_pattern, request_host):
            return None
        
        # Allow valid hostnames (e.g., EC2 DNS names, custom domains)
        # Pattern: alphanumeric with hyphens and dots, optionally with port
        hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9](:\d+)?$'
        if re.match(hostname_pattern, request_host):
            return None
        
        # Reject anything else (likely malicious)
        logger.warning(f"Rejected request with invalid host header: {request_host} from {request.remote_addr}")
        return jsonify({'error': 'Invalid Host'}), 400
    
    return app


def run_web_server(config: dict):
    """
    Run the Flask web server using waitress (production-ready WSGI server).
    
    Args:
        config: Configuration dictionary
    """
    app = create_app(config)
    
    host = config.get('WEB_INTERFACE_HOST', '127.0.0.1')
    port = config.get('WEB_INTERFACE_PORT', 8080)
    
    logger.info(f"Starting audit web interface on {host}:{port}")
    logger.info("Using Waitress production WSGI server")
    
    try:
        from waitress import serve
        # Use waitress for production-ready serving
        serve(app, host=host, port=port, threads=4, channel_timeout=60)
    except ImportError:
        logger.warning("Waitress not installed, falling back to Flask development server")
        logger.warning("For production use, install waitress: pip install waitress")
        debug = config.get('DEBUG', False)
        app.run(host=host, port=port, debug=debug, threaded=True)

