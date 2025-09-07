# Post to Instagram Action

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

This GitHub Action allows you to post content to Instagram using the Instagram Graph API.

## Features

- Post images and videos to Instagram
- Add captions to posts
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

```yaml
- name: Post to Instagram
  uses: ./post-to-instagram
  with:
    access-token: ${{ secrets.IG_ACCESS_TOKEN }}
    user-id: ${{ secrets.IG_USER_ID }}
    content: "Hello from GitHub Actions! 🚀 #automation #github"
    media-file: "https://example.com/hosted-image.jpg"  # Must be publicly accessible URL
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `access-token` | Instagram User Access Token | Yes | - |
| `user-id` | Instagram User ID | Yes | - |
| `content` | Caption for the Instagram post (max 2200 characters) | Yes | - |
| `media-file` | Publicly accessible URL to image or video file | Yes | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

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
      uses: ./post-to-instagram
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

## Getting Instagram Access Token

1. Follow the [Instagram Basic Display API documentation](https://developers.facebook.com/docs/instagram-basic-display-api/getting-started)
2. Use the [Instagram Graph API Explorer](https://developers.facebook.com/tools/explorer/)
3. Generate a long-lived access token for production use

## Limitations

- Media files must be publicly accessible URLs (not local files)
- Instagram has strict content policies
- Rate limits apply based on your app usage
- Only supports single media posts (no carousels)
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

## Credits

- Built using Instagram Graph API
- Created by Gerald Nguyen
- Licensed under MIT License