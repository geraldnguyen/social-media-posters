# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.15.1] - 2026-01-14

### Added

- **YouTube Video Update Script** - New `update_youtube.py` script in the post-to-youtube folder
  - Update video metadata for existing YouTube videos
  - Support for updating title, description, tags, and category
  - Support for updating privacy status, embeddable, license, and stats visibility settings
  - Support for updating made-for-kids and synthetic media flags
  - Full templating support for dynamic content updates
  - Dry-run mode for testing updates before applying them
  - Proper error handling and detailed logging
  - Fetches current video details before updating to preserve unchanged fields

- **CLI Command for Video Updates** - New `update-youtube` command in the social CLI
  - Exposes all video update functionality via command-line interface
  - Supports all authentication methods (OAuth refresh token, service account)
  - Consistent with other CLI commands in the project
  - Examples: `social update-youtube --video-id VIDEO_ID --video-title "New Title"`

- **Comprehensive Unit Tests** - New test suite for update_youtube functionality
  - Tests for YouTubeUpdateAPI class initialization with various auth methods
  - Tests for get_video functionality
  - Tests for updating individual fields (title, description, tags, etc.)
  - Tests for updating multiple fields simultaneously
  - Tests for error handling (missing video ID, video not found, etc.)
  - All 16 tests pass successfully

### Changed

- **Documentation Updates**
  - Updated post-to-youtube/README.md with update video functionality
  - Added examples for using the update script via CLI and Python
  - Added environment variable reference for video updates
  - Added dry-run mode examples for updates
  - Updated features list to highlight update capability

### Fixed

- **Package Build Configuration** - Resolved module import errors and build failures (January 6, 2026)
  - Fixed `ModuleNotFoundError: No module named 'post_to_youtube'` when using the CLI
  - Fixed `error: package directory 'post-to-bluesky' does not exist` during `python -m build`
  - Created `__init__.py` files in all `post-to-*` directories to make them valid Python packages
  - Updated `MANIFEST.in` to properly include `post-to-*` directories with only `.py` and `.yml` files
  - Removed incorrect package configuration from `pyproject.toml` that referenced non-existent package directories
  - CLI now uses dynamic path-based imports instead of treating `post-to-*` folders as installed packages
  - Package can now be successfully built with `python -m build` and uploaded to PyPI
  - Both source distribution (sdist) and wheel builds now work correctly in isolated environments
  - `post-to-*` directories are now included as data files rather than separate packages
  - Scripts are loaded dynamically at runtime using `sys.path` manipulation
  - Maintains backward compatibility with existing functionality

## [1.13.0] - 2026-01-04

### Changed

- **Facebook Video Upload API** - Updated video posting to use Facebook's resumable upload API
  - Implemented chunked upload for large video files to prevent timeout errors
  - Videos larger than 5MB (configurable via `VIDEO_UPLOAD_THRESHOLD_MB`) use resumable upload with 4MB chunks
  - Videos smaller than the threshold use simple direct upload for efficiency
  - Extended timeout to 5 minutes for each chunk upload
  - Three-phase upload process: start session, transfer chunks, finish upload
  - Detailed progress logging for each chunk transfer
  - Proper error handling for session initialization and upload failures
  - Maintains backward compatibility with existing functionality
  - See: https://developers.facebook.com/docs/video-api/guides/publishing

### Added

- **Unit Tests** for Facebook video upload functionality (`post-to-facebook/test_post_to_facebook.py`)
  - Tests for small video simple upload method
  - Tests for large video resumable upload method
  - Tests for upload session start, transfer, and finish phases
  - Tests for chunked upload with multiple chunks and correct offsets
  - Tests for error handling (missing session ID, finish phase failure)
  - Tests for photo upload functionality

### Updated

- Documentation in `post-to-facebook/README.md` with new video upload improvements section
- Environment variable `VIDEO_UPLOAD_THRESHOLD_MB` for customizing upload method selection
- 00-PROMPTS.MD to mark v1.13.0 requirement as completed

### Fixed

- Facebook video upload timeout error: `('Connection aborted.', TimeoutError('The write operation timed out'))`
- Large video files can now be uploaded reliably without connection timeouts

