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

```yaml
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
  uses: ./post-to-facebook
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

## Supported Media Types

- **Images**: .jpg, .jpeg, .png, .gif
- **Videos**: .mp4, .mov, .avi

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

## Credits

- Built using [Facebook SDK for Python](https://github.com/mobolic/facebook-sdk) library
- Created by Gerald Nguyen
- Licensed under MIT License