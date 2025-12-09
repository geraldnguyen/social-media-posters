# Remote Media Support

All posting scripts in this repository support using remote media files (images, videos, etc.) by specifying an HTTP or HTTPS URL as the media file path. If the remote file is less than a configurable size limit (default: 5MB), the script will automatically download the file and use the downloaded local path for uploading to the social media platform.

- The maximum allowed download size can be set using the `MAX_DOWNLOAD_SIZE_MB` environment variable. If not set, the default is 5MB.
- This feature works for all scripts that accept media file paths (e.g., Post to X, Facebook, Instagram, Threads).
- If the file is too large or cannot be downloaded, the script will log an error and exit.

This makes it easy to use media hosted on the internet in your automated social media posts.
# Resolving Import Errors for Common Utilities

If you encounter import errors such as `Import "social_media_utils" could not be resolved` when running or editing the post-to-* scripts, follow these steps to ensure Python and your editor can find the `common` utilities:

## 1. Add `common` to PYTHONPATH

- Create a `.env` file in your project root (if it doesn't exist).
- Add the following line:
  - On Windows:
    ```
    PYTHONPATH=${PYTHONPATH};${workspaceFolder}/common
    ```
  - On macOS/Linux:
    ```
    PYTHONPATH=${PYTHONPATH}:${workspaceFolder}/common
    ```

This allows both your scripts and VS Code to resolve imports like `from social_media_utils import ...`.

## 2. (Optional) VS Code Settings

You can also add the following to `.vscode/settings.json` to help Pylance find the `common` directory:

```json
{
  "python.analysis.extraPaths": [
    "./common"
  ]
}
```

## 3. Keep the sys.path Modification in Scripts

Each script already includes:

```python
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))
```

This ensures the script works when run directly.

---
By following these steps, you can avoid import errors and keep your code modular and reusable across all post-to-* actions.
# Social Media Posters

A collection of GitHub Actions for posting content to various social media platforms. These actions provide a simple and automated way to share content across multiple social networks from your GitHub workflows.

## Available Actions

### 🐦 [Post to X (Twitter)](./post-to-x)
Post content to X (formerly Twitter) using the X API v2.
- Supports text posts with media attachments
- Character limit: 280 characters
- Media support: Images and videos

### 📘 [Post to Facebook Page](./post-to-facebook)
Post content to Facebook Pages using the Facebook Graph API.
- Supports text posts with media and links
- No strict character limit
- Media support: Images and videos

### 📸 [Post to Instagram](./post-to-instagram)
Post content to Instagram using the Instagram Graph API.
- Requires publicly accessible media URLs
- Caption limit: 2200 characters
- Media support: Images and videos with strict requirements

### 🧵 [Post to Threads](./post-to-threads)
Post content to Threads using the Threads API.
- Character limit: 500 characters
- Supports media and link attachments
- Media support: Images and videos via URLs

### 💼 [Post to LinkedIn](./post-to-linkedin)
Post content to LinkedIn using the LinkedIn API v2.
- Character limit: 3000 characters
- Supports text posts with media and links
- Media support: Images (videos not currently supported)

## Quick Start

1. Choose the social media platform(s) you want to post to
2. Set up the required API credentials (see individual action READMEs)
3. Store credentials as GitHub repository secrets
4. Use the actions in your workflows

## Example Workflow

### For External Users

If you're using these actions from another repository, reference them with the full repository path and version:

```yaml
name: Social Media Post
on:
  push:
    branches: [ main ]

jobs:
  post-to-social-media:
    runs-on: ubuntu-latest
    steps:
      - name: Post to X
        uses: geraldnguyen/social-media-posters/post-to-x@v1.9.0
        with:
          api-key: ${{ secrets.X_API_KEY }}
          api-secret: ${{ secrets.X_API_SECRET }}
          access-token: ${{ secrets.X_ACCESS_TOKEN }}
          access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
          content: "🚀 New release deployed! Check out the latest features."
      
      - name: Post to Facebook Page
        uses: geraldnguyen/social-media-posters/post-to-facebook@v1.9.0
        with:
          access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
          page-id: ${{ secrets.FB_PAGE_ID }}
          content: "We've just released a new version with exciting features!"
          link: ${{ github.event.head_commit.url }}
```

### For Local Development

If you're developing or testing within this repository, use relative paths:

```yaml
name: Social Media Post
on:
  push:
    branches: [ main ]

jobs:
  post-to-social-media:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Post to X
        uses: ./post-to-x
        with:
          api-key: ${{ secrets.X_API_KEY }}
          api-secret: ${{ secrets.X_API_SECRET }}
          access-token: ${{ secrets.X_ACCESS_TOKEN }}
          access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
          content: "🚀 New release deployed! Check out the latest features."
      
      - name: Post to Facebook Page
        uses: ./post-to-facebook
        with:
          access-token: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
          page-id: ${{ secrets.FB_PAGE_ID }}
          content: "We've just released a new version with exciting features!"
          link: ${{ github.event.head_commit.url }}
```

## Repository Structure

```
social-media-posters/
├── post-to-x/              # X (Twitter) posting action
│   ├── action.yml
│   ├── post_to_x.py
│   ├── requirements.txt
│   └── README.md
├── post-to-facebook/       # Facebook Page posting action
│   ├── action.yml
│   ├── post_to_facebook.py
│   ├── requirements.txt
│   └── README.md
├── post-to-instagram/      # Instagram posting action
│   ├── action.yml
│   ├── post_to_instagram.py
│   ├── requirements.txt
│   └── README.md
├── post-to-threads/        # Threads posting action
│   ├── action.yml
│   ├── post_to_threads.py
│   ├── requirements.txt
│   └── README.md
├── post-to-linkedin/       # LinkedIn posting action
│   ├── action.yml
│   ├── post_to_linkedin.py
│   ├── requirements.txt
│   ├── test_post_to_linkedin.py
│   └── README.md
├── common/                 # Shared utilities
│   ├── __init__.py
│   └── social_media_utils.py
├── CHANGELOG.md
└── README.md
```

## Common Features

All actions share these common features:

- **Error Handling**: Comprehensive error handling with informative messages
- **Logging**: Configurable logging levels (DEBUG, INFO, WARNING, ERROR)
- **Validation**: Input validation for content and media files
- **Outputs**: Returns post ID and URL for further processing
- **Security**: Secure handling of API credentials via GitHub secrets

### Templated Content Helpers

All actions include a flexible templating engine that can pull values from environment variables, built-in timestamps, or remote JSON payloads referenced by `CONTENT_JSON`. In addition to basic lookups, you can apply pipe operations to transform list results:

#### Basic Operations
- `each:prefix(str)` adds the specified prefix to each element (great for turning categories into hashtags).
- `join(str)` concatenates all list items into a single string using the provided separator.

#### Case Transformation Operations  
- `each:case_title()` converts each element to Title Case
- `each:case_sentence()` converts each element to Sentence case
- `each:case_upper()` converts each element to UPPERCASE
- `each:case_lower()` converts each element to lowercase
- `each:case_pascal()` converts each element to PascalCase
- `each:case_kebab()` converts each element to kebab-case
- `each:case_snake()` converts each element to snake_case

#### Length Operations
- `max_length(int, suffix?)` limits string length with optional suffix (e.g., "...")
- `each:max_length(int, suffix?)` applies max_length to each item in a list
- `join_while(separator, max_length)` joins items until maximum length is reached

Example:

```
CONTENT_JSON=https://example.com/data.json | stories[RANDOM]
POST_CONTENT=Summary: @{json.description | max_length(150, '...')} Tags: @{json.genres | each:case_upper() | each:prefix('#') | join_while(' ', 100)}
```

If the selected story exposes a `genres` list of `mythology`, `tragedy`, and `supernatural`, the rendered content is:

```
Summary: This is a captivating tale of ancient gods and mortals, exploring themes of destiny, sacrifice, and the supernatural forces that govern our world... Tags: #MYTHOLOGY #TRAGEDY #SUPERNATURAL
```

## Security Best Practices

1. **Never commit API credentials** to your repository
2. **Use GitHub secrets** to store all sensitive information
3. **Follow the principle of least privilege** for API permissions
4. **Regularly rotate access tokens** and API keys
5. **Monitor API usage** to detect unusual activity

## GitHub Actions Best Practices

When using these actions in your workflows:

### Version Pinning
- **Use specific version tags** (e.g., `@v1.9.0`) instead of branches for stability
- **Review changelogs** before upgrading to new versions
- **Test in non-production** environments before updating production workflows

### Action References
- **External repositories**: Use `geraldnguyen/social-media-posters/<action-folder>@<version>`
- **Within this repository**: Use relative paths like `./post-to-x` (requires checkout step)

### Security
- **Store credentials as repository secrets**, never hardcode them
- **Use environment-specific secrets** for different deployment stages
- **Limit secret access** to only the workflows and jobs that need them
- **Regularly audit** your secrets and rotate credentials

### Workflow Optimization
- **Use conditionals** to control when posts are made
- **Implement dry-run mode** for testing before actual posting
- **Add error handling** and notifications for failures
- **Cache dependencies** when possible to speed up workflow execution

### Example: Production Workflow with Best Practices

```yaml
name: Production Social Media Post
on:
  release:
    types: [published]

jobs:
  post-to-social-media:
    runs-on: ubuntu-latest
    steps:
      - name: Post to X
        uses: geraldnguyen/social-media-posters/post-to-x@v1.9.0
        with:
          api-key: ${{ secrets.X_API_KEY }}
          api-secret: ${{ secrets.X_API_SECRET }}
          access-token: ${{ secrets.X_ACCESS_TOKEN }}
          access-token-secret: ${{ secrets.X_ACCESS_TOKEN_SECRET }}
          content: "🚀 New release ${{ github.event.release.tag_name }} is now available!"
          log-level: "INFO"
        continue-on-error: true
      
      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Social media posting failed',
              body: 'The social media post workflow failed. Please check the logs.'
            })
```

## Prerequisites by Platform

| Platform | Requirements |
|----------|-------------|
| X (Twitter) | X Developer Account, App with API v2 access |
| Facebook | Facebook App, Page Admin access, Graph API permissions |
| Instagram | Business/Creator account, Facebook App, Graph API access |
| Threads | Threads account, approved Threads App |
| LinkedIn | LinkedIn Developer Account, App with Share on LinkedIn product |

## Rate Limits

Each platform has different rate limits:

- **X**: Varies by API endpoint and access level
- **Facebook**: Varies by app usage and user activity
- **Instagram**: Limited by Graph API quotas
- **Threads**: Subject to Meta's API rate limits
- **LinkedIn**: Subject to LinkedIn API throttling limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Created by Gerald Nguyen
- Built with Python and various social media SDKs
- Inspired by the need for automated social media posting in CI/CD workflows

## Support

For issues, questions, or feature requests:

1. Check the individual action READMEs for platform-specific issues
2. Review the [CHANGELOG](CHANGELOG.md) for recent updates
3. Open an issue in this repository

## Disclaimer

These actions are provided as-is. Users are responsible for:
- Complying with each platform's terms of service
- Managing their API credentials securely
- Respecting rate limits and usage policies
- Ensuring content meets platform guidelines