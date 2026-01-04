# Post to Facebook Page Action

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

This GitHub Action allows you to post content to a Facebook Page using the Facebook Graph API.

## Features

- Post text content to Facebook Pages
- Attach media files (images, videos)
- Include links in posts
- Configurable logging levels
- Returns post ID and URL for further processing

## Prerequisites

You need to have a Facebook Page and create a Facebook App to get the required access token:

1. Go to the [Facebook Developers](https://developers.facebook.com/) portal
2. Create a new app or use an existing one
3. Add the "Pages" product to your app
4. Generate a Page Access Token with the following permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
5. Get your Page ID from your Facebook Page settings

## Usage

### For External Users

If you're using this action from another repository, reference it with the full repository path and version:

```yaml
- name: Post to Facebook Page
  uses: geraldnguyen/social-media-posters/post-to-facebook@v1.9.0
  with:
    access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
    page-id: ${{ secrets.FB_PAGE_ID }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/video.mp4"  # Optional
    link: "https://example.com"  # Optional
    log-level: "INFO"  # Optional
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post to Facebook Page
  uses: ./post-to-facebook
  with:
    access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
    page-id: ${{ secrets.FB_PAGE_ID }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/video.mp4"  # Optional
    link: "https://example.com"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `access-token` | Facebook Page Access Token | Yes | - |
| `page-id` | Facebook Page ID | Yes | - |
| `content` | Content to post to Facebook Page | Yes | - |
| `media-files` | Comma-separated list of media file paths | No | - |
| `link` | Link to attach to the post | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Example with Media and Link

```yaml
- name: Post to Facebook Page with media and link
  uses: geraldnguyen/social-media-posters/post-to-facebook@v1.9.0
  with:
    access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
    page-id: ${{ secrets.FB_PAGE_ID }}
    content: "Check out our latest blog post! 📖"
    media-files: "blog-images/featured.jpg"
    link: "https://blog.example.com/latest-post"
```

## Security Notes

- Store your Page Access Token as a GitHub repository secret
- Store your Page ID as a GitHub repository secret
- Never commit access tokens to your repository
- Use long-lived Page Access Tokens for production use

## GitHub Actions Best Practices

### Version Pinning
- **Always use a specific version tag** (e.g., `@v1.9.0`) in production workflows for stability
- **Test updates** in a non-production environment before upgrading
- **Check the changelog** for breaking changes when updating versions

### Action Reference Format
- **External repositories**: `geraldnguyen/social-media-posters/post-to-facebook@v1.9.0`
- **Local/same repository**: `./post-to-facebook` (requires checkout step first)

### Workflow Tips
- **Use appropriate log levels** (`DEBUG` for troubleshooting, `INFO` for production)
- **Implement error handling** with `continue-on-error` or conditional steps
- **Use template variables** for dynamic, reusable content
- **Store secrets securely** and never expose them in logs
- **Monitor API rate limits** to avoid throttling

### Example: Production-Ready Workflow

```yaml
name: Share on Facebook
on:
  release:
    types: [published]

jobs:
  post-to-facebook:
    runs-on: ubuntu-latest
    steps:
      - name: Post release to Facebook
        uses: geraldnguyen/social-media-posters/post-to-facebook@v1.9.0
        with:
          access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
          page-id: ${{ secrets.FB_PAGE_ID }}
          content: "🎉 We've just released version ${{ github.event.release.tag_name }}! Check out what's new."
          link: ${{ github.event.release.html_url }}
          log-level: "INFO"
        continue-on-error: true
```

## Supported Media Types

- **Images**: .jpg, .jpeg, .png, .gif
- **Videos**: .mp4, .mov, .avi

## Video Upload Improvements (v1.13.0)

This action now uses **Facebook's resumable upload API** for reliable video uploads, especially for large files:

### Features
- **Automatic upload method selection**: Small videos (<5MB by default) use simple upload, large videos use resumable upload
- **Chunked upload**: Large videos are uploaded in 4MB chunks to avoid timeout issues
- **Configurable threshold**: Set `VIDEO_UPLOAD_THRESHOLD_MB` environment variable to customize the size threshold (default: 5MB)
- **Extended timeout**: Chunk uploads have a 5-minute timeout for better reliability
- **Detailed logging**: Track upload progress with INFO level logging showing each chunk transfer

### Configuration

You can customize the video upload behavior with environment variables:

```yaml
- name: Post video to Facebook Page
  uses: geraldnguyen/social-media-posters/post-to-facebook@v1.13.0
  with:
    access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
    page-id: ${{ secrets.FB_PAGE_ID }}
    content: "Check out this video! 🎥"
    media-files: "path/to/large-video.mp4"
  env:
    VIDEO_UPLOAD_THRESHOLD_MB: 10  # Use resumable upload for videos >10MB
    LOG_LEVEL: DEBUG  # See detailed chunk upload progress
```

### How It Works

1. **Start Phase**: Initiates an upload session with Facebook, providing the video file size
2. **Transfer Phase**: Uploads the video in 4MB chunks with progress tracking
3. **Finish Phase**: Finalizes the upload and publishes the video with metadata (description, privacy settings)

This approach prevents timeout errors and provides better visibility into upload progress, especially for large video files.

## Limitations

- Media files must be accessible from the GitHub Actions runner
- Facebook has file size limits for media uploads
- Rate limits apply based on your Facebook App usage
- Multiple media files are uploaded separately (not as an album)

## Getting Page Access Token

1. Go to [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Select "Get Token" → "Get Page Access Token"
4. Choose your page
5. Grant the necessary permissions
6. Copy the generated token

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

## Templated Content: Post Retrieval Extraction

You can extract a sub-object from a remote JSON by specifying a path after a pipe (|) in the `CONTENT_JSON` variable. Example:

```
CONTENT_JSON=https://example.com/data.json | stories[0]
POST_CONTENT=API-driven: @{json.description}, @{json.permalink}
```
This will use the first element of the `stories` array as the root for all `@{json...}` lookups.

## Templated Content: [RANDOM] Array Element Picker

You can use `[RANDOM]` in the path to pick a random element from an array:

```
CONTENT_JSON=https://example.com/data.json | stories[RANDOM]
POST_CONTENT=API-driven: @{json.description}, @{json.permalink}
```
This will randomly select an element from the `stories` array for use in template lookups.

## Templated Content: List Operations

Array results can be processed in-place using pipe operators in your template expression:

### Basic Operations
- `each:prefix(str)`: prepend the string to every element returned
- `join(str)`: join all elements into a single string with the given separator

### Selection Operations
- `random()`: select a random element from a list (throws error if list is null or empty)
- `attr(name)`: extract the named attribute from each object in a list of objects

### Case Transformation Operations
- `each:case_title()`: convert each element to Title Case (`hello world` → `Hello World`)
- `each:case_sentence()`: convert each element to Sentence case (`hello world` → `Hello world`)
- `each:case_upper()`: convert each element to UPPERCASE (`hello world` → `HELLO WORLD`)
- `each:case_lower()`: convert each element to lowercase (`Hello WORLD` → `hello world`)
- `each:case_pascal()`: convert each element to PascalCase (`hello world` → `HelloWorld`)
- `each:case_kebab()`: convert each element to kebab-case (`hello world` → `hello-world`)
- `each:case_snake()`: convert each element to snake_case (`hello world` → `hello_world`)

Example:

```
CONTENT_JSON=https://example.com/data.json | stories[RANDOM]
POST_CONTENT=Hashtags: @{json.genres | each:case_lower() | each:prefix('#') | join(' ')}
```

If the story contains a `genres` array of `["MYTHOLOGY", "TRAGEDY", "SUPERNATURAL"]`, the rendered content will be:

```
Hashtags: #mythology #tragedy #supernatural
```

### Length Operations

You can control text length using length operations:

#### max_length Operation

Limits the length of a string with optional suffix.

```
@{json.description | max_length(100)}
@{json.title | max_length(50, '...')}
```

#### each:max_length Operation

Applies max_length to each item in a list.

```
@{json.tags | each:max_length(20) | join(' #')}
```

#### join_while Operation

Joins list items with a separator until a maximum length is reached.

```
@{json.tags | join_while(' #', 50)}
@{json.categories | join_while(', ', 100)}
```

### Length Operations Example

```
CONTENT_JSON=https://example.com/data.json | stories[RANDOM] 
POST_CONTENT=Summary: @{json.description | max_length(100, '...')} Tags: @{json.tags | join_while(' #', 50)}
```

This will clip the description at 100 characters (at word boundary) and join tags with '#' separator until the total length reaches 50 characters.

## Credits

- Built using [Facebook SDK for Python](https://github.com/mobolic/facebook-sdk) library
- Created by Gerald Nguyen
- Licensed under MIT License