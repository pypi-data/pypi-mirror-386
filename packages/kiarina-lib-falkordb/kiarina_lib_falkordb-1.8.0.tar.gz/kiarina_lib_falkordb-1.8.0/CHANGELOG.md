# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.0] - 2025-10-24

### Changed
- Updated `kiarina-falkordb` dependency from `>=1.2.0` to `>=1.3.0`

## [1.7.0] - 2025-10-21

### Changed
- No changes

## [1.6.3] - 2025-10-13

### Changed
- Updated `pydantic-settings-manager` dependency from `>=2.1.0` to `>=2.3.0`

## [1.6.2] - 2025-10-10

### Changed
- No changes

## [1.6.1] - 2025-10-10

### Changed
- No changes

## [1.6.0] - 2025-10-10

### Changed
- No changes

## [1.5.0] - 2025-10-10

### Changed
- No changes

## [1.4.0] - 2025-10-09

### Changed
- **BREAKING**: Changed `url` field to use `SecretStr` for enhanced security
  - FalkorDB connection URLs (which may contain passwords) are now masked in string representations and logs
  - Prevents accidental exposure of credentials in debug output
  - Access URL value via `.get_secret_value()` method when needed
  - Internal usage automatically handles secret extraction

### Security
- **Enhanced credential protection**: FalkorDB URLs with embedded credentials are now protected from accidental exposure
  - URLs are displayed as `**********` in logs and string representations
  - Follows the project-wide security policy for sensitive data

## [1.3.0] - 2025-10-05

### Changed
- No changes

## [1.2.0] - 2025-09-25

### Changed
- No changes

## [1.1.1] - 2025-01-15

### Changed
- Switched from `falkordb` to `kiarina-falkordb` dependency for better compatibility and maintenance

## [1.1.0] - 2025-09-11

### Changed
- No changes

## [1.0.1] - 2025-09-11

### Changed
- No changes - version bump for consistency with other packages

## [1.0.0] - 2025-09-09

### Added
- Initial release of kiarina-lib-falkordb
- FalkorDB client with configuration management using pydantic-settings-manager
- Connection pooling and caching
- Retry mechanism for connection failures
- Support for both sync and async operations (async prepared for future FalkorDB support)
- Type safety with full type hints and Pydantic validation
- Environment variable configuration support
- Runtime configuration overrides
- Multiple named configurations support

### Dependencies
- falkordb (from kiarina/falkordb-py fork with redis6 support)
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
- redis>=6.4.0
