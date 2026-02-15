# Post to Bluesky Action

## Template Interpolation

You can use template placeholders in your post content. The following sources are supported:

- `${env.VAR}`: Replaced with the value of the environment variable `VAR` (e.g., `${env.NAME}`)
- `${builtin.CURR_DATE}`: Replaced with the current date in `YYYY-MM-DD` format
- `${builtin.CURR_TIME}`: Replaced with the current time in `HH:MM:SS` format
- `${builtin.CURR_DATETIME}`: Replaced with the current date and time in `YYYY-MM-DD HH:MM:SS` format

Example:

```env
POST_CONTENT='Hello ${env.NAME}, today is ${builtin.CURR_DATE} at ${builtin.CURR_TIME}!'
NAME=Gerald
```
This will post: `Hello Gerald, today is 2025-09-07 at 14:18:25!`

This GitHub Action allows you to post content to Bluesky using the official AT Protocol Python SDK.

## Features

- Post text content to Bluesky (up to 300 characters)
- Attach images (up to 4 images per post)
- Include links in posts
- Configurable logging levels
- Template interpolation support
- Returns post URI, CID, and URL for further processing

## Prerequisites

You need a Bluesky account to use this action:

1. Create a Bluesky account at [bsky.app](https://bsky.app/)
2. Generate an app password:
   - Go to Settings → Advanced → App Passwords
   - Create a new app password
   - Save this password securely (you won't be able to see it again)
3. Use your handle (e.g., `user.bsky.social`) or email as the identifier
4. Use the app password for authentication

## Usage

### For External Users

If you're using this action from another repository, reference it with the full repository path and version:

```yaml
- name: Post to Bluesky
  uses: geraldnguyen/social-media-posters/post-to-bluesky@v1.9.0
  with:
    identifier: ${{ secrets.BLUESKY_IDENTIFIER }}
    password: ${{ secrets.BLUESKY_PASSWORD }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/image2.png"  # Optional
    link: "https://example.com"  # Optional
    log-level: "INFO"  # Optional
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post to Bluesky
  uses: ./post-to-bluesky
  with:
    identifier: ${{ secrets.BLUESKY_IDENTIFIER }}
    password: ${{ secrets.BLUESKY_PASSWORD }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/image2.png"  # Optional
    link: "https://example.com"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `identifier` | Bluesky identifier (handle or email) | Yes | - |
| `password` | Bluesky password or app password | Yes | - |
| `content` | Content to post to Bluesky (max 300 chars) | Yes | - |
| `media-files` | Comma-separated list of image file paths (max 4) | No | - |
| `link` | Link to include in the post | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `content-json` | JSON API URL and path for dynamic content templating | No | - |
| `time-zone` | Time zone for date/time placeholders | No | - |
| `dry-run` | Dry run mode - print but don't post | No | false |

## Outputs

| Output | Description |
|--------|-------------|
| `post-uri` | AT Protocol URI of the created post |
| `post-cid` | Content ID (CID) of the created post |
| `post-url` | URL of the created post |

## Example with Media

```yaml
- name: Post to Bluesky with images
  uses: geraldnguyen/social-media-posters/post-to-bluesky@v1.9.0
  with:
    identifier: ${{ secrets.BLUESKY_IDENTIFIER }}
    password: ${{ secrets.BLUESKY_PASSWORD }}
    content: "Check out these awesome images! 📸"
    media-files: "images/photo1.jpg,images/photo2.png"
```

## Example with Template Interpolation

```yaml
- name: Post daily update to Bluesky
  uses: geraldnguyen/social-media-posters/post-to-bluesky@v1.9.0
  with:
    identifier: ${{ secrets.BLUESKY_IDENTIFIER }}
    password: ${{ secrets.BLUESKY_PASSWORD }}
    content: "Daily update for ${builtin.CURR_DATE} 🌟"
    log-level: "DEBUG"
```

## Security Notes

- Store your Bluesky identifier as a GitHub repository secret
- Store your app password as a GitHub repository secret
- **Never commit passwords to your repository**
- Use app passwords instead of your main account password
- App passwords can be revoked if compromised

## GitHub Actions Best Practices

### Version Pinning
- **Always use a specific version tag** (e.g., `@v1.9.0`) in production workflows for stability
- **Test updates** in a non-production environment before upgrading
- **Check the changelog** for breaking changes when updating versions

### Action Reference Format
- **External repositories**: `geraldnguyen/social-media-posters/post-to-bluesky@v1.9.0`
- **Local/same repository**: `./post-to-bluesky` (requires checkout step first)

### Workflow Tips
- **Respect the 300-character limit** for Bluesky posts
- **Use app passwords** for better security (can be revoked without changing main password)
- **Implement error handling** with `continue-on-error` or conditional steps
- **Use template variables** for dynamic, reusable content
- **Store secrets securely** and never expose them in logs
- **Use dry-run mode** to test posts before going live

### Example: Production-Ready Workflow

```yaml
name: Post to Bluesky
on:
  workflow_dispatch:
    inputs:
      message:
        description: 'Message to post'
        required: true

jobs:
  post-to-bluesky:
    runs-on: ubuntu-latest
    steps:
      - name: Post to Bluesky
        uses: geraldnguyen/social-media-posters/post-to-bluesky@v1.9.0
        with:
          identifier: ${{ secrets.BLUESKY_IDENTIFIER }}
          password: ${{ secrets.BLUESKY_PASSWORD }}
          content: ${{ github.event.inputs.message }}
          log-level: "INFO"
        continue-on-error: false
```

## Supported Media Types

- **Images**: .jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif (expanded in v1.23.0)
- Maximum 4 images per post
- Videos are not currently supported

## Limitations

- Post content is limited to 300 characters (Bluesky platform limit)
- Maximum 4 images per post (Bluesky platform limit)
- Video uploads are not currently supported
- Link cards require additional metadata fetching (currently links are included as text)

## AT Protocol SDK

This action uses the official [atproto](https://pypi.org/project/atproto/) Python SDK which provides a clean, typed interface for interacting with Bluesky and other AT Protocol services. The SDK handles:

- Authentication and session management
- Blob (media) uploads with proper MIME type detection
- Post creation with structured data models
- Error handling and retries

Key SDK methods used:
- `Client.login()` - Authenticate with Bluesky
- `Client.upload_blob()` - Upload images
- `Client.send_post()` - Create posts with text and embedded media

## Troubleshooting

### Authentication Errors

- Ensure you're using an app password, not your main account password
- Verify your identifier is correct (handle or email)
- Check that your app password hasn't been revoked

### Media Upload Errors

- Ensure image files exist and are accessible
- Check file formats are supported (.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif)
- Verify you're not exceeding the 4 image limit

### Content Length Errors

- Keep posts under 300 characters
- Use the `validate_post_content` function to check length before posting

## Local Testing

You can test this action locally by creating a `.env` file in the `post-to-bluesky` directory:

```env
BLUESKY_IDENTIFIER=your.handle.bsky.social
BLUESKY_PASSWORD=your-app-password
POST_CONTENT=Test post content
LOG_LEVEL=DEBUG
DRY_RUN=true
```

Then run:

```bash
python post_to_bluesky.py
```

## License

This action is part of the social-media-posters project. See the main repository LICENSE file for details.
