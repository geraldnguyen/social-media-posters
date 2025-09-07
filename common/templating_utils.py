"""Templated content processing utilities for social media actions."""

import os
import logging
import re
import requests
from datetime import datetime, timezone, timedelta

def process_templated_content_if_needed(content: str) -> str:
    import json
    import requests

    # Cache for loaded JSON
    _json_cache = {}

    def get_json_data():
        if 'data' in _json_cache:
            return _json_cache['data']
        url = os.getenv('CONTENT_JSON')
        if not url:
            logging.warning('CONTENT_JSON environment variable not set.')
            _json_cache['data'] = None
            return None
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            _json_cache['data'] = data
            return data
        except Exception as e:
            logging.error(f"Failed to fetch or parse JSON from {url}: {e}")
            _json_cache['data'] = None
            return None

    def extract_json_path(data, path):
        # Use jsonpath-ng for robust JSON path extraction
        try:
            from jsonpath_ng import parse as jsonpath_parse
        except ImportError:
            logging.error("jsonpath-ng is not installed. Please install it with 'pip install jsonpath-ng'. Returning unresolved placeholder.")
            return ''
        # Convert dot/bracket notation to jsonpath-ng format if needed
        # Accept both foo.bar[0].baz and foo.bar[0]['baz']
        try:
            expr = jsonpath_parse(f'$.{path}')
            matches = [match.value for match in expr.find(data)]
            if not matches:
                return ''
            # If only one match, return as string
            if len(matches) == 1:
                return str(matches[0])
            # If multiple matches, join as comma-separated string
            return ', '.join(str(m) for m in matches)
        except Exception as e:
            logging.error(f"Error parsing JSON path '{path}': {e}")
            return ''
    
    """Process templated content if context is provided."""
    def get_timezone():
        tz = os.getenv('TIME_ZONE', 'UTC')
        logging.debug(f"Resolving timezone: {tz}")
        if tz.upper() == 'UTC':
            logging.info("Using UTC timezone.")
            return timezone.utc
        m = re.match(r'UTC([+-]\d+)$', tz.upper())
        if m:
            offset = int(m.group(1))
            logging.info(f"Using timezone offset: UTC{offset:+d}")
            return timezone(timedelta(hours=offset))
        logging.warning(f"Unrecognized TIME_ZONE '{tz}', defaulting to UTC.")
        return timezone.utc

    def builtin_value(key: str) -> str:
        now = datetime.now(get_timezone())
        if key == 'CURR_DATE':
            val = now.strftime('%Y-%m-%d')
        elif key == 'CURR_TIME':
            val = now.strftime('%H:%M:%S')
        elif key == 'CURR_DATETIME':
            val = now.strftime('%Y-%m-%d %H:%M:%S')
        else:
            val = ''
        logging.info(f"Resolved builtin.{key} to '{val}'")
        return val

    def replace_placeholder(match):
        source, key = match.group(1), match.group(2)
        if source == 'env':
            val = os.getenv(key, '')
            logging.info(f"Resolved env.{key} to '{val}'")
            return val
        elif source == 'builtin':
            return builtin_value(key)
        elif source == 'json':
            data = get_json_data()
            if data is None:
                logging.warning(f"No JSON data available for {source}.{key}")
                return match.group(0)
            val = extract_json_path(data, key)
            if val == '':
                logging.warning(f"Could not resolve {source}.{key}, leaving placeholder as-is.")
                return match.group(0)
            logging.info(f"Resolved {source}.{key} to '{val}'")
            return val
        logging.warning(f"Unknown placeholder source: {source}")
        return match.group(0)

    # Updated pattern to support env, builtin, json sources with flexible keys/paths
    pattern = re.compile(r'\@\{(env|builtin|json)\.([a-zA-Z0-9_\[\]\.]+)\}')
    result = pattern.sub(replace_placeholder, content)
    logging.info(f"Processed templated content: from {content} --> '{result}'")
    return result
