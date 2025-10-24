"""
Web server entry point for audit dashboard.
Run this script to start the web interface for viewing audit logs.
"""
import os
import sys
import logging
import threading
import argparse
import atexit
from pathlib import Path

# Add parent directory to path if needed
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from insyt_secure.web.app import run_web_server
from insyt_secure.config import settings
from insyt_secure.config.runtime_config import get_web_config
from insyt_secure.utils.logging_config import configure_logging

# Configure logging
logger = logging.getLogger(__name__)

# PID file path
_WEB_PID_FILE = Path('./data/insyt-audit-web.pid')


def _write_pid_file():
    """Write web dashboard PID to file so main service can find and kill it."""
    try:
        _WEB_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if PID file already exists (from previous crashed instance)
        if _WEB_PID_FILE.exists():
            try:
                with open(_WEB_PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if that process is still running
                try:
                    os.kill(old_pid, 0)  # Signal 0 checks if process exists
                    logger.warning(f"Found existing web dashboard process (PID: {old_pid})")
                    logger.warning("Another instance may already be running. If port is in use, kill it first.")
                except ProcessLookupError:
                    # Old process is dead, safe to overwrite
                    logger.debug(f"Cleaning up stale PID file from process {old_pid}")
            except:
                # Corrupted PID file, just overwrite
                pass
        
        # Write our PID
        with open(_WEB_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.debug(f"Web dashboard PID file written: {_WEB_PID_FILE}")
    except Exception as e:
        logger.warning(f"Failed to write web dashboard PID file: {e}")


def _remove_pid_file():
    """Remove PID file on shutdown."""
    try:
        if _WEB_PID_FILE.exists():
            _WEB_PID_FILE.unlink()
            logger.debug("Web dashboard PID file removed")
    except Exception as e:
        logger.warning(f"Failed to remove web dashboard PID file: {e}")


# Register cleanup
atexit.register(_remove_pid_file)


def main():
    """Main entry point for web server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Insyt Secure Audit Web Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings (localhost:8080)
  insyt-audit-web
  
  # Allow remote access (bind to all interfaces)
  insyt-audit-web --host 0.0.0.0
  
  # Use custom port
  insyt-audit-web --port 9000
  
  # Remote access with custom port
  insyt-audit-web --host 0.0.0.0 --port 9000
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='Host to bind to (default: 127.0.0.1 for localhost only, use 0.0.0.0 for remote access)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to bind to (default: 8080)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    # Write PID file so main service can kill us
    _write_pid_file()
    
    logger.info("="*60)
    logger.info("Starting Insyt Secure Audit Web Interface")
    logger.info("="*60)
    
    # Load web configuration from runtime config
    web_config = get_web_config()
    
    # Check if web interface is enabled
    if not web_config.get('enabled', True):
        logger.warning("="*60)
        logger.warning("Web interface is DISABLED in configuration")
        logger.warning("="*60)
        logger.warning("")
        logger.warning("The web interface has been disabled via the settings page.")
        logger.warning("This is typically done for security or resource reasons.")
        logger.warning("")
        logger.warning("To re-enable:")
        logger.warning("1. Edit ./data/runtime_config.json")
        logger.warning("2. Set web_config.enabled to true")
        logger.warning("3. Run insyt-audit-web again")
        logger.warning("")
        logger.warning("Or set environment variable: WEB_INTERFACE_ENABLED=true")
        logger.warning("="*60)
        sys.exit(1)
    
    # Command-line args override runtime config, which overrides settings defaults
    host = args.host if args.host is not None else web_config.get('host', settings.WEB_INTERFACE_HOST)
    port = args.port if args.port is not None else web_config.get('port', settings.WEB_INTERFACE_PORT)
    
    # Get managed projects from runtime config
    from insyt_secure.config.runtime_config import _runtime_config
    managed_projects = []
    projects_config = _runtime_config.get('projects', {})
    for proj_id, proj_config in projects_config.items():
        if isinstance(proj_config, dict) and 'api_key' in proj_config:
            managed_projects.append({
                'project_id': proj_id,
                'api_key': proj_config['api_key']
            })
    
    # Prepare configuration for web server
    config = {
        'AUDIT_DB_PATH': settings.AUDIT_DB_PATH,
        'AUDIT_MAX_SIZE_GB': settings.AUDIT_MAX_SIZE_GB,
        'AUDIT_MAX_RETENTION_DAYS': settings.AUDIT_MAX_RETENTION_DAYS,
        'AUTH_DB_PATH': settings.AUTH_DB_PATH,
        'SECRET_KEY': settings.SECRET_KEY,
        'ACCOUNT_SERVICE_URL': settings.ACCOUNT_SERVICE_URL,
        'PROJECT_ID': settings.PROJECT_ID,
        'API_KEY': settings.API_KEY,
        'MANAGED_PROJECTS': managed_projects,  # Pass all managed projects
        'WEB_INTERFACE_HOST': host,
        'WEB_INTERFACE_PORT': port,
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true'
    }
    
    logger.info(f"Web interface will start on {config['WEB_INTERFACE_HOST']}:{config['WEB_INTERFACE_PORT']}")
    logger.info(f"Audit database: {config['AUDIT_DB_PATH']}")
    logger.info(f"Retention policy: {config['AUDIT_MAX_SIZE_GB']} GB, {config['AUDIT_MAX_RETENTION_DAYS']} days")
    logger.info(f"Managing {len(managed_projects)} project(s) for password reset")
    logger.info(f"Default credentials: admin / admin")
    logger.info("="*60)
    
    try:
        run_web_server(config)
    except KeyboardInterrupt:
        logger.info("Shutting down web server...")
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
