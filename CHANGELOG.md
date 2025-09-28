# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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