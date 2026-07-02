# Post to TikTok

GitHub Action and CLI command to upload and publish videos to TikTok using the [TikTok Content Posting API v2](https://developers.tiktok.com/doc/content-posting-api-get-started).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Environment Variables](#environment-variables)
- [Usage — GitHub Action](#usage--github-action)
- [Usage — CLI](#usage--cli)
- [Authentication](#authentication)
- [Scheduling](#scheduling)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **TikTok Developer Account** — Register at [developers.tiktok.com](https://developers.tiktok.com).
2. **Registered App** — Create an app with the **Content Posting API** product enabled.
3. **Scopes** — Your app must request the `video.upload` and `video.publish` scopes.
4. **Access Token** — Obtain an OAuth2 access token (see [Authentication](#authentication)).

---

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `access-token` | Conditional | — | TikTok access token (with `video.upload` and `video.publish` scopes). Provide this **or** the refresh-token trio below. |
| `client-key` | Conditional | — | TikTok app Client Key. Required when using refresh-token authentication. |
| `client-secret` | Conditional | — | TikTok app Client Secret. Required when using refresh-token authentication. |
| `refresh-token` | Conditional | — | TikTok OAuth2 refresh token. Must be provided together with `client-key` and `client-secret`. |
| `video-file` | **Yes** | — | Local path **or** public HTTPS URL of the video file. |
| `content` | No | `""` | Video description/caption. **URLs are not permitted by TikTok in captions.** |
| `privacy-level` | No | `PUBLIC_TO_EVERYONE` | `PUBLIC_TO_EVERYONE` \| `MUTUAL_FOLLOW_FRIENDS` \| `FOLLOWER_OF_CREATOR` \| `SELF_ONLY` |
| `disable-duet` | No | `false` | Disable duet for this video. |
| `disable-comment` | No | `false` | Disable comments for this video. |
| `disable-stitch` | No | `false` | Disable stitch for this video. |
| `brand-content` | No | `false` | Mark as branded content (paid partnership). |
| `brand-organic` | No | `false` | Mark as organic branded content. |
| `is-aigc` | No | `false` | Mark as AI-generated content. |
| `cover-timestamp-ms` | No | `1000` | Millisecond offset within the video to use as cover image. |
| `video-publish-at` | No | — | Schedule future publishing. See [Scheduling](#scheduling). |
| `chunk-size-mb` | No | `10` | Upload chunk size in MB (5–64). Increase for better performance on fast connections. |
| `log-level` | No | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `content-json` | No | — | URL (with optional JSON path) for dynamic content templating. |
| `time-zone` | No | `UTC` | Time zone for built-in date/time placeholders. |
| `dry-run` | No | `false` | Print what would be posted without calling the TikTok API. |
| `save-response` | No | `false` | Save response summary to `tiktok-response.json`. |

---

## Outputs

| Output | Description |
|---|---|
| `video-id` | TikTok publish ID (or video ID when available). |
| `video-url` | URL of the published video (may be `null` for some account types). |

---

## Environment Variables

The script also accepts configuration via environment variables (useful for local runs):

| Variable | Description |
|---|---|
| `TIKTOK_ACCESS_TOKEN` | TikTok OAuth2 access token |
| `TIKTOK_CLIENT_KEY` | TikTok app Client Key |
| `TIKTOK_CLIENT_SECRET` | TikTok app Client Secret |
| `TIKTOK_REFRESH_TOKEN` | TikTok OAuth2 refresh token |
| `VIDEO_FILE` | Path or URL to the video file |
| `POST_CONTENT` | Video description/caption |
| `VIDEO_PRIVACY_LEVEL` | Privacy level (see Inputs table) |
| `TIKTOK_DISABLE_DUET` | `true`/`false` |
| `TIKTOK_DISABLE_COMMENT` | `true`/`false` |
| `TIKTOK_DISABLE_STITCH` | `true`/`false` |
| `TIKTOK_BRAND_CONTENT` | `true`/`false` |
| `TIKTOK_BRAND_ORGANIC` | `true`/`false` |
| `TIKTOK_IS_AIGC` | `true`/`false` |
| `TIKTOK_COVER_TIMESTAMP_MS` | Integer millisecond offset (default `1000`) |
| `VIDEO_PUBLISH_AT` | Schedule time (ISO 8601 or offset format) |
| `TIKTOK_CHUNK_SIZE_MB` | Upload chunk size in MB |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CONTENT_JSON` | JSON API URL and optional path for templating |
| `TIME_ZONE` | Time zone string (e.g. `Asia/Singapore`) |
| `DRY_RUN` | `true`/`false` |
| `SAVE_RESPONSE` | `true`/`false` |

---

## Usage — GitHub Action

### Instant publish with a local video file

```yaml
- name: Post to TikTok
  uses: your-org/social-media-posters/post-to-tiktok@main
  with:
    access-token: ${{ secrets.TIKTOK_ACCESS_TOKEN }}
    video-file: ./videos/my-video.mp4
    content: 'Check out my latest video!'
    privacy-level: PUBLIC_TO_EVERYONE
```

### Scheduled publish using a refresh token

```yaml
- name: Post to TikTok (scheduled)
  uses: your-org/social-media-posters/post-to-tiktok@main
  with:
    client-key: ${{ secrets.TIKTOK_CLIENT_KEY }}
    client-secret: ${{ secrets.TIKTOK_CLIENT_SECRET }}
    refresh-token: ${{ secrets.TIKTOK_REFRESH_TOKEN }}
    video-file: ./videos/weekly-update.mp4
    content: 'Weekly update coming tomorrow!'
    video-publish-at: '+1d'
    privacy-level: PUBLIC_TO_EVERYONE
```

### Publish from a remote URL with debug logging

```yaml
- name: Post to TikTok (remote video)
  uses: your-org/social-media-posters/post-to-tiktok@main
  with:
    access-token: ${{ secrets.TIKTOK_ACCESS_TOKEN }}
    video-file: 'https://cdn.example.com/my-video.mp4'
    content: 'Dynamic content from API: @{json.title}'
    content-json: 'https://api.example.com/posts.json | items[0]'
    log-level: DEBUG
    save-response: 'true'
```

---

## Usage — CLI

Install the package first:

```bash
pip install social-media-posters
```

### Instant publish

```bash
social tiktok \
  --tiktok-access-token "$TIKTOK_ACCESS_TOKEN" \
  --video-file ./my-video.mp4 \
  --post-content "Check out my latest video!" \
  --video-privacy-level PUBLIC_TO_EVERYONE
```

### Scheduled publish

```bash
social tiktok \
  --tiktok-client-key "$TIKTOK_CLIENT_KEY" \
  --tiktok-client-secret "$TIKTOK_CLIENT_SECRET" \
  --tiktok-refresh-token "$TIKTOK_REFRESH_TOKEN" \
  --video-file ./weekly-update.mp4 \
  --post-content "Weekly update" \
  --video-publish-at "+2h"
```

### Dry run (no API calls)

```bash
social tiktok \
  --tiktok-access-token "$TIKTOK_ACCESS_TOKEN" \
  --video-file ./my-video.mp4 \
  --post-content "Test caption" \
  --dry-run
```

---

## Authentication

TikTok uses **OAuth 2.0**. Two authentication modes are supported:

### 1. Access Token (simplest for CI/CD)

Obtain an access token via the TikTok OAuth2 flow, then store it as a secret:

```
TIKTOK_ACCESS_TOKEN=<your_access_token>
```

> **Note:** Access tokens expire after **24 hours**. For workflows that run frequently, use the refresh-token approach.

### 2. Refresh Token (recommended for long-running automation)

Store all three values as secrets:

```
TIKTOK_CLIENT_KEY=<app_client_key>
TIKTOK_CLIENT_SECRET=<app_client_secret>
TIKTOK_REFRESH_TOKEN=<refresh_token>
```

The script will automatically obtain a new access token before posting. Refresh tokens are valid for **30 days** and must be renewed periodically.

---

## Scheduling

Use the `video-publish-at` input (or `VIDEO_PUBLISH_AT` env var) to schedule a future post.

Supported formats:

| Format | Example | Description |
|---|---|---|
| ISO 8601 | `2024-12-31T23:59:59Z` | Exact UTC date-time |
| Offset | `+1d` | 1 day from now |
| Offset | `+2h` | 2 hours from now |
| Offset | `+30m` | 30 minutes from now |

**TikTok scheduling constraints:**
- The scheduled time must be **at least 20 minutes** in the future.
- The scheduled time must be **at most 10 days** in the future.
- The time is converted to a Unix timestamp and passed to the TikTok API.

---

## Limitations

The following limitations are imposed by the TikTok Content Posting API:

| Limitation | Details |
|---|---|
| **No URLs in captions** | TikTok does not allow clickable URLs or bare `http://`/`https://` links in video descriptions. Including a URL may result in the video being rejected or shadowbanned. |
| **Video duration** | Minimum **3 seconds**. Maximum depends on your account type: standard = **60 seconds**, verified creator = **3 minutes**, qualified creator = **10 minutes**. Query your limit via the creator info API. |
| **Video file size** | Practical maximum is **4 GB**. For videos up to 60 seconds the recommended maximum is **287.6 MB**. |
| **Supported video formats** | `.mp4`, `.mov`, `.webm`, `.mpeg` |
| **Supported video resolutions** | Minimum 360p; TikTok recommends 1080p or higher. |
| **Scheduling window** | 20 minutes → 10 days from now. |
| **Privacy levels** | `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY` |
| **Branded content** | Both `brand-content` and `brand-organic` toggles must comply with TikTok's Branded Content Policy. |
| **API access** | Requires a registered TikTok developer app with the Content Posting API product enabled and approved scopes (`video.upload`, `video.publish`). |
| **PULL_FROM_URL** | The remote video URL must be publicly accessible (no auth required). |
| **One video per call** | This action uploads exactly one video per run. |

---

## Troubleshooting

### `No TikTok access token available`

- Ensure `TIKTOK_ACCESS_TOKEN` is set **or** that all three of `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, and `TIKTOK_REFRESH_TOKEN` are set.

### `TikTok token refresh error`

- The refresh token may have expired (30-day lifetime). Re-authorise your app to obtain a new refresh token.

### `TikTok video init failed`

- Check the error message for details. Common causes: invalid privacy level, description too long, or missing API scopes.

### `TikTok publish failed: ...`

- Check `fail_reason` in the logs. Common causes: unsupported video format, video too short/long, or TikTok community guidelines violation.

### Video is stuck in `PROCESSING_UPLOAD` / `PROCESSING_DOWNLOAD`

- The action polls up to 30 times with 5-second intervals (2.5 minutes total). If TikTok processing takes longer, the action will exit with a timeout warning. The video may still appear on your profile once processing completes.

### Enable debug logging

Set `log-level: DEBUG` in the action input (or `LOG_LEVEL=DEBUG` env var / `--log-level DEBUG` CLI option) to see full request/response details.

GitHub Actions debug mode (`RUNNER_DEBUG=1` or `ACTIONS_STEP_DEBUG=true`) also automatically enables `DEBUG` logging.
