"""Templated content processing utilities for social media actions."""

import os
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from jsonpath_ng import parse as jsonpath_parse


def process_templated_content_if_needed(content: str) -> str:
    """Process content with support for env, builtin and json templates.

    Supported placeholders:
    - @{env.VAR}
    - @{builtin.CURR_DATE|CURR_TIME|CURR_DATETIME}
    - @{json.path.to.field}
    """

    def split_pipeline(expression: str):
        segments = []
        current = []
        in_single = False
        in_double = False
        depth = 0

        for char in expression:
            if char == '|' and not in_single and not in_double and depth == 0:
                segment = ''.join(current).strip()
                if segment:
                    segments.append(segment)
                current = []
                continue

            current.append(char)

            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == '(' and not in_single and not in_double:
                depth += 1
            elif char == ')' and not in_single and not in_double and depth > 0:
                depth -= 1

        segment = ''.join(current).strip()
        if segment:
            segments.append(segment)

        return segments

    def strip_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            return value[1:-1]
        return value

    def parse_function_call(expr: str):
        expr = expr.strip()
        call_match = re.match(r'^([a-zA-Z_][\w\-]*)\((.*)\)$', expr)
        if not call_match:
            return expr, None

        func_name = call_match.group(1)
        arg_str = call_match.group(2).strip()
        if not arg_str:
            return func_name, []
        
        # Parse multiple arguments separated by commas
        args = []
        current_arg = []
        in_quotes = False
        quote_char = None
        paren_depth = 0
        
        for char in arg_str:
            if char in ('"', "'") and paren_depth == 0:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == ',' and not in_quotes and paren_depth == 0:
                args.append(strip_quotes(''.join(current_arg).strip()))
                current_arg = []
                continue
            
            current_arg.append(char)
        
        if current_arg:
            args.append(strip_quotes(''.join(current_arg).strip()))
        
        return func_name, args

    def apply_case_transformation(text: str, case_type: str) -> str:
        """Apply case transformation to a string."""
        if case_type == 'case_title':
            return text.title()
        elif case_type == 'case_sentence':
            return text.capitalize()
        elif case_type == 'case_upper':
            return text.upper()
        elif case_type == 'case_lower':
            return text.lower()
        elif case_type == 'case_pascal':
            # Convert to PascalCase: remove spaces and capitalize each word
            words = re.split(r'[\s_-]+', text.strip())
            return ''.join(word.capitalize() for word in words if word)
        elif case_type == 'case_kebab':
            # Convert to kebab-case: lowercase with hyphens
            # First handle CamelCase by inserting hyphens before uppercase letters (except first)
            text = re.sub(r'(?<!^)(?=[A-Z])', '-', text)
            # Replace spaces and underscores with hyphens
            text = re.sub(r'[\s_]+', '-', text)
            # Convert to lowercase and clean up multiple hyphens
            return re.sub(r'-+', '-', text.lower()).strip('-')
        elif case_type == 'case_snake':
            # Convert to snake_case: lowercase with underscores
            # First handle CamelCase by inserting underscores before uppercase letters (except first)
            text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
            # Replace spaces and hyphens with underscores
            text = re.sub(r'[\s-]+', '_', text)
            # Convert to lowercase and clean up multiple underscores
            return re.sub(r'_+', '_', text.lower()).strip('_')
        else:
            return text

    def apply_max_length(text: str, max_length: int, suffix: str = '') -> str:
        """Clip text at word boundary if it exceeds max_length and append suffix."""
        text = str(text)
        if len(text) <= max_length:
            return text
        
        if max_length <= 0:
            return suffix
        
        # Find the last space before or at max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space == -1:
            # No space found, clip at max_length
            result = truncated
        else:
            # Clip at last word boundary
            result = truncated[:last_space]
        
        return result + suffix

    def apply_operations(value, operations):
        for op in operations:
            if not op:
                continue

            if op.startswith('each:'):
                func_expr = op[len('each:'):].strip()
                func_name, func_arg = parse_function_call(func_expr)
                if func_name == 'prefix':
                    if not isinstance(value, (list, tuple)):
                        logging.warning(
                            "each:prefix operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    prefix = '' if not func_arg else str(func_arg[0] if func_arg else '')
                    value = [prefix + str(item) for item in value]
                elif func_name.startswith('case_'):
                    if not isinstance(value, (list, tuple)):
                        logging.warning(
                            "each:%s operation requires list input but received %s", func_name, type(value).__name__
                        )
                        continue
                    value = [apply_case_transformation(str(item), func_name) for item in value]
                elif func_name == 'max_length':
                    if not isinstance(value, (list, tuple)):
                        logging.warning(
                            "each:max_length operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    if not func_arg or len(func_arg) < 1:
                        logging.warning("each:max_length requires at least 1 argument (max_length)")
                        continue
                    try:
                        max_len = int(func_arg[0])
                        suffix = func_arg[1] if len(func_arg) > 1 else ''
                        value = [apply_max_length(str(item), max_len, str(suffix)) for item in value]
                    except (ValueError, IndexError) as e:
                        logging.warning("Invalid arguments for each:max_length: %s", e)
                else:
                    logging.warning("Unsupported each operation '%s'", func_name)
            else:
                func_name, func_arg = parse_function_call(op)
                if func_name == 'join':
                    if not isinstance(value, (list, tuple)):
                        logging.warning(
                            "join operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    separator = '' if not func_arg else str(func_arg[0] if func_arg else '')
                    value = separator.join(str(item) for item in value)
                elif func_name == 'max_length':
                    if not func_arg or len(func_arg) < 1:
                        logging.warning("max_length requires at least 1 argument (max_length)")
                        continue
                    try:
                        max_len = int(func_arg[0])
                        suffix = func_arg[1] if len(func_arg) > 1 else ''
                        value = apply_max_length(str(value), max_len, str(suffix))
                    except (ValueError, IndexError) as e:
                        logging.warning("Invalid arguments for max_length: %s", e)
                elif func_name == 'join_while':
                    if not isinstance(value, (list, tuple)):
                        logging.warning(
                            "join_while operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    if not func_arg or len(func_arg) < 2:
                        logging.warning("join_while requires 2 arguments (separator, max_length)")
                        continue
                    try:
                        separator = str(func_arg[0])
                        max_len = int(func_arg[1])
                        result_parts = []
                        for item in value:
                            item_str = str(item)
                            if not result_parts:
                                # First item
                                if len(item_str) <= max_len:
                                    result_parts.append(item_str)
                                else:
                                    break
                            else:
                                # Check if adding this item would exceed max_len
                                tentative = separator.join(result_parts) + separator + item_str
                                if len(tentative) <= max_len:
                                    result_parts.append(item_str)
                                else:
                                    break
                        value = separator.join(result_parts)
                    except (ValueError, IndexError) as e:
                        logging.warning("Invalid arguments for join_while: %s", e)
                else:
                    logging.warning("Unsupported pipeline operation '%s'", func_name)

        return value

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
        source, expression = match.group(1), match.group(2)
        logging.debug("Processing placeholder: source=%s, expression=%s", source, expression)

        segments = split_pipeline(expression)
        if not segments:
            logging.warning("Empty placeholder expression for source '%s'", source)
            return match.group(0)

        key = segments[0]
        operations = segments[1:]

        if source == 'env':
            val = os.getenv(key, '')
            logging.debug("Resolved env.%s to '%s'", key, val)
        elif source == 'builtin':
            val = builtin_value(key)
            logging.debug("Resolved builtin.%s to '%s'", key, val)
        elif source == 'json':
            data = _json_root
            logging.debug("Using JSON root for lookup: %s", data)
            if data is None:
                logging.warning("No JSON data available for %s.%s", source, key)
                return match.group(0)
            val = extract_json_path(data, key)
            if val == '' or val is None:
                logging.warning("Could not resolve %s.%s, leaving placeholder as-is.", source, key)
                return match.group(0)
            logging.debug("Resolved %s.%s to '%s'", source, key, str(val))
        else:
            logging.warning("Unknown placeholder source: %s", source)
            return match.group(0)

        if operations:
            val = apply_operations(val, operations)

        return str(val)


    # Updated pattern to support env, builtin, json sources with flexible keys/paths
    pattern = re.compile(r'\@\{(env|builtin|json)\.([^}]+)\}')
    # Apply replacements
    result = pattern.sub(replace_placeholder, content)
    logging.debug("Processed templated content: from %s --> '%s'", content, result)
    return result