## [1.12.0] - 2026-01-03

### Added

- **CLI Wrapper (`social` command)** - A unified command-line interface for all post-to-XYZ scripts
  - Single `social` command with subcommands for each platform (x, facebook, instagram, threads, linkedin, youtube, bluesky)
  - Common options across all commands: `--dry-run`, `--input-file`, `--content-json`, `--log-level`, `--post-content`, `--media-files`, `--max-download-size-mb`
  - Platform-specific options for API credentials and posting parameters
  - Version and help commands built-in
  - Seamless integration with existing post-to-XYZ Python scripts
  - Environment variable support through command-line options
  - Compatible with all templating engine features
  
- **Package Configuration** (`pyproject.toml`)
  - Installable Python package: `pip install social-media-posters`
  - Optional dependencies for each platform: `pip install -e ".[x]"`, `pip install -e ".[all]"`, etc.
  - Entry point: `social` command available after installation
  
- **Comprehensive CLI Guide** (`social_cli/GUIDE.md`)
  - Installation instructions for all platforms
  - Platform setup guides with credential requirements
  - 2+ usage examples for each platform (x, facebook, instagram, linkedin, youtube, bluesky, threads)
  - Configuration methods documentation (CLI options, environment variables, JSON config, .env files)
  - Templating engine usage examples
  - Troubleshooting section for common issues
  - Advanced usage patterns (batch processing, cron jobs, CI/CD integration, multi-platform posting)
  - Best practices and security guidelines
  
- **Unit Tests** (`social_cli/test_cli.py`)
  - Tests for all CLI commands (help, version, platform commands)
  - Tests for option-to-environment-variable mapping
  - Tests for common options across all commands
  - Integration tests with mocked API calls

### Updated

- Root README.md to feature the new CLI tool prominently at the top
- Repository now serves as both GitHub Actions and a CLI tool package

### Benefits

- **Unified Interface**: Single `social` command for all platforms
- **Ease of Use**: Post from terminal with simple commands
- **Automation Ready**: Use in shell scripts, cron jobs, or CI/CD pipelines
- **Consistent Experience**: Same options and patterns across all platforms
- **No GitHub Required**: Use locally without GitHub Actions
- **Flexible Configuration**: Multiple ways to provide credentials and parameters
- **Full Feature Support**: All templating, dry-run, and media features available

## [1.11.0] - 2026-01-02

### Added

- **JSON Configuration File Support** for all post-to-XYZ actions
  - Load parameters from a JSON configuration file (`input.json` by default)
  - Custom file path via `INPUT_FILE` environment variable
  - Support for both absolute and relative file paths
  - Automatic fallback if JSON file doesn't exist
  - Environment variables take precedence over JSON config values
  - Added `load_json_config()` function in `social_media_utils.py`
  - Updated `get_required_env_var()` and `get_optional_env_var()` to check JSON config
  - Updated `dry_run_guard()` to support JSON config for DRY_RUN parameter
  - **Automatic type conversion** for JSON values to string format:
    - Lists/Arrays converted to comma-separated strings (e.g., `["a", "b"]` → `"a,b"`)
    - Booleans converted to lowercase strings (e.g., `true` → `"true"`, `false` → `"false"`)
    - Numbers converted to strings (e.g., `42` → `"42"`)
    - Null converted to empty string
  - Comprehensive unit tests (`test_json_config_loading.py`, `test_json_value_conversion.py`)
  - Integration tests for all post-to-XYZ scripts (`test_json_config_integration.py`)
  - Documentation in README.md with examples and best practices

### Benefits

- Simplified local development and testing with JSON config files
- Easier management of multiple configurations for different environments
- Better organization of complex parameter sets
- Natural JSON syntax support (use native types like arrays, booleans, numbers)
- Maintains backward compatibility with environment variables and `.env` files
- Clear precedence: Environment Variables > JSON Config > .env File > Defaults

### Fixed

- JSON values are now automatically converted to strings to match environment variable behavior
- Resolves errors when using lists, booleans, or numbers in JSON config (e.g., `'list' object has no attribute 'split'`)

