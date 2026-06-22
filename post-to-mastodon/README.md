# Post to Mastodon Action

This GitHub Action allows you to post content (toots) to Mastodon using the Mastodon REST API.

## Features

- Post text content to Mastodon (up to 500 characters by default)
- Attach multiple images or videos (using API v2 with automatic fallback to API v1)
- Include links in posts (appended to the status text)
- Scheduled posting (supports ISO 8601 or offset formats like `+1d`, `+2h`, `+30m`)
- Configurable logging levels
- Template interpolation support
- Proper cleanup of temporary downloaded media files
- Returns post ID and post URL for further processing
- Optional response summary file (`mastodon-response.json`) via `save-response` / `SAVE_RESPONSE`

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
This will post: `Hello Gerald, today is 2026-06-17 at 14:18:25!`

## Remote Media Files

All actions and the `social` CLI support HTTP or HTTPS URLs for supported media inputs. If a remote file is within the configured size limit, it is downloaded first and then uploaded from the local path.

- Set `MAX_DOWNLOAD_SIZE_MB` to change the download limit (default: 5 MB)
- If a remote file is too large or cannot be downloaded, the action logs an error and stops

## Prerequisites

To use this action, you need:

1. A Mastodon account on any Mastodon instance (e.g., `mastodon.social`, `me.dm`, etc.)
2. An access token with the `write:statuses` and `write:media` scopes:
   - Go to your Mastodon instance in a web browser
   - Navigate to **Preferences** -> **Development** -> **New Application**
   - Provide an application name (e.g., "GitHub Actions Poster")
   - Select the required scopes: `write:statuses` (to post status updates) and `write:media` (to upload media attachments)
   - Click **Submit**
   - Click on your newly created application and copy your **Your Access Token** (keep this token secret!)

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `server` | Mastodon server address (e.g. "mastodon.social" or "me.dm") | Yes | |
| `access-token` | Mastodon Access Token | Yes | |
| `content` | Content to post to Mastodon | Yes | |
| `link` | Link to attach/append to the post | No | |
| `media-files` | Comma-separated list of media files or URLs to attach | No | |
| `scheduled-publish-time` | Schedule post for future publication. Supports ISO 8601 (e.g., "2024-12-31T23:59:59Z") or offset format (e.g., "+1d", "+2h", "+30m") | No | |
| `log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | No | `INFO` |
| `content-json` | JSON API URL and path for dynamic content templating | No | |
| `time-zone` | Time zone for date/time placeholders (e.g. UTC, UTC+7) | No | |
| `dry-run` | Dry-run mode. If true, the content will be printed but not posted | No | `false` |
| `save-response` | Save response summary to `mastodon-response.json` (`success`, `error`, `post_id`, `post_url`) | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created status or scheduled status |
| `post-url` | Public URL of the created post, or reference URL for scheduled posts |

## Example Workflows

### Standard Posting Workflow

```yaml
name: Post to Mastodon

on:
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Post Status
        uses: ./.github/actions/post-to-mastodon
        with:
          server: 'mastodon.social'
          access-token: ${{ secrets.MASTODON_ACCESS_TOKEN }}
          content: 'Hello, world! Posting to Mastodon from GitHub Actions!'
```

### Scheduled Posting with Media and Templated Content

```yaml
name: Scheduled Media Toot

on:
  schedule:
    - cron: '0 12 * * *' # Every day at 12:00 PM UTC

jobs:
  toot:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Toot with Template and Image
        uses: ./.github/actions/post-to-mastodon
        with:
          server: 'me.dm'
          access-token: ${{ secrets.MASTODON_ACCESS_TOKEN }}
          content: 'Today is ${builtin.CURR_DATE}. Check out this beautiful image!'
          media-files: 'https://example.com/daily-photo.jpg'
          scheduled-publish-time: '+2h' # Schedule to publish 2 hours from now
```

## CLI Usage

If you installed the CLI package, you can also post to Mastodon from the command line:

```bash
# Set environment variables
export MASTODON_SERVER="mastodon.social"
export MASTODON_ACCESS_TOKEN="your_access_token"

# Post simple content
social mastodon --post-content "Post from social CLI"

# Post with media files, a link, and debug logging
social mastodon \
  --post-content "Check out our latest update!" \
  --post-link "https://github.com/geraldnguyen/social-media-posters" \
  --media-files "photo1.png,https://example.com/photo2.jpg" \
  --log-level DEBUG

# Scheduled toot
social mastodon \
  --post-content "Scheduled announcement!" \
  --scheduled-publish-time "+1d"
```
