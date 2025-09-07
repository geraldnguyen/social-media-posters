# 00 - Initialization

## GitHub Agent

Create multiple GitHub Actions that other can use:
- Post to X
- Post to Facebook Page
- Post to Instagram
- Post to Threads

Each action should be contain in its own folder, with all required files to meet GitHub Actions requirement PLUS an README.MD file documenting all necessary information (e.g. description, required parameters, credits)

Each action is backed by a python script performing appropriate posting tasks. A link to sample implementation of each posting tasks are available below
- Post to X: https://github.com/geraldnguyen/tellstory.net/blob/main/scripts/post_to_x.py
- Post to Facebook Page: https://github.com/geraldnguyen/tellstory.net/blob/main/scripts/post_to_fb_page.py
- Post to Instagram: https://github.com/geraldnguyen/tellstory.net/blob/main/scripts/post_to_instagram.py
- Post to Threads: https://github.com/geraldnguyen/tellstory.net/blob/main/scripts/post_to_threads.py

You are free to clean up the codes, standardize the behaviors, and extract common functionality to a shared module if necessary.

Create or update a CHANGELOG.MD file with a summary of the changes

## Adjustments - add instructions for resolving common module import errors with PYTHONPATH and VS Code settings 

## Adjustments - Run the scripts locally

Add support for running the script locally by loading the secret from a local .env file if present

## Adjustments - Support remote media

If the media file path is from the internet (http or https) and size less than 5MB (configurable as an parameter) download the file, then use the downloaded file's path to upload.

## Adjustments - Dry-run mode

Add a dry-run mode via environment variable DRY_RUN. If true, just print out the info about the content, media files, the request body, but do not actually post.

Apply the same changes to all post-to-... script. Use a common function or module if possible.


## Adjustments - Templated content

Implement the function process_templated_content_if_needed

```
  def process_templated_content_if_needed(content: str) -> str:
    """Process templated content if context is provided."""
    
    # Copilot: Implement templating logic if needed
    # Each templated placeholder is in the format ${source.KEY}
    # where source can be 'env' for environment variables or 'builtin' for built-in values
    # env.KEY should be replaced with the value of the environment variable KEY
    # Supported built-in values: CURR_DATE, CURR_TIME, CURR_DATETIME
    # TIMEZONE can be set via env var TIME_ZONE, default to UTC

    return content
```

## Adjustments - API-driven templated content

Support the "json" template source:

Given the following values in environment:

POST_CONTENT=API-driven: @{json.stories[0].description}, @{api.stories[0].permalink}
CONTENT_JSON=https://tellstory.net/stories/random/index.json

Expect:
- Retrieve the json at the URL given in CONTENT_JSON variable
- Travel the json path, supporting both dot notation and array bracket notation to retrieve the value

Create unit tests for the changes