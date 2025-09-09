"""Templated content processing utilities for social media actions."""

import os
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from jsonpath_ng import parse as jsonpath_parse
import json


def process_templated_content_if_needed(content: str) -> str:

    def extract_json_path(data, path):
        
        logging.info(f"Extracting JSON path: {path} from data: {data}")
        try:
            expr = jsonpath_parse(f'$.{path}')
            matches = [match.value for match in expr.find(data)]
            logging.info(f"Matches for path '{path}': {matches}")
            if not matches:
                logging.info(f"No matches found for path '{path}'")
                return ''
            if len(matches) == 1:
                val = matches[0]
                logging.info(f"Single match for path '{path}': {val}")
                if isinstance(val, (dict, list)):
                    return val
                return str(val)
            # If multiple matches, join as comma-separated string
            logging.info(f"Multiple matches for path '{path}': {matches}")
            return ', '.join(str(m) for m in matches)
        except Exception as e:
            logging.error(f"Error parsing JSON path '{path}': {e}")
            return ''

    def get_json_data():
        raw = os.getenv('CONTENT_JSON')
        logging.info(f"Raw CONTENT_JSON: {raw}")
        if not raw:
            logging.warning('CONTENT_JSON environment variable not set.')
            return None
        import random
        if '|' in raw:
            url, json_path = [part.strip() for part in raw.split('|', 1)]
            logging.info(f"Parsed CONTENT_JSON url: {url}, json_path: {json_path}")
        else:
            url, json_path = raw.strip(), None
            logging.info(f"Parsed CONTENT_JSON url: {url}, no json_path")
        try:
            logging.info(f"Fetching JSON from URL: {url}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logging.debug(f"Fetched JSON: {data}")
            if json_path:
                # Support [RANDOM] in the path
                if '[RANDOM]' in json_path:
                    path_before, _, path_after = json_path.partition('[RANDOM]')
                    path_before = path_before.rstrip('.')
                    # Remove trailing dot if present
                    arr = extract_json_path(data, path_before)
                    if isinstance(arr, list) and arr:
                        idx = random.randint(0, len(arr) - 1)
                        logging.info(f"[RANDOM] picked index {idx} from array of length {len(arr)}")
                        element = arr[idx]
                        # If there's more path after [RANDOM], extract further
                        if path_after.strip():
                            # Remove leading dot or brackets
                            sub_path = path_after.lstrip('.').lstrip('[]')
                            sub = extract_json_path(element, sub_path)
                            logging.info(f"Sub-JSON after path '{json_path}': {sub}")
                            return sub
                        logging.info(f"Sub-JSON after path '{json_path}': {element}")
                        return element
                    else:
                        logging.warning(f"[RANDOM] used but path '{path_before}' did not resolve to a non-empty array.")
                        return None
                else:
                    sub = extract_json_path(data, json_path)
                    logging.info(f"Sub-JSON after path '{json_path}': {sub}")
                    return sub
            return data
        except Exception as e:
            logging.error(f"Failed to fetch or parse JSON from {url}: {e}")
            return None

    
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
        logging.info(f"Processing placeholder: source={source}, key={key}")
        if source == 'env':
            val = os.getenv(key, '')
            logging.info(f"Resolved env.{key} to '{val}'")
            return val
        elif source == 'builtin':
            val = builtin_value(key)
            logging.info(f"Resolved builtin.{key} to '{val}'")
            return val
        elif source == 'json':
            data = get_json_data()
            logging.info(f"Using JSON root for lookup: {data}")
            if data is None:
                logging.warning(f"No JSON data available for {source}.{key}")
                return match.group(0)
            val = extract_json_path(data, key)
            if val == '':
                logging.warning(f"Could not resolve {source}.{key}, leaving placeholder as-is.")
                return match.group(0)
            logging.info(f"Resolved {source}.{key} to '{str(val)}'")
            return str(val)
        logging.warning(f"Unknown placeholder source: {source}")
        return match.group(0)

    # Updated pattern to support env, builtin, json sources with flexible keys/paths
    pattern = re.compile(r'\@\{(env|builtin|json)\.([a-zA-Z0-9_\[\]\.]+)\}')
    # Always call get_json_data() first to set _json_root if needed
    result = pattern.sub(replace_placeholder, content)
    logging.info(f"Processed templated content: from {content} --> '{result}'")
    return result
