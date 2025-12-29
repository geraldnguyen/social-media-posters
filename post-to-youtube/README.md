# Post to YouTube Action

This GitHub Action allows you to upload videos to YouTube using the YouTube Data API v3.

## Features

- Upload videos to YouTube with full metadata support
- Support for both local video files and remote URLs
- Schedule video publishing for future dates/times
- Custom thumbnail upload
- Add videos to playlists automatically
- Full templating support for dynamic content
- Configurable logging levels
- Dry-run mode for testing
- Returns video ID and URL for further processing

## Template Interpolation

You can use template placeholders in your video title, description, and other text fields. The following sources are supported:

- `@{env.VAR}`: Replaced with the value of the environment variable `VAR`
- `@{builtin.CURR_DATE}`: Replaced with the current date in `YYYY-MM-DD` format
- `@{builtin.CURR_TIME}`: Replaced with the current time in `HH:MM:SS` format
- `@{builtin.CURR_DATETIME}`: Replaced with the current date and time in `YYYY-MM-DD HH:MM:SS` format
- `@{json...}`: Fetch and use values from remote JSON APIs (see below)

Example:

```env
VIDEO_TITLE='Weekly Update - @{builtin.CURR_DATE}'
VIDEO_DESCRIPTION='This week in @{env.PROJECT_NAME}: @{builtin.CURR_DATETIME}'
PROJECT_NAME='My Awesome Project'
```

This will create a video titled: `Weekly Update - 2025-12-29` with a description like `This week in My Awesome Project: 2025-12-29 08:48:59`

## Prerequisites

You need to set up YouTube Data API v3 access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials:
   - **Option A: Service Account** (Recommended for automation)
     - Create a service account
     - Download the JSON key file
     - Grant the service account access to your YouTube channel
   - **Option B: API Key** (Limited functionality, read-only operations)
     - Create an API key
     - Note: API keys cannot be used for video uploads; use service account instead

### Setting up Service Account for YouTube

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. The service account needs to be authorized to act on behalf of your YouTube channel
4. This typically requires OAuth 2.0 consent and delegation of authority

**Important**: YouTube Data API requires OAuth 2.0 for video uploads. Service accounts work best for automated workflows.

## Usage

### For External Users

If you're using this action from another repository, reference it with the full repository path and version:

```yaml
- name: Upload video to YouTube
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "path/to/video.mp4"
    title: "My Awesome Video Title"
    description: "A detailed description of my video"
    tags: "tutorial,github-actions,automation"
    privacy-status: "public"
    log-level: "INFO"
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Upload video to YouTube
  uses: ./post-to-youtube
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "path/to/video.mp4"
    title: "My Awesome Video Title"
    description: "A detailed description of my video"
    tags: "tutorial,github-actions,automation"
    privacy-status: "public"
    log-level: "INFO"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `api-key` | YouTube Data API service account JSON credentials | Yes | - |
| `channel-id` | YouTube Channel ID | No | - |
| `content` | Content/caption (for community posts, not yet fully supported) | No | - |
| `video-file` | Path to video file (local or URL) | No* | - |
| `title` | Video title (required for video uploads) | No* | - |
| `description` | Video description | No | "" |
| `tags` | Comma-separated list of video tags | No | - |
| `category-id` | Video category ID | No | 22 (People & Blogs) |
| `privacy-status` | Privacy status (public, private, unlisted) | No | public |
| `publish-at` | Schedule publication (ISO 8601: YYYY-MM-DDTHH:MM:SSZ) | No | - |
| `thumbnail` | Path to custom thumbnail (local or URL) | No | - |
| `playlist-id` | Playlist ID to add video to | No | - |
| `made-for-kids` | Whether video is made for kids (true/false) | No | false |
| `embeddable` | Whether video is embeddable (true/false) | No | true |
| `license` | Video license (youtube or creativeCommon) | No | youtube |
| `public-stats-viewable` | Whether stats are publicly viewable (true/false) | No | true |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `content-json` | JSON API URL and path for dynamic templating | No | - |
| `time-zone` | Time zone for date/time placeholders | No | UTC |
| `dry-run` | Dry run mode (true/false) | No | false |

\* Either `video-file` and `title` must be provided for video uploads

## Outputs

| Output | Description |
|--------|-------------|
| `video-id` | ID of the uploaded video |
| `video-url` | URL of the uploaded video |

## Video Category IDs

Common YouTube category IDs:

- `1` - Film & Animation
- `2` - Autos & Vehicles
- `10` - Music
- `15` - Pets & Animals
- `17` - Sports
- `19` - Travel & Events
- `20` - Gaming
- `22` - People & Blogs (default)
- `23` - Comedy
- `24` - Entertainment
- `25` - News & Politics
- `26` - Howto & Style
- `27` - Education
- `28` - Science & Technology

## Examples

### Basic Video Upload

```yaml
- name: Upload video to YouTube
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "recordings/demo.mp4"
    title: "Product Demo Video"
    description: "See our latest product features in action!"
    tags: "demo,product,tutorial"
    category-id: "28"  # Science & Technology
    privacy-status: "public"
