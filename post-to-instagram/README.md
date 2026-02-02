# Post to Instagram Action

## 🆕 v1.19.0: Instagram via Facebook with Resumable Upload

This version introduces a new posting method that uploads media files directly to Meta's servers using Facebook's resumable upload API before publishing to Instagram. This is particularly useful for:
- **Video uploads**: Uses resumable upload for reliable large video transfers
- **Local media files**: Supports uploading local video files instead of requiring pre-hosted URLs
- **Better reliability**: Chunked uploads with automatic retry capability

### Two Posting Methods Available

1. **Original Method** (`post_to_instagram.py`): Uses Instagram Graph API with public URLs
2. **New Method** (`post_to_instagram_via_fb.py`): Uses Facebook's infrastructure with resumable upload

**Choose the new method if you:**
- Have local video files to upload
- Need more reliable video uploads with resume capability
- Want to use Facebook's access token for Instagram posting

**Stick with the original method if you:**
- Already have media hosted at public URLs
- Only posting images (which still require URLs in the new method)
- Prefer the simpler URL-based approach

## Template Interpolation

You can use template placeholders in your post content and media file URLs. The following sources are supported:

- `${env.VAR}`: Replaced with the value of the environment variable `VAR` (e.g., `${env.NAME}`)
- `${builtin.CURR_DATE}`: Replaced with the current date in `YYYY-MM-DD` format
- `${builtin.CURR_TIME}`: Replaced with the current time in `HH:MM:SS` format
- `${builtin.CURR_DATETIME}`: Replaced with the current date and time in `YYYY-MM-DD HH:MM:SS` format

Template interpolation works for:
- **Content**: Post captions
- **Media files**: Both `media-file` and `media-files` inputs

Example:

```env
POST_CONTENT='Hello ${env.NAME}, today is ${builtin.CURR_DATE} at ${builtin.CURR_TIME}!'
MEDIA_FILE='https://example.com/images/${builtin.CURR_DATE}/photo.jpg'
NAME=Gerald
```
This will post: `Hello Gerald, today is 2025-09-07 at 14:18:25!` with media from `https://example.com/images/2025-09-07/photo.jpg`

This GitHub Action allows you to post content to Instagram using the Instagram Graph API.

## Features

- **v1.19.0+**: Upload local video files using Facebook's resumable upload API
- **v1.19.0+**: More reliable video uploads with chunked transfer and retry capability
- Post single images and videos to Instagram
- Create carousel posts with multiple images/videos (up to 10 media files)
- Add captions to posts
- Template interpolation support
- Configurable logging levels
- Returns post ID and URL for further processing

## Installation Methods

### Method 1: Instagram via Facebook (v1.19.0+) - **Recommended for Videos**

Use this method to upload local video files with resumable upload:

```yaml
- name: Post video to Instagram (via Facebook)
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.19.0
  with:
    use-fb-method: true  # Enable Facebook resumable upload
    access-token: ${{ secrets.FB_ACCESS_TOKEN }}  # Facebook access token
    user-id: ${{ secrets.IG_USER_ID }}  # Instagram User ID
    content: "Check out this amazing video! 🎥"
    media-files: "/path/to/local/video.mp4"  # Local video file
```

### Method 2: Original Instagram Graph API - **Recommended for Images**

Use this method with pre-hosted media URLs:

```yaml
- name: Post image to Instagram  
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.19.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}  # Instagram access token
    user-id: ${{ secrets.IG_USER_ID }}
    content: "Check out this amazing photo! 📸"
    media-file: "https://example.com/hosted-image.jpg"  # Must be publicly accessible URL
```

## Prerequisites

You need to have an Instagram Business or Creator account and create a Facebook App:

