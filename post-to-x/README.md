# Post to X (Twitter) Action

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

This GitHub Action allows you to post content to X (formerly Twitter) using the X API v2.

## Features

- Post text content to X
- Attach media files (images, videos)
- Configurable logging levels
- Returns post ID and URL for further processing

## Prerequisites

You need to have an X Developer Account and create an app to get the required API credentials:

1. Go to the [X Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Get your API keys and tokens:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)
   - Access Token
   - Access Token Secret

## Usage

```yaml
- name: Post to X
  uses: ./post-to-x
  with:
    api-key: ${{ secrets.X_API_KEY }}
    api-secret: ${{ secrets.X_API_SECRET }}
    access-token: ${{ secrets.X_ACCESS_TOKEN }}
    access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/video.mp4"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `api-key` | X API Key (Consumer Key) | Yes | - |
| `api-secret` | X API Secret (Consumer Secret) | Yes | - |
| `access-token` | X Access Token | Yes | - |
| `access-token-secret` | X Access Token Secret | Yes | - |
| `content` | Content to post to X (max 280 characters) | Yes | - |
| `media-files` | Comma-separated list of media file paths | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Example with Media

```yaml
- name: Post to X with media
  uses: ./post-to-x
  with:
    api-key: ${{ secrets.X_API_KEY }}
    api-secret: ${{ secrets.X_API_SECRET }}
    access-token: ${{ secrets.X_ACCESS_TOKEN }}
    access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
    content: "Check out this amazing screenshot! 📸"
    media-files: "screenshots/demo.png"
```

## Templated Content: JSON Source

This action supports API-driven templated content using the `@{json...}` or `@{api...}` syntax. Example:

```
POST_CONTENT=API-driven: @{json.stories[0].description}, @{api.stories[0].permalink}
CONTENT_JSON=https://tellstory.net/stories/random/index.json
```

- The action will fetch the JSON from the URL in `CONTENT_JSON`.
- It will extract values using the JSON path in the template.
- Both dot notation and array bracket notation are supported.
- Powered by the `jsonpath-ng` library.

## Security Notes

- Store all API credentials as GitHub repository secrets
- Never commit API keys or tokens to your repository
- Use the principle of least privilege for your X app permissions

## Limitations

- Content is limited to 280 characters (X's character limit)
- Media files must be accessible from the GitHub Actions runner
- Rate limits apply based on your X API access level

## Credits

- Built using [Tweepy](https://github.com/tweepy/tweepy) library
- Created by Gerald Nguyen
- Licensed under MIT License