# Changelog

All notable changes to the `insyt-secure` package will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and follows the format from [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.5.0] - 2025-10-21

### Added
- **Audit Logging System**: Comprehensive logging of all code execution requests
  - Automatic logging of query, Python code, extracted data, status, user, group, and timestamp
  - Data compression for query, code, and results (70-80% storage reduction)
  - SQLite database with optimized indexes for fast queries
  - Configurable retention policy (size and age-based auto-purging)
  - Default limits: 1 GB storage, 60 days retention

- **Web Dashboard**: Modern web interface for viewing audit logs
  - Built with Flask, Tailwind CSS, Alpine.js, and Chart.js
  - Zero build tools required (CDN-based frontend)
  - Responsive, mobile-friendly design
  - Real-time analytics and charts
  - Advanced filtering (users, groups, statuses, date ranges)
  - Pagination support for large datasets
  - Detailed view modal with lazy loading
  - Execution trends visualization

- **Authentication System**: Secure login and password management
  - Bcrypt password hashing
  - Session-based authentication (24-hour expiration)
  - Default credentials: admin/admin
  - In-app password changes
  - Password reset via 6-digit email codes
  - Brute-force protection on reset attempts
  - Session cleanup and security features

- **Analytics Dashboard**: Visual insights into code executions
  - Total executions, success/failure counts and rates
  - Most active users leaderboard
  - Top groups leaderboard
  - Execution trends over time (configurable periods)
  - Filterable analytics by date range

- **Configuration System**: Flexible environment-based configuration
  - Toggle audit logging on/off
  - Toggle web interface on/off
  - Configurable database paths
  - Configurable retention policies
  - Configurable web server host/port
  - Support for password reset via account service integration

- **Command-Line Tools**:
  - `insyt-audit-web`: Start web dashboard server
  - Existing `insyt-secure` command unchanged

- **Documentation**:
  - `AUDIT_LOGGING_README.md`: Complete feature documentation
  - `MIGRATION_GUIDE.md`: Upgrade guide for existing deployments
  - `QUICK_START.md`: 5-minute getting started guide
  - `IMPLEMENTATION_SUMMARY.md`: Technical implementation details
  - `.env.example`: Configuration template
  - `examples/audit_logging_demo.py`: Working demo script

### Changed
- Updated version from 0.4.5 to 0.5.0
- Enhanced `CodeExecutor` to integrate automatic audit logging
- Updated `settings.py` with audit logging and web interface configuration
- Modified MQTT message processing to extract audit fields (query, user, group)

### Added Dependencies
- `flask>=3.0.0`: Web framework for dashboard
- `bcrypt>=4.0.0`: Secure password hashing
- `werkzeug>=3.0.0`: WSGI utilities (bundled with Flask)

### Security
- Secure password storage with bcrypt and salt
- Cryptographically secure session tokens
- Automatic session expiration
- Rate limiting on password reset attempts
- Localhost-only binding by default
- No sensitive data in logs (masked code/queries)

### Performance
- Compressed storage reduces database size by 70-80%
- Indexed database queries for fast filtering
- Pagination for efficient data loading
- Lazy loading of detail views
- Minimal execution overhead (< 5ms per request)
- Non-blocking audit logging

### Backward Compatibility
- ✅ **Fully backward compatible** - no breaking changes
- Existing code executors work without modifications
- MQTT message format unchanged (audit fields optional)
- All existing environment variables still supported
- Audit logging can be completely disabled if not needed

### Notes
- For audit logging to capture full context, MQTT messages should include:
  - `query`: User's natural language question
  - `user`: Username or email
  - `group`: Team/group affiliation (optional)
- If these fields are missing, execution still works (defaults used)
- Web dashboard requires first-time password change from default

## [0.3.7] - 2025-06-27

### Added
- Fixed `locals()` and `globals()` functions now available in secure execution environment
- Enhanced data analytics support with new built-ins: `slice`, `memoryview`, `bytes`, `bytearray`, `frozenset`, `iter`, `next`, `callable`, `super`, `object`, `delattr`
- Added data processing modules: `collections`, `itertools`, `functools`, `operator`, `statistics`, `decimal`, `csv`, `io`, `copy`, `heapq`, `bisect`, `uuid`, `hashlib`, `base64`, `string`, `textwrap`
- Object-oriented programming support with `property`, `staticmethod`, `classmethod` decorators

### Fixed
- Resolved `NameError: name 'locals' is not defined` in code execution environment

## [0.3.0] - 2025-05-14

### Added
- Support for managing one or more projects simultaneously
- Independent connection management for each project (separate credential handling and reconnection)
- Shared DNS cache across all project connections
- Command-line option `--projects` for specifying project configurations
- Support for environment variable `INSYT_PROJECTS` for project configuration

### Changed
- Enhanced project identification in logs
- Improved resource management for multiple concurrent connections

### Removed
- Legacy single-project mode using separate `--project-id` and `--api-key` parameters
- Projects must now be specified using the `--projects` parameter or `INSYT_PROJECTS` environment variable

## [0.2.9] - 2025-05-13

### Added
- DNS caching mechanism to improve resilience against DNS server outages
- Cached DNS resolutions are stored for up to 24 hours and used as fallback
- Initial release of version 0.2.6 