```

### Video Upload with Remote File

```yaml
- name: Upload video from URL
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "https://example.com/videos/demo.mp4"
    title: "Remote Video Upload"
    description: "Video uploaded from a remote URL"
    privacy-status: "unlisted"
```

### Scheduled Video Upload

```yaml
- name: Schedule video publication
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "content/weekly-update.mp4"
    title: "Weekly Update - Episode 5"
    description: "This week's highlights and upcoming events"
    privacy-status: "private"
    publish-at: "2025-12-31T12:00:00Z"
    tags: "weekly,update,news"
```

**Note**: Scheduled publishing requires `privacy-status` to be set to `private`. The video will automatically become public at the scheduled time.

### Video with Custom Thumbnail and Playlist

```yaml
- name: Upload with thumbnail and add to playlist
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "tutorials/lesson-01.mp4"
    title: "Tutorial Lesson 1: Getting Started"
    description: "Learn the basics in this first lesson"
    tags: "tutorial,lesson,beginner"
    thumbnail: "thumbnails/lesson-01.jpg"
    playlist-id: "PLxxxxxxxxxxxxxxxxxxxxxx"
    category-id: "27"  # Education
```

### Video for Kids with Creative Commons License

```yaml
- name: Upload educational content for kids
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "kids-content/abc-song.mp4"
    title: "ABC Song for Kids"
    description: "Fun educational song for learning the alphabet"
    tags: "kids,education,alphabet,song"
    category-id: "27"  # Education
    made-for-kids: "true"
    license: "creativeCommon"
    privacy-status: "public"
```

## Templated Content: JSON Source

This action supports API-driven templated content using the `@{json...}` syntax. Example:

```yaml
- name: Upload video with dynamic content
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "generated/video.mp4"
    title: "@{json.title} - @{builtin.CURR_DATE}"
    description: "@{json.description}"
    tags: "@{json.tags | join(',')}"
    content-json: "https://example.com/api/video-metadata.json"
```

- The action will fetch the JSON from the URL in `content-json`
- It will extract values using the JSON path in the template
- Both dot notation and array bracket notation are supported
- Powered by the `jsonpath-ng` library

## Templated Content: Post Retrieval Extraction

You can extract a sub-object from remote JSON by specifying a path after a pipe (|):

```yaml
content-json: https://example.com/data.json | videos[0]
title: "@{json.title}"
description: "@{json.description}"
```

This uses the first element of the `videos` array as the root for all `@{json...}` lookups.

## Templated Content: [RANDOM] Array Element Picker

Use `[RANDOM]` in the path to pick a random element:

```yaml
content-json: https://example.com/data.json | videos[RANDOM]
title: "Random Video: @{json.title}"
```

## Templated Content: List Operations

Post-process array values using pipe operations:

### Basic Operations
- `each:prefix(str)` - add prefix to every element
- `join(str)` - concatenate all elements

### Selection Operations
- `random()` - select a random element (throws error if list is null/empty)
- `attr(name)` - extract named attribute from objects

### Case Transformation Operations
- `each:case_title()` - Title Case
- `each:case_sentence()` - Sentence case
- `each:case_upper()` - UPPERCASE
- `each:case_lower()` - lowercase
- `each:case_pascal()` - PascalCase
- `each:case_kebab()` - kebab-case
- `each:case_snake()` - snake_case

### Length Operations
- `max_length(int, str)` - clip text at word boundary with suffix
- `each:max_length(int, str)` - apply max_length to each element
- `join_while(str, int)` - join until maximum length reached

Example:

```yaml
content-json: https://example.com/data.json | videos[RANDOM]
tags: "@{json.tags | each:case_lower() | join(',')}"
```

## Dry-Run Mode

Set `dry-run` to `true` to test without actually uploading:

```yaml
- name: Test YouTube upload
  uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
  with:
    api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
    video-file: "test-video.mp4"
    title: "Test Upload"
    description: "Testing the upload process"
    dry-run: "true"
