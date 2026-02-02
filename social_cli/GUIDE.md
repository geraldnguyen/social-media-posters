# Social Media Posters CLI Guide

The `social` CLI provides a unified command-line interface for posting to various social media platforms. This guide covers installation, setup, usage examples, and troubleshooting.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Platform Setup](#platform-setup)
4. [Usage Examples](#usage-examples)
5. [Configuration Methods](#configuration-methods)
6. [Templating Engine](#templating-engine)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Installation

### Install from PyPI (when published)

```bash
pip install social-media-posters
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/geraldnguyen/social-media-posters.git
cd social-media-posters

# Install with all dependencies
pip install -e ".[all]"

# Or install with specific platform support
pip install -e ".[x,facebook,instagram]"
```

### Platform-Specific Installation

You can install only the dependencies you need:

```bash
# Only X (Twitter)
pip install -e ".[x]"

# Only Facebook
pip install -e ".[facebook]"

# Only Instagram
pip install -e ".[instagram]"

# YouTube support
pip install -e ".[youtube]"

# Multiple platforms
pip install -e ".[x,facebook,linkedin]"
```

## Quick Start

```bash
# Check version
social --version

# Get help
social --help

# Get help for a specific command
social x --help
```

## Platform Setup

### X (Twitter)

1. Create a Twitter Developer account at https://developer.twitter.com
2. Create an app and get your API credentials
3. Set up environment variables or use `.env` file:

```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

### Facebook

1. Create a Facebook App at https://developers.facebook.com
2. Get Page Access Token with required permissions
3. Set up environment variables:

```bash
FB_PAGE_ID=your_page_id
FB_ACCESS_TOKEN=your_access_token
```

### Instagram

1. Connect your Instagram account to a Facebook Page
2. Get Instagram Business Account access token
3. Set up environment variables:

```bash
IG_USER_ID=your_instagram_user_id
IG_ACCESS_TOKEN=your_access_token
```

### LinkedIn

1. Create a LinkedIn App at https://www.linkedin.com/developers
2. Get OAuth 2.0 access token
3. Get your author ID (person or organization URN)
4. Set up environment variables:

```bash
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_AUTHOR_ID=urn:li:person:your_id
```

### YouTube

1. Create a Google Cloud Project
2. Enable YouTube Data API v3
3. Set up OAuth 2.0 credentials or Service Account
4. Set up environment variables:

```bash
YOUTUBE_OAUTH_CLIENT_ID=your_client_id
YOUTUBE_OAUTH_CLIENT_SECRET=your_client_secret
YOUTUBE_OAUTH_REFRESH_TOKEN=your_refresh_token
```

### Bluesky

1. Create a Bluesky account at https://bsky.app
2. Use your username/email and password
3. Set up environment variables:

```bash
BLUESKY_IDENTIFIER=your.username.bsky.social
BLUESKY_PASSWORD=your_password
```

### Threads

1. Get Threads API access through Meta
2. Obtain user ID and access token
3. Set up environment variables:

```bash
THREADS_USER_ID=your_user_id
THREADS_ACCESS_TOKEN=your_access_token
```

## Usage Examples

### X (Twitter) Examples

#### Example 1: Simple Text Post

```bash
social x \
  --post-content "Hello from the social CLI! 🚀" \
  --x-api-key "$X_API_KEY" \
  --x-api-secret "$X_API_SECRET" \
  --x-access-token "$X_ACCESS_TOKEN" \
  --x-access-token-secret "$X_ACCESS_TOKEN_SECRET"
```

#### Example 2: Post with Media

```bash
social x \
  --post-content "Check out this amazing photo!" \
  --media-files "image.jpg,image2.png" \
  --dry-run
```

#### Example 3: Using Environment Variables

```bash
# Set environment variables
export X_API_KEY="your_key"
export X_API_SECRET="your_secret"
export X_ACCESS_TOKEN="your_token"
export X_ACCESS_TOKEN_SECRET="your_token_secret"
export POST_CONTENT="Posting from environment variables!"

# Run command
social x
```

### Facebook Examples

#### Example 1: Simple Text Post

```bash
social facebook \
  --fb-page-id "123456789" \
  --fb-access-token "your_token" \
  --post-content "Hello Facebook! 👋"
```

#### Example 2: Post with Link

```bash
social facebook \
  --post-content "Check out this article!" \
  --post-link "https://example.com/article" \
  --post-privacy "public"
```

#### Example 3: Post with Image

```bash
social facebook \
  --post-content "Beautiful sunset 🌅" \
  --media-files "sunset.jpg"
```

### Instagram Examples

#### Example 1: Post Image with Caption

```bash
social instagram \
  --ig-user-id "your_user_id" \
  --ig-access-token "your_token" \
  --post-content "Amazing view! #travel #nature" \
  --media-files "https://example.com/image.jpg"
```

#### Example 2: Post Video

```bash
social instagram \
  --post-content "Watch this! #video" \
  --media-files "https://example.com/video.mp4" \
  --dry-run
```

### Instagram via Facebook Examples (v1.19.0+)

The `instagram-via-fb` command uses Facebook's access token for Instagram posting. **Note**: All media must be hosted at publicly accessible URLs (Instagram API limitation).

#### Example 1: Post Video from URL

```bash
social instagram-via-fb \
  --ig-user-id "your_ig_user_id" \
  --fb-access-token "your_fb_access_token" \
  --post-content "Check out this amazing video! 🎥" \
  --media-files "https://cdn.example.com/video.mp4"
```

#### Example 2: Post Image from URL

```bash
social instagram-via-fb \
  --ig-user-id "your_ig_user_id" \
  --fb-access-token "your_fb_access_token" \
  --post-content "Beautiful photo! 📸" \
  --media-files "https://cdn.example.com/image.jpg"
```

#### Example 3: Carousel with Mixed Media

```bash
social instagram-via-fb \
  --post-content "My trip highlights! 🌍✈️" \
  --media-files "https://cdn.com/video.mp4,https://cdn.com/photo1.jpg,https://cdn.com/photo2.jpg" \
  --dry-run
```

#### Example 4: Using Environment Variables

```bash
export IG_USER_ID="your_ig_user_id"
export FB_ACCESS_TOKEN="your_fb_access_token"
export POST_CONTENT="New video! 🎥 #content"
export MEDIA_FILES="https://cdn.example.com/video.mp4"

social instagram-via-fb
```

**Note for Local Files**: If you have local files, upload them to S3, Cloudinary, or similar hosting first, then use the public URL.

### LinkedIn Examples

#### Example 1: Text Post

```bash
social linkedin \
  --linkedin-access-token "your_token" \
  --linkedin-author-id "urn:li:person:your_id" \
  --post-content "Excited to share my thoughts on AI! #AI #Tech"
```

#### Example 2: Post with Link

```bash
social linkedin \
  --post-content "Read my latest article on software architecture" \
  --post-link "https://blog.example.com/architecture"
```

#### Example 3: Post with Image

```bash
social linkedin \
  --post-content "Conference highlights! #conference" \
  --media-files "presentation.jpg"
```

### YouTube Examples

#### Example 1: Upload Video

```bash
social youtube \
  --video-file "my-video.mp4" \
  --video-title "My Amazing Video" \
  --video-description "This is a description" \
  --video-tags "tutorial,howto,educational" \
  --video-privacy-status "public"
```

#### Example 2: Schedule Video Upload

```bash
social youtube \
  --video-file "https://example.com/video.mp4" \
  --video-title "Scheduled Release" \
  --video-description "Coming soon!" \
  --video-privacy-status "private" \
  --video-publish-at "2026-12-31T10:00:00Z" \
  --dry-run
```

#### Example 3: Upload with Thumbnail and Playlist

```bash
social youtube \
  --video-file "video.mp4" \
  --video-title "Tutorial Part 1" \
  --video-description "First part of the series" \
  --video-thumbnail "thumbnail.jpg" \
  --playlist-id "PLxxxxxx" \
  --video-category-id "27"
```

### Bluesky Examples

#### Example 1: Simple Post

```bash
social bluesky \
  --bluesky-identifier "username.bsky.social" \
  --bluesky-password "your_password" \
  --post-content "Hello Bluesky! 🦋"
```

#### Example 2: Post with Link

```bash
social bluesky \
  --post-content "Check out this link!" \
  --post-link "https://example.com" \
  --dry-run
```

### Threads Examples

#### Example 1: Text Post

```bash
social threads \
  --threads-user-id "your_user_id" \
  --threads-access-token "your_token" \
  --post-content "Hello from Threads! 🧵"
```

#### Example 2: Post with Media

```bash
social threads \
  --post-content "Look at this!" \
  --media-files "https://example.com/image.jpg"
```

## Configuration Methods

The CLI supports multiple configuration methods with the following precedence (highest to lowest):

1. **Command-line options** (highest priority)
2. **Environment variables**
3. **JSON configuration file**
4. **.env file** (for local development)

### Using JSON Configuration File

Create a JSON file with your configuration:

```json
{
  "X_API_KEY": "your_api_key",
  "X_API_SECRET": "your_api_secret",
  "X_ACCESS_TOKEN": "your_access_token",
  "X_ACCESS_TOKEN_SECRET": "your_access_token_secret",
  "POST_CONTENT": "Hello from JSON config!",
  "LOG_LEVEL": "INFO",
  "DRY_RUN": "true"
}
```

Use it with the CLI:

```bash
# Default file (input.json in current directory)
social x

# Custom file path
social x --input-file config.json

# Or set environment variable
export INPUT_FILE=config.json
social x
```

### Using .env File

Create a `.env` file in your working directory:

```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
POST_CONTENT=Hello from .env file!
LOG_LEVEL=INFO
DRY_RUN=true
```

The CLI will automatically load this file.

## Templating Engine

The CLI supports a powerful templating engine for dynamic content:

### Environment Variables

```bash
social x --post-content "Posted at @{env.USER} time"
```

### Built-in Values

```bash
social x --post-content "Today is @{builtin.CURR_DATE}"
```

Available built-in values:
- `CURR_DATE` - Current date
- `CURR_TIME` - Current time
- `CURR_DATETIME` - Current date and time

### JSON API Templating

```bash
# Set content JSON URL
export CONTENT_JSON="https://api.example.com/data.json | stories[RANDOM]"

# Use values in content
social x --post-content "Story: @{json.title} - @{json.url}"
```

### Pipe Operations

Apply transformations to template values:

```bash
# Case transformations
social x --post-content "@{json.title | case_upper()}"

# Prefix and join
social facebook --post-content "Tags: @{json.tags | each:prefix('#') | join(' ')}"

# Length limiting
social x --post-content "@{json.description | max_length(200, '...')}"

# Random selection
social linkedin --post-content "@{json.stories | random() | attr(title)}"
```

### Advanced Features (v1.17.0+)

#### Optional Parentheses

Function calls can omit parentheses for cleaner syntax:

```bash
# Both syntaxes work:
social x --post-content "@{json.genres | each:prefix('#') | join(' ')}"
social x --post-content "@{json.genres | each:prefix '#' | join ' '}"
```

#### JSON Expressions as Parameters

Use JSON field values as function parameters:

```bash
# Use json.separator as the join separator
export CONTENT_JSON="https://api.example.com/data.json"
social x --post-content "@{json.items | join json.separator}"

# Use json.tag_prefix for dynamic prefixing
social facebook --post-content "@{json.tags | each:prefix json.tag_prefix | join ' '}"
```

#### Coalesce with `or` Operation

Use the first truthy (non-null, non-empty, non-blank) value:

```bash
# Use youtube_link if available, otherwise use permalink
social x --post-content "Watch: @{json.youtube_link | or json.permalink}"

# Chain multiple fallbacks
social facebook --post-content "@{json.title | or json.headline | or 'Untitled'}"

# Combine with other operations
social x --post-content "@{json.short_desc | or json.description | max_length(200, '...')}"
```

#### Complete Example

```bash
export CONTENT_JSON="https://tellstory.net/stories/random/index.json | stories[RANDOM]"

social x --post-content "@{json.description | max_length 150 '...'} @{json.youtube_link | or json.permalink} @{json.genres | each:prefix '#' | join ' '}"
```

## Troubleshooting

### Common Issues

#### 1. Module Import Errors

If you see import errors like `ModuleNotFoundError`:

```bash
# Ensure you're in the correct directory
cd /path/to/social-media-posters

# Reinstall the package
pip install -e ".[all]"
```

#### 2. Authentication Errors

- Verify your credentials are correct
- Check token expiration
- Ensure you have the required permissions
- Use `--dry-run` to test without posting

```bash
social x --dry-run --post-content "Test" --log-level DEBUG
```

#### 3. Media Upload Errors

- Verify file exists and is readable
- Check file size limits
- For remote URLs, ensure they're publicly accessible
- Verify media format is supported

```bash
# Test with smaller file
social instagram --media-files "small-image.jpg" --dry-run

# Check media file info
file image.jpg
ls -lh image.jpg
```

#### 4. Rate Limiting

- Use `--dry-run` for testing
- Add delays between posts
- Check platform-specific rate limits
- Monitor API usage

#### 5. Debugging

Enable debug logging to see detailed information:

```bash
social x --post-content "Debug test" --log-level DEBUG
```

### Platform-Specific Issues

#### X (Twitter)

- **280 character limit**: Use `max_length()` pipe operation
- **Media format**: Supports JPG, PNG, GIF, MP4
- **Rate limits**: Varies by access level

#### Facebook

- **Media types**: Supports images and videos
- **Privacy**: Use `--post-privacy public` or `private`
- **Link previews**: Automatically generated

#### Instagram

- **Media required**: Must include image or video
- **Aspect ratio**: 4:5 to 1.91:1 for images
- **Caption length**: Max 2200 characters
- **URL requirement**: Media must be publicly accessible

#### LinkedIn

- **Character limit**: 3000 characters
- **Media**: Images supported, videos not yet implemented
- **Links**: Automatic preview generation

#### YouTube

- **File size**: Up to 256GB or 12 hours
- **Formats**: MP4, AVI, MOV, WMV, FLV, 3GP, MPEG
- **Daily quota**: 10,000 units by default
- **Processing time**: Videos may take time to process

#### Bluesky

- **Character limit**: 300 characters
- **Media**: Supports images
- **Links**: Automatic card generation

#### Threads

- **Character limit**: 500 characters
- **Media**: Requires publicly accessible URLs
- **Two-step process**: Create container, then publish

## Advanced Usage

### Batch Processing with Scripts

Create a shell script for multiple posts:

```bash
#!/bin/bash

# batch-post.sh
posts=(
  "First post content"
  "Second post content"
  "Third post content"
)

for content in "${posts[@]}"; do
  social x --post-content "$content"
  sleep 5  # Wait between posts
done
```

### Using with Cron Jobs

Schedule automatic posts:

```bash
# Edit crontab
crontab -e

# Add scheduled post (daily at 9 AM)
0 9 * * * /usr/local/bin/social x --post-content "Good morning! ☀️"
```

### Integration with CI/CD

Use in GitHub Actions or other CI systems:

```yaml
# .github/workflows/social-post.yml
name: Post to Social Media

on:
  release:
    types: [published]

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install CLI
        run: pip install social-media-posters
      
      - name: Post to X
        env:
          X_API_KEY: ${{ secrets.X_API_KEY }}
          X_API_SECRET: ${{ secrets.X_API_SECRET }}
          X_ACCESS_TOKEN: ${{ secrets.X_ACCESS_TOKEN }}
          X_ACCESS_TOKEN_SECRET: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
        run: |
          social x --post-content "New release: ${{ github.event.release.tag_name }}"
```

### Environment Variable Profiles

Create different profiles for different environments:

```bash
# production.env
X_API_KEY=prod_key
X_API_SECRET=prod_secret
LOG_LEVEL=INFO

# development.env
X_API_KEY=dev_key
X_API_SECRET=dev_secret
LOG_LEVEL=DEBUG
DRY_RUN=true
```

Load specific profile:

```bash
# Load production config
export $(cat production.env | xargs)
social x --post-content "Production post"

# Load development config
export $(cat development.env | xargs)
social x --post-content "Development test"
```

### Content Templates

Create reusable content templates:

```bash
# templates/announcement.txt
🎉 Big announcement! @{json.title}

📝 @{json.description | max_length(150, '...')}

🔗 Learn more: @{json.url}

#announcement #updates

# Use template
export CONTENT_JSON="https://api.example.com/announcements/latest"
export POST_CONTENT="$(cat templates/announcement.txt)"
social x
```

### Multi-Platform Posting

Post to multiple platforms with one script:

```bash
#!/bin/bash

# multi-post.sh
CONTENT="$1"

echo "Posting to X..."
social x --post-content "$CONTENT"

echo "Posting to Facebook..."
social facebook --post-content "$CONTENT"

echo "Posting to LinkedIn..."
social linkedin --post-content "$CONTENT"

echo "Done!"
```

Use it:

```bash
./multi-post.sh "Hello from all platforms! 🚀"
```

## Best Practices

1. **Use Dry-Run First**: Always test with `--dry-run` before posting
2. **Secure Credentials**: Never commit credentials to version control
3. **Environment Variables**: Use environment variables or secret management
4. **Rate Limiting**: Respect platform rate limits
5. **Content Validation**: Verify content before posting
6. **Error Handling**: Check exit codes in scripts
7. **Logging**: Use appropriate log levels for debugging
8. **Backup Configs**: Keep backup copies of working configurations

## Getting Help

- Check this guide for common issues
- Use `--help` for command-specific information
- Check platform-specific documentation
- Review the [main README](../README.md) for more details
- Open an issue on [GitHub](https://github.com/geraldnguyen/social-media-posters/issues)

## Version Information

Current version: 1.13.0

Check your installed version:

```bash
social --version
```

## License

MIT License - see LICENSE file for details
