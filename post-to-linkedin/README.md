# Post to LinkedIn Action

This GitHub Action allows you to post content to LinkedIn using the LinkedIn API v2.

## Features

- Post text content to LinkedIn
- Attach media files (images)
- Attach links with automatic preview
- Configurable logging levels
- Dry-run mode for testing
- Full templating support for dynamic content
- Returns post ID and URL for further processing

## Template Interpolation

You can use template placeholders in your post content. The following sources are supported:

- `@{env.VAR}`: Replaced with the value of the environment variable `VAR` (e.g., `@{env.NAME}`)
- `@{builtin.CURR_DATE}`: Replaced with the current date in `YYYY-MM-DD` format
- `@{builtin.CURR_TIME}`: Replaced with the current time in `HH:MM:SS` format
- `@{builtin.CURR_DATETIME}`: Replaced with the current date and time in `YYYY-MM-DD HH:MM:SS` format

Example:

```env
POST_CONTENT='Hello @{env.NAME}, today is @{builtin.CURR_DATE} at @{builtin.CURR_TIME}!'
NAME=Gerald
```
This will post: `Hello Gerald, today is 2025-09-07 at 14:18:25!`

## Prerequisites

You need to have a LinkedIn Developer account and create an app to get the required API credentials:

1. Go to the [LinkedIn Developers Portal](https://www.linkedin.com/developers/)
2. Create a new app or use an existing one
3. Request access to the required products:
   - **Share on LinkedIn** (for posting capabilities)
   - **Sign In with LinkedIn** (for authentication)
4. Configure OAuth 2.0 settings and redirect URLs
5. Get your access token (you'll need to implement OAuth 2.0 flow)
6. Get your author ID:
   - For personal posts: `urn:li:person:{PERSON_ID}`
   - For organization posts: `urn:li:organization:{ORGANIZATION_ID}`

### Getting an Access Token

LinkedIn uses OAuth 2.0 for authentication. You'll need to:

1. Create an authorization URL with your client ID
2. User grants permission
3. Exchange the authorization code for an access token
4. Use the access token to post content

Refer to [LinkedIn's OAuth 2.0 documentation](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication) for detailed instructions.

### Getting Your Author ID

To get your person ID:
```bash
curl -X GET https://api.linkedin.com/v2/userinfo \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

The response will include your ID which you can format as `urn:li:person:{ID}`.

## Usage

### For External Users

If you're using this action from another repository, reference it with the full repository path and version:

```yaml
- name: Post to LinkedIn
  uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "Excited to share our latest project! 🚀"
    media-files: "path/to/image.jpg"  # Optional
    link: "https://example.com/blog-post"  # Optional
    log-level: "INFO"  # Optional
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post to LinkedIn
  uses: ./post-to-linkedin
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "Excited to share our latest project! 🚀"
    media-files: "path/to/image.jpg"  # Optional
    link: "https://example.com/blog-post"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `access-token` | LinkedIn Access Token | Yes | - |
| `author-id` | LinkedIn Author ID (person or organization URN) | Yes | - |
| `content` | Content to post to LinkedIn (max 3000 characters) | Yes | - |
| `media-files` | Comma-separated list of media file paths | No | - |
| `link` | Link to attach to the post | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `content-json` | JSON API URL and path for dynamic content templating | No | - |
| `time-zone` | Time zone for date/time placeholders (e.g. UTC, UTC+7) | No | - |
| `dry-run` | Dry run mode. If true, content is printed but not posted | No | false |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Example with Media

```yaml
- name: Post to LinkedIn with media
  uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "Check out this amazing screenshot! 📸"
    media-files: "screenshots/demo.png"
```

## Example with Link

```yaml
- name: Post to LinkedIn with link
  uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "Just published a new blog post about GitHub Actions! 📝"
    link: "https://example.com/blog/github-actions-guide"
```

## Templated Content: JSON Source

This action supports API-driven templated content using the `@{json...}` syntax. Example:

```yaml
- name: Post to LinkedIn with dynamic content
  uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "New story: @{json.title} - @{json.description}"
    content-json: "https://example.com/api/stories/latest.json"
    link: "@{json.permalink}"
```

- The action will fetch the JSON from the URL in `content-json`.
- It will extract values using the JSON path in the template.
- Both dot notation and array bracket notation are supported.
- Powered by the `jsonpath-ng` library.

## Templated Content: Post Retrieval Extraction

You can extract a sub-object from a remote JSON by specifying a path after a pipe (|) in the `content-json` variable. Example:

```
content-json: https://example.com/data.json | stories[0]
content: "API-driven: @{json.description}, @{json.permalink}"
```
This will use the first element of the `stories` array as the root for all `@{json...}` lookups.

## Templated Content: [RANDOM] Array Element Picker

You can use `[RANDOM]` in the path to pick a random element from an array:

```
content-json: https://example.com/data.json | stories[RANDOM]
content: "Random story: @{json.description}, @{json.permalink}"
```
This will randomly select an element from the `stories` array for use in template lookups.

## Templated Content: List Operations

You can post-process array values inside a template expression using pipe operations. Available operations include:

### Basic Operations
- `each:prefix(str)`: add the supplied prefix to every element in the list
- `join(str)`: concatenate all elements into a single string separated by the provided string

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

### Length Operations
- `max_length(int, str)`: clip text at word boundary if it exceeds the specified length and append suffix
- `each:max_length(int, str)`: apply max_length to each element in a list
- `join_while(str, int)`: join elements with separator but stop when total length would exceed limit

Example:

```
content-json: https://example.com/data.json | stories[RANDOM]
content: "Topics: @{json.topics | each:case_upper() | each:prefix('#') | join(' ')}"
```

If the selected story contains `"topics": ["ai", "technology", "innovation"]`, the rendered output becomes:

```
Topics: #AI #TECHNOLOGY #INNOVATION
```

### Length Operations Example

```
content-json: https://example.com/data.json | stories[RANDOM] 
content: "Summary: @{json.description | max_length(200, '...')} Tags: @{json.tags | join_while(' #', 100)}"
```

This will clip the description at 200 characters (at word boundary) and join tags with '#' separator until the total length reaches 100 characters.

### Selection Operations Example

```
content-json: https://example.com/data.json | stories
content: "Random story: @{json | random() | attr(title)}"
```

This will randomly select a story object from the `stories` array and extract its `title` attribute.

## Dry-Run Mode

Set the `dry-run` input to `true` to test your post without actually publishing it:

```yaml
- name: Test LinkedIn post
  uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
  with:
    access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
    author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
    content: "This is a test post"
    dry-run: "true"
```

In dry-run mode, the action will:
- Process all templates
- Validate the content
- Log detailed information about the post
- NOT actually publish to LinkedIn

## Security Notes

- Store all API credentials as GitHub repository secrets
- Never commit API tokens to your repository
- Use the principle of least privilege for your LinkedIn app permissions
- Regularly rotate access tokens
- LinkedIn access tokens typically expire after 60 days

## GitHub Actions Best Practices

### Version Pinning
- **Always use a specific version tag** (e.g., `@v1.9.0`) in production workflows for stability
- **Test updates** in a non-production environment before upgrading
- **Check the changelog** for breaking changes when updating versions

### Action Reference Format
- **External repositories**: `geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0`
- **Local/same repository**: `./post-to-linkedin` (requires checkout step first)

### Workflow Tips
- **Use dry-run mode** to test posts before going live
- **Set appropriate log levels** (`DEBUG` for troubleshooting, `INFO` for production)
- **Implement error handling** with `continue-on-error` or conditional steps
- **Use template variables** for dynamic, reusable content
- **Store secrets securely** and never expose them in logs

### Example: Production-Ready Workflow

```yaml
name: Share Blog Post on LinkedIn
on:
  workflow_dispatch:
    inputs:
      post_url:
        description: 'Blog post URL'
        required: true

jobs:
  post-to-linkedin:
    runs-on: ubuntu-latest
    steps:
      - name: Post to LinkedIn
        uses: geraldnguyen/social-media-posters/post-to-linkedin@v1.9.0
        with:
          access-token: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
          author-id: ${{ secrets.LINKEDIN_AUTHOR_ID }}
          content: "📝 Just published a new blog post! Check it out and let me know your thoughts."
          link: ${{ github.event.inputs.post_url }}
          log-level: "INFO"
        continue-on-error: false
        
      - name: Notify on success
        if: success()
        run: echo "Successfully posted to LinkedIn!"
        
      - name: Notify on failure
        if: failure()
        run: echo "Failed to post to LinkedIn. Check the logs for details."
```

## Limitations

- Content is limited to 3000 characters (LinkedIn's character limit for posts)
- Media files must be accessible from the GitHub Actions runner
- Only image files (.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif) are supported for media uploads (expanded in v1.23.0)
- Video uploads are not currently supported
- Rate limits apply based on your LinkedIn API access level
- Access tokens expire and need to be refreshed

## Troubleshooting

### "Invalid access token" error
- Verify your access token is correct and not expired
- Ensure your app has the "Share on LinkedIn" product enabled
- Re-authenticate and get a fresh access token

### "Invalid author URN" error
- Verify your author ID format is correct: `urn:li:person:{ID}` or `urn:li:organization:{ID}`
- Ensure the access token has permission to post on behalf of the author

### Media upload failures
- Verify the image file exists and is accessible
- Check that the file is a supported format (.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif)
- Ensure the file size is reasonable (LinkedIn has size limits)

## LinkedIn API Documentation

- [LinkedIn Share API](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/share-api)
- [LinkedIn Authentication](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- [LinkedIn UGC Posts](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api)

## Credits

- Built using LinkedIn API v2
- Created by Gerald Nguyen
- Licensed under MIT License