1. Convert your Instagram account to a Business or Creator account
2. Create a Facebook Page and connect it to your Instagram account
3. Go to the [Facebook Developers](https://developers.facebook.com/) portal
4. Create a new app or use an existing one
5. Add the "Instagram Basic Display" product to your app
6. Generate an access token with the following permissions:
   - `instagram_graph_user_profile`
   - `instagram_graph_user_media`
7. Get your Instagram User ID

## Usage

### For External Users

**Single Media Post:**

```yaml
- name: Post single image to Instagram
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "Check out this amazing photo! 📸"
    media-file: "https://example.com/hosted-image.jpg"  # Must be publicly accessible URL
```

**Carousel Post (Multiple Images):**

```yaml
- name: Post carousel to Instagram
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "My photo series! 📸 #carousel #photos"
    media-files: "https://example.com/image1.jpg,https://example.com/image2.jpg,https://example.com/image3.jpg"
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post to Instagram
  uses: ./post-to-instagram
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "Check out this amazing photo! 📸"
    media-file: "https://example.com/hosted-image.jpg"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `access-token` | Instagram User Access Token | Yes | - |
| `user-id` | Instagram User ID | Yes | - |
| `content` | Caption for the Instagram post (max 2200 characters) | Yes | - |
| `media-file` | Publicly accessible URL to single image or video file (use either media-file OR media-files) | No* | - |
| `media-files` | Comma-separated list of publicly accessible media URLs for carousel (max 10, use either media-file OR media-files) | No* | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

*Either `media-file` or `media-files` must be provided, but not both.

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Important Notes

### Media File Requirements

**The media file must be a publicly accessible URL.** Instagram's API requires that media files be hosted on a public server. You cannot use local file paths.

**Image Requirements:**
- Minimum resolution: 320x320 pixels
- Aspect ratio: Between 0.8 and 1.91
- Supported formats: JPEG, PNG
- Maximum file size: 8MB

**Video Requirements:**
- Minimum resolution: 320x320 pixels
- Aspect ratio: Between 0.8 and 1.91
- Supported formats: MP4, MOV
- Maximum file size: 100MB
- Maximum duration: 60 seconds

### Carousel Posts

Instagram supports carousel posts with multiple images and videos in a single post. Use the `media-files` input to create carousel posts.

**Carousel Requirements:**
- Maximum 10 media files per carousel
- All media files must be publicly accessible URLs
- Mixed content allowed (images + videos)
- Same caption applies to the entire carousel
- Individual media items cannot have separate captions

**Example Carousel Post:**
```yaml
- name: Post carousel to Instagram
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "My photo series! 📸 #carousel"
    media-files: "https://example.com/photo1.jpg,https://example.com/photo2.jpg,https://example.com/video.mp4"
```

### Example with Image Hosting

```yaml
- name: Upload image and post to Instagram
  runs-on: ubuntu-latest
  steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    # Upload your image to a hosting service first
    - name: Upload to hosting service
      run: |
        # Upload your image to AWS S3, Cloudinary, or similar
        # and get the public URL
        echo "IMAGE_URL=https://your-hosting-service.com/image.jpg" >> $GITHUB_ENV
    
    - name: Post to Instagram
      uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
      with:
        access-token: ${{ secrets.IG_ACCESS_TOKEN }}
        user-id: ${{ secrets.IG_USER_ID }}
        content: "Check out this amazing photo! 📸 #photography"
        media-file: ${{ env.IMAGE_URL }}
```

## Security Notes

- Store your access token as a GitHub repository secret
- Store your user ID as a GitHub repository secret
- Never commit access tokens to your repository
- Use long-lived access tokens for production use

## GitHub Actions Best Practices

### Version Pinning
- **Always use a specific version tag** (e.g., `@v1.9.0`) in production workflows for stability
- **Test updates** in a non-production environment before upgrading
- **Check the changelog** for breaking changes when updating versions

### Action Reference Format
- **External repositories**: `geraldnguyen/social-media-posters/post-to-instagram@v1.9.0`
- **Local/same repository**: `./post-to-instagram` (requires checkout step first)

### Workflow Tips
- **Media files must be publicly accessible URLs** (Instagram API requirement)
- **Respect Instagram's content policies** and guidelines
- **Use appropriate aspect ratios** (0.8 to 1.91) for best results
- **Test with different image sizes** before production use
- **Implement error handling** with `continue-on-error` or conditional steps
- **Use template variables** for dynamic, reusable content
- **Store secrets securely** and never expose them in logs
- **Monitor API rate limits** to avoid throttling

### Example: Production-Ready Workflow

```yaml
name: Post to Instagram
on:
  workflow_dispatch:
    inputs:
      caption:
        description: 'Post caption'
        required: true
      image_url:
        description: 'Public URL of the image'
        required: true

jobs:
  post-to-instagram:
    runs-on: ubuntu-latest
    steps:
      - name: Post to Instagram
        uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
        with:
          access-token: ${{ secrets.IG_ACCESS_TOKEN }}
          user-id: ${{ secrets.IG_USER_ID }}
          content: ${{ github.event.inputs.caption }}
          media-file: ${{ github.event.inputs.image_url }}
          log-level: "INFO"
        continue-on-error: false
      
      - name: Notify on success
        if: success()
        run: echo "Successfully posted to Instagram!"
```

## Getting Instagram Access Token

1. Follow the [Instagram Basic Display API documentation](https://developers.facebook.com/docs/instagram-basic-display-api/getting-started)
2. Use the [Instagram Graph API Explorer](https://developers.facebook.com/tools/explorer/)
3. Generate a long-lived access token for production use

## v1.19.0: Instagram via Facebook Method Details

### Overview

The Instagram via Facebook method (v1.19.0+) uses Facebook's Graph API infrastructure to upload media files directly to Meta's servers before publishing to Instagram. This provides better reliability, especially for video uploads.

### Key Benefits

1. **Resumable Video Uploads**: Videos are uploaded in 4MB chunks with automatic resume capability
2. **Local File Support**: Upload videos directly from local files (no need to host them first)
3. **Better Reliability**: Chunked uploads prevent timeout errors for large files
4. **Status Monitoring**: Automatic waiting for video processing before publishing

### How It Works

1. **For Videos**:
   - Video is uploaded in chunks to Meta's servers using resumable upload (start/transfer/finish flow)
   - System waits for video processing to complete
   - Video container is published to Instagram

2. **For Images**:
   - Images still require publicly accessible URLs (Instagram API limitation)
   - Image container is created with the URL
   - Container is published to Instagram

3. **For Carousels**:
   - Each media item is processed individually
   - All containers are combined into a carousel
   - Carousel is published with the caption

### Environment Variables (via FB Method)

| Variable | Description | Required |
|----------|-------------|----------|
| `IG_USER_ID` | Instagram Business/Creator User ID | Yes |
| `FB_ACCESS_TOKEN` | Facebook Access Token with Instagram permissions | Yes |
| `POST_CONTENT` | Post caption (max 2200 characters) | Yes |
| `MEDIA_FILES` | Comma-separated list of media paths/URLs | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `DRY_RUN` | Set to "true" to test without posting | No |
| `MAX_DOWNLOAD_SIZE_MB` | Max size for downloading remote videos (default: 500MB) | No |

### Usage Examples

**Local Video Upload:**

```bash
# Using environment variables
export IG_USER_ID="your_ig_user_id"
export FB_ACCESS_TOKEN="your_fb_access_token"
export POST_CONTENT="Check out this video! 🎥 #video"
export MEDIA_FILES="/path/to/video.mp4"

python post-to-instagram/post_to_instagram_via_fb.py
```

**Carousel with Mixed Media:**

```bash
export MEDIA_FILES="/path/to/video.mp4,https://example.com/image1.jpg,https://example.com/image2.jpg"
export POST_CONTENT="My amazing carousel! 📸🎥"

python post-to-instagram/post_to_instagram_via_fb.py
```

**Using CLI:**

```bash
# Install CLI
pip install -e ".[instagram]"

# Post video
social instagram-via-fb \
  --ig-user-id "your_ig_user_id" \
  --fb-access-token "your_token" \
  --post-content "Video post! 🎥" \
  --media-files "/path/to/video.mp4" \
  --dry-run
```

### Requirements for FB Method

**Facebook Access Token:**
- Must have `instagram_content_publish` permission
- Must have access to the linked Instagram Business/Creator account
- Can be obtained via Facebook Graph API Explorer

**Instagram Account:**
- Must be a Business or Creator account
- Must be linked to a Facebook Page
- Instagram User ID can be obtained via Graph API

**Media Requirements:**

*Videos (Local or URL):*
- Formats: MP4, MOV
- Maximum file size: 500MB (configurable)
- Minimum resolution: 320x320 pixels
- Uploaded using resumable upload with 4MB chunks

*Images (URL only):*
- Must be publicly accessible URLs
- Formats: JPEG, PNG
- Minimum resolution: 320x320 pixels
- Aspect ratio: Between 0.8 and 1.91

### Troubleshooting (FB Method)

**"Video processing failed or timed out"**
- Check that your video meets Instagram's format requirements
- Ensure the video file is not corrupted
- Try with a smaller video file

**"Image file must be a publicly accessible URL"**
- Images still require public URLs (Instagram API limitation)
- Upload images to S3, Cloudinary, or similar hosting service
- Use the URL in MEDIA_FILES

**"Upload session failed"**
- Check your Facebook access token has correct permissions
- Verify your Instagram account is linked to a Facebook Page
- Ensure your token hasn't expired

### Comparison: Original vs FB Method

| Feature | Original Method | FB Method (v1.19.0) |
|---------|----------------|---------------------|
| Video Upload | URL only | Local files + URLs |
| Image Upload | URL only | URL only |
| Upload Method | Direct URL | Resumable chunks (videos) |
| Reliability | Good | Better (chunked) |
| File Size Limit | Per Instagram API | Up to 500MB (configurable) |
| Best For | Pre-hosted media | Local video files |

## Limitations

- **Media files must be publicly accessible URLs** (Instagram API requirement - files are not downloaded locally)
- Instagram has strict content policies
- Rate limits apply based on your app usage
- Carousel posts support up to 10 media files
- Requires Instagram Business or Creator account

## Troubleshooting

### Common Issues

1. **"Media file must be a publicly accessible URL"**
   - Upload your media to a hosting service like AWS S3, Cloudinary, or GitHub Pages
   - Ensure the URL is publicly accessible without authentication

2. **"Image aspect ratio must be between 0.8 and 1.91"**
   - Resize your image to meet Instagram's requirements
   - Use square (1:1) images for best compatibility

3. **"Invalid access token"**
   - Ensure your token has the correct permissions
   - Check if your token has expired and needs renewal

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

Pipe operators let you transform list values before they are rendered:

### Basic Operations
- `each:prefix(str)`: prefix every element with the provided string (useful for hashtags)
- `join(str)`: collapse the list into a single string separated by the provided delimiter

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
POST_CONTENT=Genres: @{json.genres | each:case_title() | each:prefix('#') | join(' ')}
```

With a `genres` array of `["mythology", "tragedy", "supernatural"]`, the final output becomes:

```
Genres: #Mythology #Tragedy #Supernatural
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

- Built using Instagram Graph API
- Created by Gerald Nguyen
- Licensed under MIT License