```

In dry-run mode, the action will:
- Process all templates
- Validate the video file
- Log detailed information
- NOT actually upload to YouTube

## Security Notes

- Store API credentials as GitHub repository secrets
- Never commit API keys or service account JSON to your repository
- Use the principle of least privilege for service account permissions
- Regularly audit and rotate credentials
- Be aware of YouTube API quotas and limits

## GitHub Actions Best Practices

### Version Pinning
- **Use specific version tags** (e.g., `@v1.10.0`) for stability
- **Test updates** before deploying to production
- **Check changelog** for breaking changes

### Action References
- **External**: `geraldnguyen/social-media-posters/post-to-youtube@v1.10.0`
- **Local**: `./post-to-youtube` (requires checkout step)

### Workflow Tips
- **Use dry-run mode** to test before uploading
- **Set appropriate log levels** (DEBUG for troubleshooting, INFO for production)
- **Implement error handling** with `continue-on-error` or conditionals
- **Store secrets securely** and never expose them in logs
- **Monitor API quotas** to avoid hitting limits

### Example: Production Workflow

```yaml
name: Weekly Video Upload
on:
  schedule:
    - cron: '0 12 * * 1'  # Every Monday at noon
  workflow_dispatch:

jobs:
  upload-video:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Upload to YouTube
        id: youtube
        uses: geraldnguyen/social-media-posters/post-to-youtube@v1.10.0
        with:
          api-key: ${{ secrets.YOUTUBE_SERVICE_ACCOUNT_JSON }}
          video-file: "weekly-content/latest.mp4"
          title: "Weekly Update - @{builtin.CURR_DATE}"
          description: "This week's highlights and updates"
          tags: "weekly,update,news"
          category-id: "22"
          privacy-status: "public"
          log-level: "INFO"
        continue-on-error: false
      
      - name: Log video URL
        if: success()
        run: |
          echo "Video uploaded successfully!"
          echo "Video URL: ${{ steps.youtube.outputs.video-url }}"
      
      - name: Notify on failure
        if: failure()
        run: |
          echo "Failed to upload video. Check the logs."
```

## Limitations

- Video file size limits apply (varies by YouTube account type)
- API quota limits apply (10,000 units per day by default)
- Community posts are not fully supported via API
- Service account setup can be complex
- OAuth 2.0 delegation may be required for some operations
- Uploaded videos may take time to process before becoming available

## Troubleshooting

### "Invalid credentials" error
- Verify your service account JSON is correct
- Ensure the service account has necessary permissions
- Check that YouTube Data API v3 is enabled in your project

### "Insufficient permissions" error
- Verify the service account has been granted access to your channel
- Check OAuth 2.0 scopes are correct
- Ensure your app has proper authorization

### "Quota exceeded" error
- Check your API quota usage in Google Cloud Console
- Request a quota increase if needed
- Implement rate limiting in your workflow

### Video upload fails
- Verify the video file exists and is accessible
- Check the video format is supported by YouTube
- Ensure file size is within limits
- Verify network connectivity for remote URLs

## YouTube API Documentation

- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Video Upload Guide](https://developers.google.com/youtube/v3/guides/uploading_a_video)
- [API Reference](https://developers.google.com/youtube/v3/docs)
- [Quota Management](https://developers.google.com/youtube/v3/getting-started#quota)

## Credits

- Built using YouTube Data API v3
- Created by Gerald Nguyen
- Licensed under MIT License