### Updated

- Root README.md to document JSON configuration feature and automatic type conversion
- 00-PROMPTS.MD to mark v1.11.0 requirement as completed

## [1.10.0] - 2025-12-29

### Added

- **Post to YouTube Action** (`post-to-youtube/`)
  - Complete YouTube video upload support using YouTube Data API v3
  - Support for video uploads from local files or remote URLs
  - Full video metadata support (title, description, tags, category)
  - Privacy settings (public, private, unlisted)
  - Scheduled video publishing with ISO 8601 format
  - Custom thumbnail upload support
  - Automatic playlist addition
  - Video settings support:
    - Made for kids flag
    - Embeddable flag
    - License type (YouTube or Creative Commons)
    - Public stats viewable flag
  - Full templating engine support for dynamic content
  - Dry-run mode for testing without uploading
  - Detailed logging with configurable log levels
  - Service account and API key authentication
  - Unit tests covering YouTube API integration (`test_post_to_youtube.py`)
  - Comprehensive documentation with setup instructions and examples
  - Compatible with all common features:
    - Remote media file download (videos up to 500MB)
    - Environment variable templating
    - JSON API templating with pipe operations
    - Built-in date/time placeholders
    - Case transformation operations
    - Length operations
    - List operations (prefix, join, random, attr)

### Updated

- Root README.md to include YouTube action in:
  - Available Actions section
  - Repository Structure
  - Prerequisites by Platform table
  - Rate Limits section
- 00-PROMPTS.MD to mark v1.10.0 requirement as completed

### Dependencies

- **YouTube Action**: python-dotenv, requests>=2.31.0, jsonpath-ng, google-api-python-client>=2.100.0, google-auth>=2.23.0, google-auth-oauthlib>=1.1.0, google-auth-httplib2>=0.1.1

## [1.9.0] - 2025-12-07

### Added

- **Post to LinkedIn Action** (`post-to-linkedin/`)
  - Complete LinkedIn posting support using LinkedIn API v2
  - Support for text posts up to 3000 characters
  - Image media attachment support (multiple images supported)
  - Link attachment support with automatic preview
  - Full templating engine support for dynamic content
  - Dry-run mode for testing without posting
  - Detailed logging with configurable log levels
  - OAuth 2.0 authentication support
  - Unit tests covering LinkedIn API integration (`test_post_to_linkedin.py`)
  - Comprehensive documentation with setup instructions and examples
  - Support for both personal and organization posts via author URN
  - Compatible with all common features:
    - Remote media file download
    - Environment variable templating
    - JSON API templating with pipe operations
    - Built-in date/time placeholders
    - Case transformation operations
    - Length operations
    - List operations (prefix, join, random, attr)

### Updated

- Root README.md to include LinkedIn action in:
  - Available Actions section
  - Repository Structure
  - Prerequisites by Platform table
  - Rate Limits section
- 00-PROMPTS.MD to mark v1.9.0 requirement as completed

### Dependencies

- **LinkedIn Action**: python-dotenv, requests>=2.31.0, jsonpath-ng

## [1.4.0] - 2025-11-12

### Added

