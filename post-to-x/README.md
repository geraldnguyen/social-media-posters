# Post to X (Twitter) Action

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

This GitHub Action allows you to post content to X (formerly Twitter) using the X API v2.

## Features

- Post text content to X
- Attach media files (images, videos)
- Configurable logging levels
- Returns post ID and URL for further processing

## Prerequisites

You need to have an X Developer Account and create an app to get the required API credentials:

1. Go to the [X Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Get your API keys and tokens:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)
   - Access Token
   - Access Token Secret

## Usage

### For External Users

If you're using this action from another repository, reference it with the full repository path and version:

```yaml
- name: Post to X
  uses: geraldnguyen/social-media-posters/post-to-x@v1.9.0
  with:
    api-key: ${{ secrets.X_API_KEY }}
    api-secret: ${{ secrets.X_API_SECRET }}
    access-token: ${{ secrets.X_ACCESS_TOKEN }}
    access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/video.mp4"  # Optional
    log-level: "INFO"  # Optional
```

### For Local Development

If you're developing within the social-media-posters repository:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3

- name: Post to X
  uses: ./post-to-x
  with:
    api-key: ${{ secrets.X_API_KEY }}
    api-secret: ${{ secrets.X_API_SECRET }}
    access-token: ${{ secrets.X_ACCESS_TOKEN }}
    access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
    content: "Hello from GitHub Actions! 🚀"
    media-files: "path/to/image.jpg,path/to/video.mp4"  # Optional
    log-level: "INFO"  # Optional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `api-key` | X API Key (Consumer Key) | Yes | - |
| `api-secret` | X API Secret (Consumer Secret) | Yes | - |
| `access-token` | X Access Token | Yes | - |
| `access-token-secret` | X Access Token Secret | Yes | - |
| `content` | Content to post to X (max 280 characters) | Yes | - |
| `media-files` | Comma-separated list of media file paths | No | - |
| `log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |

## Outputs

| Output | Description |
|--------|-------------|
| `post-id` | ID of the created post |
| `post-url` | URL of the created post |

## Example with Media

```yaml
- name: Post to X with media
  uses: geraldnguyen/social-media-posters/post-to-x@v1.9.0
  with:
    api-key: ${{ secrets.X_API_KEY }}
    api-secret: ${{ secrets.X_API_SECRET }}
    access-token: ${{ secrets.X_ACCESS_TOKEN }}
    access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
    content: "Check out this amazing screenshot! 📸"
    media-files: "screenshots/demo.png"
```

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
CONTENT_JSON=https://example.com/data.json | stories[RANDOM]
POST_CONTENT=Genres: @{json.genres | each:case_upper() | each:prefix('#') | join(' ')}
```

If the selected story contains `"genres": ["mythology", "tragedy", "supernatural"]`, the rendered output becomes:

```
Genres: #MYTHOLOGY #TRAGEDY #SUPERNATURAL
```

### Length Operations Example

```
CONTENT_JSON=https://example.com/data.json | stories[RANDOM] 
POST_CONTENT=Summary: @{json.description | max_length(100, '...')} Tags: @{json.tags | join_while(' #', 50)}
```

This will clip the description at 100 characters (at word boundary) and join tags with '#' separator until the total length reaches 50 characters.

### Selection Operations Example

```
CONTENT_JSON=https://example.com/data.json | stories
POST_CONTENT=Random story: @{json | random() | attr(title)}
```

This will randomly select a story object from the `stories` array and extract its `title` attribute.

## JSON Configuration File

Starting from v1.11.0, you can provide all parameters via a JSON configuration file instead of environment variables. This is particularly useful for:
- Local development and testing
- Managing multiple configurations
- Organizing complex parameter sets

### Usage

1. **Create a JSON config file** (default: `input.json` in your working directory):

```json
{
  "X_API_KEY": "your_api_key_here",
  "X_API_SECRET": "your_api_secret_here",
  "X_ACCESS_TOKEN": "your_access_token_here",
  "X_ACCESS_TOKEN_SECRET": "your_access_token_secret_here",
  "POST_CONTENT": "Your tweet content here",
  "MEDIA_FILES": "",
  "LOG_LEVEL": "INFO",
  "DRY_RUN": "false"
}
```

2. **Run the script**:

```bash
# Uses input.json by default
python post_to_x.py

# Or specify a custom config file
INPUT_FILE=my_config.json python post_to_x.py
```

3. **Or set INPUT_FILE in your `.env` file**:

```
INPUT_FILE=my_custom_config.json
```

### Configuration Priority

Parameters are loaded in the following order (highest to lowest priority):
1. Environment variables
2. JSON configuration file
3. `.env` file
4. Default values

This means environment variables will always override values from the JSON config file.

### Example: Mixed Configuration

You can combine JSON config with environment variables. For example, store non-sensitive parameters in JSON and sensitive credentials in environment variables:

```json
// config.json
{
  "POST_CONTENT": "Test post with mixed config",
  "LOG_LEVEL": "DEBUG",
  "DRY_RUN": "true"
}
```

```bash
# Provide credentials via environment
X_API_KEY="secret_key" \
X_API_SECRET="secret_secret" \
X_ACCESS_TOKEN="secret_token" \
X_ACCESS_TOKEN_SECRET="secret_token_secret" \
INPUT_FILE=config.json \
python post_to_x.py
```

### Example Template

A template JSON config file (`input.json.example`) is provided in the action folder. Copy and customize it for your needs:

```bash
cp input.json.example input.json
# Edit input.json with your values
```

**Important**: The `input.json` file is ignored by git to prevent accidentally committing sensitive credentials.

## Security Notes

- Store all API credentials as GitHub repository secrets
- Never commit API keys or tokens to your repository
- Use the principle of least privilege for your X app permissions
- The `input.json` file is automatically ignored by git to prevent credential leaks

## GitHub Actions Best Practices

### Version Pinning
- **Always use a specific version tag** (e.g., `@v1.11.0`) in production workflows for stability
- **Test updates** in a non-production environment before upgrading
- **Check the changelog** for breaking changes when updating versions

### Action Reference Format
- **External repositories**: `geraldnguyen/social-media-posters/post-to-x@v1.11.0`
- **Local/same repository**: `./post-to-x` (requires checkout step first)

### Workflow Tips
- **Respect the 280-character limit** for X posts
- **Use appropriate log levels** (`DEBUG` for troubleshooting, `INFO` for production)
- **Implement error handling** with `continue-on-error` or conditional steps
- **Use template variables** for dynamic, reusable content
- **Store secrets securely** and never expose them in logs
- **Be mindful of rate limits** based on your API access level

### Example: Production-Ready Workflow

```yaml
name: Tweet on Release
on:
  release:
    types: [published]

jobs:
  post-to-x:
    runs-on: ubuntu-latest
    steps:
      - name: Post release announcement to X
        uses: geraldnguyen/social-media-posters/post-to-x@v1.11.0
        with:
          api-key: ${{ secrets.X_API_KEY }}
          api-secret: ${{ secrets.X_API_SECRET }}
          access-token: ${{ secrets.X_ACCESS_TOKEN }}
          access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
          content: "🚀 Version ${{ github.event.release.tag_name }} is now live! Check out the release notes: ${{ github.event.release.html_url }}"
          log-level: "INFO"
        continue-on-error: true
```

## Limitations

- Content is limited to 280 characters (X's character limit)
- Media files must be accessible from the GitHub Actions runner
- Rate limits apply based on your X API access level

## Credits

- Built using [Tweepy](https://github.com/tweepy/tweepy) library
- Created by Gerald Nguyen
- Licensed under MIT License