# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.0] - 2025-10-24

### Changed
- No changes

## [1.7.0] - 2025-10-21

### Added
- Added `.env.sample` file for environment variable configuration examples
- Added `test_settings.sample.yaml` file for test configuration examples

### Changed
- Improved test coverage with better error handling in async and sync tests
- Enhanced error handling in query operations and response views
- Updated test configuration setup in `conftest.py`

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

### Added
- Initial release of kiarina-lib-cloudflare-d1
- Cloudflare D1 client library with configuration management using pydantic-settings-manager
- `D1Settings`: Pydantic settings model for D1 configuration
  - `database_id`: Cloudflare D1 database ID (required)
- `D1Client`: Main client class for interacting with Cloudflare D1
  - `query()`: Execute SQL queries with parameterized statements
- `create_d1_client()`: Factory function to create D1 client instances
- `Result`: Query result container with success status and result data
  - `success`: Boolean indicating query success
  - `result`: List of query results
  - `first`: Property to access the first query result
- `QueryResult`: Individual query result with metadata and rows
  - `success`: Boolean indicating query success
  - `meta`: Query metadata (duration, rows read/written, etc.)
  - `results`: List of result rows
  - `rows`: Alias property for `results`
- Type safety with full type hints and Pydantic validation
- Support for both synchronous and asynchronous operations
  - Sync API: `kiarina.lib.cloudflare.d1`
  - Async API: `kiarina.lib.cloudflare.d1.asyncio`
- Environment variable configuration support with `KIARINA_LIB_CLOUDFLARE_D1_` prefix
- Runtime configuration overrides via `cli_args`
- Multiple named configurations support (e.g., production, staging)
- Seamless integration with kiarina-lib-cloudflare-auth for authentication
- Parameterized query support for SQL injection prevention
- HTTP client using httpx for reliable API communication

### Dependencies
- httpx>=0.28.1
- kiarina-lib-cloudflare-auth>=1.5.0
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
