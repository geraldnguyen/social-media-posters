"""Templated content processing utilities for social media actions."""

import os
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from jsonpath_ng import parse as jsonpath_parse
import json


def process_templated_content_if_needed(content: str) -> str:
    """Process content with support for env, builtin and json templates.

    Supported placeholders:
    - @{env.VAR}
    - @{builtin.CURR_DATE|CURR_TIME|CURR_DATETIME}
    - @{json.path.to.field}
    """

    def extract_json_path(data, path):
        logging.debug("Extracting JSON path: %s from data: %s", path, data)
        try:
            expr = jsonpath_parse(f'$.{path}')
            matches = [match.value for match in expr.find(data)]
            logging.debug("Matches for path '%s': %s", path, matches)
            if not matches:
                logging.debug("No matches found for path '%s'", path)
                return ''
            if len(matches) == 1:
                val = matches[0]
                logging.debug("Single match for path '%s': %s", path, val)
                if isinstance(val, (dict, list)):
                    return val
                return str(val)
            # If multiple matches, join as comma-separated string
            logging.debug("Multiple matches for path '%s': %s", path, matches)
            return ', '.join(str(m) for m in matches)
        except Exception as e:
            logging.error("Error parsing JSON path '%s': %s", path, e)
            return ''

    def get_json_data():
        raw = os.getenv('CONTENT_JSON')
        logging.debug("Raw CONTENT_JSON: %s", raw)
        if not raw:
            logging.warning('CONTENT_JSON environment variable not set.')
            return None
        import random
        if '|' in raw:
            url, json_path = [part.strip() for part in raw.split('|', 1)]
            logging.debug("Parsed CONTENT_JSON url: %s, json_path: %s", url, json_path)
        else:
            url, json_path = raw.strip(), None
            logging.debug("Parsed CONTENT_JSON url: %s, no json_path", url)

        try:
            logging.info("Fetching JSON from URL: %s", url)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logging.debug("Fetched JSON: %s", data)

            if json_path:
                # Support [RANDOM] in the path
                if '[RANDOM]' in json_path:
                    path_before, _, path_after = json_path.partition('[RANDOM]')
                    path_before = path_before.rstrip('.')
                    arr = extract_json_path(data, path_before)
                    if isinstance(arr, list) and arr:
                        idx = random.randint(0, len(arr) - 1)
                        logging.debug("[RANDOM] picked index %d from array of length %d", idx, len(arr))
                        element = arr[idx]
                        if path_after.strip():
                            sub_path = path_after.lstrip('.').lstrip('[]')
                            sub = extract_json_path(element, sub_path)
                            logging.debug("Sub-JSON after path '%s': %s", json_path, sub)
                            return sub
                        logging.debug("Sub-JSON after path '%s': %s", json_path, element)
                        return element
                    else:
                        logging.warning(
                            "[RANDOM] used but path '%s' did not resolve to a non-empty array.", path_before
                        )
                        return None
                else:
                    sub = extract_json_path(data, json_path)
                    logging.debug("Sub-JSON after path '%s': %s", json_path, sub)
                    return sub

            return data
        except Exception as e:
            logging.error("Failed to fetch or parse JSON from %s: %s", url, e)
            return None


    def get_timezone():
        tz = os.getenv('TIME_ZONE', 'UTC')
        logging.debug("Resolving timezone: %s", tz)
        if tz.upper() == 'UTC':
            logging.debug("Using UTC timezone.")
            return timezone.utc
        m = re.match(r'UTC([+-]\d+)$', tz.upper())
        if m:
            offset = int(m.group(1))
            logging.debug("Using timezone offset: UTC%+d", offset)
            return timezone(timedelta(hours=offset))
        logging.warning("Unrecognized TIME_ZONE '%s', defaulting to UTC.", tz)
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
        logging.debug("Resolved builtin.%s to '%s'", key, val)
        return val


    # Cache JSON root for repeated lookups
    _json_root = get_json_data()


    def replace_placeholder(match):
        source, key = match.group(1), match.group(2)
        logging.debug("Processing placeholder: source=%s, key=%s", source, key)
        if source == 'env':
            val = os.getenv(key, '')
            logging.debug("Resolved env.%s to '%s'", key, val)
            return val
        elif source == 'builtin':
            val = builtin_value(key)
            logging.debug("Resolved builtin.%s to '%s'", key, val)
            return val
        elif source == 'json':
            data = _json_root
            logging.debug("Using JSON root for lookup: %s", data)
            if data is None:
                logging.warning("No JSON data available for %s.%s", source, key)
                return match.group(0)
            val = extract_json_path(data, key)
            if val == '':
                logging.warning("Could not resolve %s.%s, leaving placeholder as-is.", source, key)
                return match.group(0)
            logging.debug("Resolved %s.%s to '%s'", source, key, str(val))
            return str(val)
        logging.warning("Unknown placeholder source: %s", source)
        return match.group(0)


    # Updated pattern to support env, builtin, json sources with flexible keys/paths
    pattern = re.compile(r'\@\{(env|builtin|json)\.([a-zA-Z0-9_\[\]\.]+)\}')
    # Apply replacements
    result = pattern.sub(replace_placeholder, content)
    logging.debug("Processed templated content: from %s --> '%s'", content, result)
    return result
