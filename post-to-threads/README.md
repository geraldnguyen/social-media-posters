# Post to Threads Action

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

This GitHub Action allows you to post content to Threads using the Threads API.

## Features

- Post text content to Threads
- Attach media files (images, videos) via URLs
- Include links in posts
- Configurable logging levels
- Returns post ID and URL for further processing

## Prerequisites

You need to have a Threads account and create a Threads App:

1. Have an active Threads account
2. Go to the [Meta for Developers](https://developers.facebook.com/) portal
3. Create a new app or use an existing one
4. Add the "Threads API" product to your app
5. Generate an access token with the following permissions:
   - `threads_basic`
   - `threads_content_publish`
6. Get your Threads User ID

## Usage

```yaml
- name: Post to Threads
  uses: ./post-to-threads
  with:
    access-token: ${{ secrets.THREADS_ACCESS_TOKEN }}
    user-id: ${{ secrets.THREADS_USER_ID }}
    content: "Hello from GitHub Actions! 🚀 #automation"
    media-file: "https://example.com/hosted-image.jpg"  # Optional
    link: "https://example.com"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `access-token` | Threads User Access Token | Yes | - |
| `user-id` | Threads User ID | Yes | - |
| `content` | Content to post to Threads (max 500 characters) | Yes | - |
| `media-file` | Publicly accessible URL to image or video file | No | - |
| `link` | Link to attach to the post | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Example with Media and Link

```yaml
- name: Post to Threads with media and link
  uses: ./post-to-threads
  with:
    access-token: ${{ secrets.THREADS_ACCESS_TOKEN }}
    user-id: ${{ secrets.THREADS_USER_ID }}
    content: "Check out our latest update! 🎉"
    media-file: "https://cdn.example.com/announcement.jpg"
    link: "https://blog.example.com/latest-update"
```

## Important Notes

### Media File Requirements

**The media file must be a publicly accessible URL.** Threads API requires that media files be hosted on a public server. You cannot use local file paths.

**Image Requirements:**
- Supported formats: JPEG, PNG, GIF
- Maximum file size: 8MB
- Recommended dimensions: 1080x1080 pixels (square)

**Video Requirements:**
- Supported formats: MP4, MOV
- Maximum file size: 100MB
- Maximum duration: 60 seconds
- Recommended dimensions: 1080x1080 pixels (square)

### Content Requirements

- Maximum length: 500 characters
- Supports Unicode characters and emojis
- Hashtags and mentions are supported

## Security Notes

- Store your access token as a GitHub repository secret
- Store your user ID as a GitHub repository secret
- Never commit access tokens to your repository
- Use long-lived access tokens for production use

## Getting Threads Access Token

1. Follow the [Threads API documentation](https://developers.facebook.com/docs/threads)
2. Create a Threads App in the Meta for Developers portal
3. Generate a user access token with appropriate permissions
4. Get your Threads User ID from the API

## Example Workflow

```yaml
name: Post to Threads
on:
  push:
    branches: [ main ]

jobs:
  post-to-threads:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Post update to Threads
        uses: ./post-to-threads
        with:
          access-token: ${{ secrets.THREADS_ACCESS_TOKEN }}
          user-id: ${{ secrets.THREADS_USER_ID }}
          content: "🚀 New code deployed to production! Check out the latest features."
          link: ${{ github.event.head_commit.url }}
```

## Limitations

- Content is limited to 500 characters
- Media files must be publicly accessible URLs (not local files)
- Rate limits apply based on your app usage
- Only supports single media posts
- Requires an approved Threads App for production use

## Troubleshooting

### Common Issues

1. **"Media file must be a publicly accessible URL"**
   - Upload your media to a hosting service like AWS S3, Cloudinary, or GitHub Pages
   - Ensure the URL is publicly accessible without authentication

2. **"Post content exceeds maximum length of 500 characters"**
   - Shorten your content to meet Threads' character limit
   - Consider using abbreviations or removing unnecessary words

3. **"Invalid access token"**
   - Ensure your token has the correct permissions
   - Check if your token has expired and needs renewal
   - Verify your app has been approved for Threads API access

## Credits

- Built using Threads API
- Created by Gerald Nguyen
- Licensed under MIT License

## Note

The Threads API is relatively new and may have changes or updates. Please refer to the official [Threads API documentation](https://developers.facebook.com/docs/threads) for the most current information.

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

Pipe operators allow you to transform lists before they are rendered:

### Basic Operations
- `each:prefix(str)`: prepend the provided string to every list element
- `join(str)`: merge the list into a single string separated by the provided delimiter

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
POST_CONTENT=Topics: @{json.genres | each:case_pascal() | each:prefix('#') | join(' ')}
```

If the chosen story has `genres` of `["ancient mythology", "greek tragedy", "supernatural events"]`, the rendered content becomes:

```
Topics: #AncientMythology #GreekTragedy #SupernaturalEvents
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