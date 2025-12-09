# Post to Instagram Action

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

- Post single images and videos to Instagram
- Create carousel posts with multiple images/videos (up to 10 media files)
- Add captions to posts
- Template interpolation support
- Configurable logging levels
- Returns post ID and URL for further processing

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

### Single Media Post

```yaml
- name: Post single image to Instagram
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "Check out this amazing photo! 📸"
    media-file: "https://example.com/hosted-image.jpg"  # Must be publicly accessible URL
```

### Carousel Post (Multiple Images)

For local development within the social-media-posters repository, use relative paths and include a checkout step:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post carousel to Instagram
  uses: ./post-to-instagram
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "My photo series! 📸"
    media-files: "https://example.com/image1.jpg,https://example.com/image2.jpg,https://example.com/image3.jpg"
```
### Carousel Post Example

```yaml
- name: Post carousel to Instagram
  uses: geraldnguyen/social-media-posters/post-to-instagram@v1.9.0
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "My photo series! 📸 #carousel #photos"
    media-files: "https://example.com/image1.jpg,https://example.com/image2.jpg,https://example.com/image3.jpg"
    log-level: "INFO"  # Optional
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