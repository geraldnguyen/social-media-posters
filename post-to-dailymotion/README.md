# Post to Dailymotion Action

This GitHub Action allows you to upload videos to Dailymotion using the Dailymotion API.

## Features

- **Upload videos** to Dailymotion with metadata support (title, description, tags, channel, etc.)
- Support for both local video files and remote URLs
- Schedule video publishing for future dates/times
- Full templating support for dynamic content
- Configurable logging levels
- Dry-run mode for testing
- Returns video ID and URL for further processing

## Remote Media Files

All actions and the `social` CLI support HTTP or HTTPS URLs for supported media inputs. If a remote file is within the configured size limit, it is downloaded first and then uploaded from the local path.

- Set `MAX_DOWNLOAD_SIZE_MB` to change the download limit (default: 5 MB)
- If a remote file is too large or cannot be downloaded, the action logs an error and stops

## Template Interpolation

You can use template placeholders in your video title, description, and other text fields. The following sources are supported:

- `@{env.VAR}`: Replaced with the value of the environment variable `VAR`
- `@{builtin.CURR_DATE}`: Replaced with the current date in `YYYY-MM-DD` format
- `@{builtin.CURR_TIME}`: Replaced with the current time in `HH:MM:SS` format
- `@{builtin.CURR_DATETIME}`: Replaced with the current date and time in `YYYY-MM-DD HH:MM:SS` format
- `@{json...}`: Fetch and use values from remote JSON APIs

Example:

```env
VIDEO_TITLE='Weekly Update - @{builtin.CURR_DATE}'
VIDEO_DESCRIPTION='This week in @{env.PROJECT_NAME}: @{builtin.CURR_DATETIME}'
PROJECT_NAME='My Awesome Project'
```

## Prerequisites

You need to set up Dailymotion API access:

1. Go to the [Dailymotion Developer Portal](https://developer.dailymotion.com/)
2. Create a new App to get your **API Key (Client ID)** and **API Secret (Client Secret)**
3. Ensure your App has the necessary permissions for video uploads

## Usage

### Basic Usage

```yaml
- name: Upload video to Dailymotion
  uses: geraldnguyen/social-media-posters/post-to-dailymotion@v1.30.0
  with:
    client-id: ${{ secrets.DAILYMOTION_CLIENT_ID }}
    client-secret: ${{ secrets.DAILYMOTION_CLIENT_SECRET }}
    channel: "news"
    video-file: "path/to/video.mp4"
    title: "My Awesome Video Title"
    description: "A detailed description of my video"
```

### Inputs

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `client-id` | Dailymotion API Client ID | Yes | - |
| `client-secret` | Dailymotion API Client Secret | Yes | - |
| `channel` | Dailymotion Channel (category) for the video (e.g., news, sport, tech) | Yes | - |
| `video-file` | Path to video file (local or URL) | Yes | - |
| `title` | Video title | Yes | - |
| `description` | Video description | No | - |
| `tags` | Comma-separated list of video tags | No | - |
| `publish-at` | Schedule video publication (ISO 8601 or offset like +1d) | No | - |
| `made-for-kids` | Whether the video is made for kids (true/false) | No | `false` |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | `INFO` |
| `content-json` | JSON API URL and path for dynamic content templating | No | - |
| `time-zone` | Time zone for date/time placeholders | No | - |
| `dry-run` | Dry run mode. If true, prints content but does not post | No | `false` |

### Outputs

| Parameter | Description |
|-----------|-------------|
| `video-id` | ID of the uploaded video |
| `video-url` | URL of the uploaded video |

## Dailymotion Channels (Categories)

Common channels include:
- `news`
- `sport`
- `tech`
- `music`
- `fun`
- `lifestyle`
- `gaming`
- `auto`
- `travel`
- `tv`

Check Dailymotion documentation for a full list of supported channels.
