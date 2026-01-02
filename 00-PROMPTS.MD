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

Then run the tests


## Adjustments - API-driven templated content - post retrieval extraction

Given the following values in environment:

POST_CONTENT=API-driven: @{json.description}, @{json.permalink}
CONTENT_JSON=https://tellstory.net/stories/random/index.json | stories[0]


Expect:
- Tokenize the CONTENT_JSON variable by space and pipe (|). 
- Retrieve the json at the URL given in CONTENT_JSON variable
- If there are a json path following the URL, process the json path, then return the obtain json for use in the POST_CONTENT's processing.
- Travel the json path from the json obtained in the step above, supporting both dot notation and array bracket notation to retrieve the value

Create unit tests for the changes

Then run the tests

## Adjustments - API-driven templated content - post retrieval extraction - Support `[RANDOM]` array element picker

Update the get_json_data function to support `[RANDOM]` array element picker

Given the following values in environment:

POST_CONTENT=API-driven: @{json.description}, @{json.permalink}
CONTENT_JSON=https://tellstory.net/stories/random/index.json | stories[RANDOM]

Expectation:
- Pick a random number beween 0 and the size of the arrays resolved by the json path with the `[RANDOM]` part.
- Obtain the element at the random index picked in the previous step
- Return the element as the json data

Create unit tests for the changes

Then run the tests

## Adjustment - List operations

Expand the Pipe operator to template expression within POST_CONTENT to support the following list operations
- `each:prefix(str)`: prefix the `str` to each each element in the input array
- `join(str)`: Join all elements in the input array into a single string using the `str` concatenator


Example: Assume the `json` value evaluated to

```
{
      "title": "The Myth of Tereus and Procne",
      "url": "/stories/mythology/the-myth-of-tereus-and-procne/",
      "permalink": "https://tellstory.net/stories/mythology/the-myth-of-tereus-and-procne/",
      "date": "2025-08-05",
      "genres": [
        "Mythology",
        "Tragedy",
        "Supernatural"
      ],
      "origins": [
        "Ancient Greece"
      ],
      "description": "a short description",
      "summary": "A short summary",
      "word_count": 2025,
      "featured": false
    }
```

and the `POST_CONTENT` having value

```
POST_CONTENT=API-driven with random pick: @{json.description}, @{json.permalink} @{json.genres | each:prefix('#') | join(' ')}
```

The template engine shall product the following output

```
API-driven with random pick: a short description, https://tellstory.net/stories/mythology/the-myth-of-tereus-and-procne/ #Mythology #Tragedy #Supernatural
```

Expectation:
- Implement the above requirements
- Create unit tests for the changes
- Then run the tests
- Before handover, update all relevant .MD file documenting the new functionality changes

## Adjustment - List operations - casing operations

Expand the Pipe operator to template expression within POST_CONTENT to support the following list operations
- each:case_title(): example: `hello world` -> `Hello World`
- each:case_sentence(): example: `hello world` -> `Hello world`
- each:case_upper(): example: `hello world` -> `HELLO WORLD`
- each:case_lower(): example: `Hello WORLD` -> `hello world`
- each:case_pascal(): example: `hello world` -> `HelloWorld`
- each:case_kebab(): example: `hello world` -> `hello-world`
- each:case_snake(): example: `hello world` -> `hello_world`

Expectation:
- Implement the above requirements
- Create unit tests for the changes
- Then run the tests
- Before handover, update all relevant .MD file documenting the new functionality changes


## Adjustment - List operations - length operations

Expand the Pipe operator to template expression within POST_CONTENT to support the following list operations
- `max_length(int, str)`: The input string's length must be less than or equal to the 1st positive integer `int` argument, else the string will be clipped at the end of its last word and appended the 2nd argument `str`. The total length of the resulting string may be larger than the 1st argument. 
- `each:max_length(int, str)`: similar to `max_length(int, str)` but apply to element of a list or array
- `join_while(str, int)`: operate similar to `join(str)` but stop and return the resulting string when it encounters any element whose joining would create a string whose length is larger than the 2nd argument `int`

Expectation:
- Implement the above requirements
- Create unit tests for the changes
- Then run the tests
- Before handover, update all relevant .MD file documenting the new functionality changes

## Adjustment - Process multiple template strings using the same json root

Create a `process_templated_contents` function in templating_utils.py:
- Support varargs parameters, each is a templated string to process
- Reuse the existing helpers from `process_templated_content_if_needed` 
- Fetches CONTENT_JSON only once, and use the same obtained `json` to process all templated string arguments

Create new unit tests for `process_templated_contents`

Then modify the `post_to_x.py` to call `process_templated_contents` to process POST_CONTENT

Then modify the `post_to_facebook.py` to call `process_templated_contents` to process POST_CONTENT and POST_LINK

Then safely delete `process_templated_content_if_needed`


## Adjustment - random() and attr(attribute) operations ✅ COMPLETED

Expand the Pipe operator to template expression (e.g. POST_CONTENT, POST_LINK) to support the following operations
- `random()`: a List opreation. Return an random element from the input list. If the list is null or empty, throw error
- `attr(name)`: an json object operation. Return the `name` attribute of the input object. If the object is null, throw error. If the attribute does not exist, throw error.


Expectation:
- Implement the above requirements ✅
- Create unit tests for the changes ✅
- Then run the tests ✅
- Before handover, update all relevant .MD file documenting the new functionality changes ✅

## v1.9.0 - Post-to-Linkedin action

Create a new post-to-linkedin action in the same-named folder.

The post-to-linkedin action shall support all features common to other post-to actions.

Detailed logging and dry-run mode must be available to faciliate troubleshooting.

Expectation:
- Implement the above requirements
- Create unit tests for the changes
- Then run the tests
- Before handover, update all relevant .MD file (in the same action folder, and on the parent folder) documenting the new functionality changes

## v1.10.0 - post-to-youtube action ✅ COMPLETED

Create a new post-to-youtube in the same-named folder

The post-to-youtube action shall support all features common to other post-to actions.

Additionally:
- Support Post and Video. The video can be uploaded locally or from a publically accessible web address ✅
- Support scheduling by date and time ✅
- Support all required and optional metadata fields ✅

Detailed logging and dry-run mode must be available to faciliate troubleshooting. ✅

Expectation:
- Implement the above requirements ✅
- Create unit tests for the changes ✅
- Then run the tests ✅
- Before handover, update all relevant .MD file (in the same action folder, and on the parent folder) documenting the new functionality changes ✅



## v1.11.0 - Support loading parameters from a JSON file

Currently, all post-to-XYZ scripts support loading parameters through environment variables and `.env` file

Expectation, **all** post-to-XYZ scripts must support environment variables, `.env` file and an JSON file (file's path can be either absolute or relative, specified via `INPUT_FILE` environment variable or entry in `.env` file, or `input.json` if not provided)

Detailed logging and dry-run mode must be available to faciliate troubleshooting. ✅

Expectation:
- Implement the above requirements ✅
- Create unit tests for the changes ✅
- Then run the tests ✅
- Before handover, update all relevant .MD file (in the same action folder, and on the parent folder) documenting the new functionality changes ✅
