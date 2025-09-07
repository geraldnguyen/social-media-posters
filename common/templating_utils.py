"""Templated content processing utilities for social media actions."""

import os
import logging
import re
from datetime import datetime, timezone, timedelta

def process_templated_content_if_needed(content: str) -> str:
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
        logging.warning(f"Unknown placeholder source: {source}")
        return match.group(0)

    pattern = re.compile(r'\@\{(env|builtin)\.([A-Z0-9_]+)\}')
    result = pattern.sub(replace_placeholder, content)
    logging.info(f"Processed templated content: from {content} --> '{result}'")
    return result