- New pipeline operations for the templating engine:
  - `random()` - selects a random element from a list (throws error if list is null or empty)
  - `attr(name)` - extracts a named attribute from a JSON object (throws error if object is null or attribute doesn't exist)
- Unit tests covering the new operations (`test_templating_utils_random_attr.py`)
- Documentation updates in 00-PROMPTS.MD marking the feature as completed

## [1.3.0] - 2025-01-28

### Added

- Length operations for the templating engine, supporting:
  - `max_length(int, suffix?)` - limits string length with optional suffix
  - `each:max_length(int, suffix?)` - applies max_length to each item in a list
  - `join_while(separator, max_length)` - joins items until maximum length is reached
- Word-boundary aware truncation for better text formatting
- Unit tests covering all length operations (`test_templating_utils_length_operations.py`)
- Documentation updates across all action READMEs and the root README to explain the new length operations

## [1.2.0] - 2025-09-28

### Added

- Case transformation operations for the templating engine, supporting:
  - `each:case_title()` - converts to Title Case
  - `each:case_sentence()` - converts to Sentence case  
  - `each:case_upper()` - converts to UPPERCASE
  - `each:case_lower()` - converts to lowercase
  - `each:case_pascal()` - converts to PascalCase
  - `each:case_kebab()` - converts to kebab-case
  - `each:case_snake()` - converts to snake_case
- Unit tests covering all case transformation operations (`test_templating_utils_case_operations.py`).
- Documentation updates across all action READMEs and the root README to explain the new case transformation capabilities.

## [1.1.0] - 2025-09-28

### Added

- Pipeline list operations for the templating engine, supporting `each:prefix(str)` and `join(str)` inside template expressions.
- Unit tests covering the new templating operations (`test_templating_utils_json.py`).
- Documentation updates across all action READMEs and the root README to explain the new templating capabilities.

## [1.0.0] - 2025-01-06

### Added

#### GitHub Actions for Social Media Posting
- **Post to X (Twitter) Action** (`post-to-x/`)
  - Support for text posts up to 280 characters
  - Media attachment support (images and videos)
  - Uses X API v2 with OAuth 1.0a authentication
  - Built with Tweepy library
  - Comprehensive error handling and logging

- **Post to Facebook Page Action** (`post-to-facebook/`)
  - Support for text posts with no strict character limit
  - Media attachment support (images and videos)
  - Link attachment support
  - Uses Facebook Graph API
  - Built with Facebook SDK for Python
  - Handles both single media and multiple media files

- **Post to Instagram Action** (`post-to-instagram/`)
  - Support for image and video posts with captions (up to 2200 characters)
  - Strict image requirements validation (aspect ratio, resolution)
  - Requires publicly accessible media URLs
  - Uses Instagram Graph API
  - Built with Pillow for image validation

- **Post to Threads Action** (`post-to-threads/`)
  - Support for text posts up to 500 characters
  - Media attachment support via URLs
  - Link attachment support
  - Uses Threads API
  - Two-step posting process (create container, then publish)

#### Common Utilities (`common/`)
- `social_media_utils.py`: Shared functionality across all actions
  - Logging setup with configurable levels
  - Environment variable handling (required/optional)
  - Content validation with character limits
  - Consistent error handling
  - Media file parsing and validation
  - Success logging with post IDs

#### Documentation
- Individual README.md files for each action with:
  - Feature descriptions
  - Prerequisites and setup instructions
  - Usage examples
  - Input/output specifications
  - Security best practices
  - Troubleshooting guides
  - API requirements and limitations

- Main repository README.md with:
  - Overview of all available actions
  - Quick start guide
  - Example workflows
  - Security best practices
  - Repository structure
  - Contributing guidelines

#### Configuration Files
- `action.yml` files for each GitHub Action with proper metadata
- `requirements.txt` files specifying Python dependencies
- Proper branding and descriptions for GitHub Actions marketplace

### Security Features
- All API credentials handled via GitHub secrets
- No hardcoded credentials in any files
- Input validation to prevent injection attacks
- Secure environment variable handling

### Technical Features
- Python 3.11 compatibility
- Composite GitHub Actions for easy integration
- Consistent output format (post-id and post-url)
- Configurable logging levels
- Comprehensive error handling
- Rate limiting awareness

### Dependencies
- **X Action**: tweepy>=4.14.0, requests>=2.31.0
- **Facebook Action**: facebook-sdk>=3.1.0, requests>=2.31.0
- **Instagram Action**: requests>=2.31.0, pillow>=10.0.0
- **Threads Action**: requests>=2.31.0

### Platform Support
- X (Twitter) API v2
- Facebook Graph API v3.1
- Instagram Graph API
- Threads API (Meta)

### Known Limitations
- Instagram and Threads require publicly accessible media URLs (no local file support)
- X has 280 character limit for posts
- Threads has 500 character limit for posts
- Instagram has strict image/video requirements
- All platforms subject to their respective rate limits

---

## Format

This changelog follows the principles of [Keep a Changelog](https://keepachangelog.com/):

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes