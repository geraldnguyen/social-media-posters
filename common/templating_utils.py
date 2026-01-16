"""Templated content processing utilities for social media actions."""

import os
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from jsonpath_ng import parse as jsonpath_parse


# Module-level logger
logger = logging.getLogger(__name__)

# Sentinel value to indicate a JSON path was not found
class _NotFound:
    pass
_NOT_FOUND = _NotFound()

def extract_json_path(data, path):
    logger.debug("Extracting JSON path: %s from data type: %s", path, type(data).__name__)
    try:
        expr = jsonpath_parse(f'$.{path}')
        matches = [match.value for match in expr.find(data)]
        logger.debug("JSON path '%s' found %d matches", path, len(matches))
        
        if not matches:
            logger.debug("No matches found for path '%s'", path)
            # Return sentinel to indicate path not found
            return _NOT_FOUND
        if len(matches) == 1:
            val = matches[0]
            logger.debug("Single match for path '%s': type=%s, value='%s'", path, type(val).__name__, str(val)[:100])
            if isinstance(val, (dict, list)):
                return val
            # v1.17.0: Return actual values including None and empty string
            if val is None:
                return None
            if val == '':
                return ''
            return str(val)
        # If multiple matches, join as comma-separated string
        logger.debug("Multiple matches for path '%s': %d values", path, len(matches))
        result = ', '.join(str(m) for m in matches)
        logger.debug("Joined result: '%s'", result[:100])
        return result
    except Exception as e:
        logger.error("Error parsing JSON path '%s': %s", path, e)
        return _NOT_FOUND  # Return sentinel to indicate error


def get_json_data():
    raw = os.getenv('CONTENT_JSON')
    logger.debug("Raw CONTENT_JSON: %s", raw)
    if not raw:
        logger.warning('CONTENT_JSON environment variable not set.')
        return None
    
    import random
    logger.debug("Parsing CONTENT_JSON value: %s", raw)
    
    if '|' in raw:
        url, json_path = [part.strip() for part in raw.split('|', 1)]
        logger.debug("Parsed CONTENT_JSON url: %s, json_path: %s", url, json_path)
    else:
        url, json_path = raw.strip(), None
        logger.debug("Parsed CONTENT_JSON url: %s, no json_path", url)

    try:
        logger.info("Fetching JSON from URL: %s", url)
        resp = requests.get(url, timeout=10)
        logger.debug("HTTP response status: %d", resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("Fetched JSON data (length: %d characters)", len(str(data)))
        logger.debug("Fetched JSON keys: %s", list(data.keys()) if isinstance(data, dict) else "not a dict")

        if json_path:
            logger.info("Extracting JSON path: %s", json_path)
            # Support [RANDOM] in the path
            if '[RANDOM]' in json_path:
                logger.debug("Detected [RANDOM] selector in path")
                path_before, _, path_after = json_path.partition('[RANDOM]')
                path_before = path_before.rstrip('.')
                logger.debug("Path before [RANDOM]: %s", path_before)
                arr = extract_json_path(data, path_before)
                if isinstance(arr, list) and arr:
                    idx = random.randint(0, len(arr) - 1)
                    logger.debug("[RANDOM] picked index %d from array of length %d", idx, len(arr))
                    element = arr[idx]
                    if path_after.strip():
                        sub_path = path_after.lstrip('.').lstrip('[]')
                        logger.debug("Processing sub-path after [RANDOM]: %s", sub_path)
                        sub = extract_json_path(element, sub_path)
                        logger.debug("Sub-JSON after path '%s': %s", json_path, sub)
                        return sub
                    logger.debug("Sub-JSON after path '%s': %s", json_path, element)
                    return element
                else:
                    logger.warning(
                        "[RANDOM] used but path '%s' did not resolve to a non-empty array.", path_before
                    )
                    return None
            else:
                sub = extract_json_path(data, json_path)
                logger.debug("Sub-JSON after path '%s': %s", json_path, sub)
                return sub

        logger.info("Returning full JSON data (no path specified)")
        return data
    except requests.RequestException as e:
        logger.error("HTTP request failed for URL %s: %s", url, e)
        return None
    except ValueError as e:
        logger.error("Failed to parse JSON response from %s: %s", url, e)
        return None
    except Exception as e:
        logger.error("Failed to fetch or parse JSON from %s: %s", url, e)
        return None


def get_timezone():
    tz = os.getenv('TIME_ZONE', 'UTC')
    logger.debug("Resolving timezone from TIME_ZONE env var: %s", tz)
    if tz.upper() == 'UTC':
        logger.debug("Using UTC timezone.")
        return timezone.utc
    m = re.match(r'UTC([+-]\d+)$', tz.upper())
    if m:
        offset = int(m.group(1))
        logger.debug("Using timezone offset: UTC%+d", offset)
        return timezone(timedelta(hours=offset))
    logger.warning("Unrecognized TIME_ZONE '%s', defaulting to UTC.", tz)
    return timezone.utc


def builtin_value(key: str) -> str:
    now = datetime.now(get_timezone())
    logger.debug("Resolving builtin value for key: %s using timezone: %s", key, now.tzinfo)
    if key == 'CURR_DATE':
        val = now.strftime('%Y-%m-%d')
        logger.debug("Resolved builtin.CURR_DATE to '%s'", val)
    elif key == 'CURR_TIME':
        val = now.strftime('%H:%M:%S')
        logger.debug("Resolved builtin.CURR_TIME to '%s'", val)
    elif key == 'CURR_DATETIME':
        val = now.strftime('%Y-%m-%d %H:%M:%S')
        logger.debug("Resolved builtin.CURR_DATETIME to '%s'", val)
    else:
        logger.warning("Unknown builtin key: %s", key)
        val = ''
        logger.debug("Resolved builtin.%s to empty string", key)
    return val


def _process_content_with_json_root(content: str, json_root) -> str:
    """Internal function to process templated content with a given JSON root."""
    logger.debug("Processing templated content (length: %d)", len(content))
    logger.debug("JSON root available: %s", json_root is not None)

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
        logger.debug("Parsing function call: %s", expr)
        
        # Try matching with parentheses first
        call_match = re.match(r'^([a-zA-Z_][\w\-]*)\((.*)\)$', expr)
        if call_match:
            func_name = call_match.group(1)
            arg_str = call_match.group(2).strip()
            logger.debug("Function name: %s, arguments string: %s", func_name, arg_str)
            if not arg_str:
                logger.debug("No arguments for function %s", func_name)
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
            
            logger.debug("Parsed function %s with %d arguments: %s", func_name, len(args), args)
            return func_name, args
        
        # Try matching without parentheses (v1.17.0 feature)
        # Format: function_name 'arg1' arg2 'arg3'
        # or: function_name json.xxx json.yyy
        no_paren_match = re.match(r'^([a-zA-Z_][\w\-]*)\s+(.+)$', expr)
        if no_paren_match:
            func_name = no_paren_match.group(1)
            args_str = no_paren_match.group(2).strip()
            logger.debug("Function name (no parens): %s, arguments string: %s", func_name, args_str)
            
            # Parse arguments - they can be quoted strings, json expressions, or numbers
            # Split by whitespace and commas, but respect quotes
            args = []
            current_arg = []
            in_quotes = False
            quote_char = None
            
            for char in args_str:
                if char in ('"', "'"):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                    current_arg.append(char)
                elif (char in (' ', ',')) and not in_quotes:
                    arg = ''.join(current_arg).strip()
                    if arg:
                        args.append(strip_quotes(arg))
                    current_arg = []
                else:
                    current_arg.append(char)
            
            # Add final argument
            arg = ''.join(current_arg).strip()
            if arg:
                args.append(strip_quotes(arg))
            
            logger.debug("Parsed function (no parens) %s with %d arguments: %s", func_name, len(args), args)
            return func_name, args
        
        logger.debug("Not a function call, returning as-is: %s", expr)
        return expr, None

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

    def resolve_argument(arg, json_root):
        """Resolve an argument that could be a literal string or a json expression.
        
        v1.17.0: Support json.xxx expressions as function parameters.
        """
        if not arg:
            return arg
        
        # Check if it's a json expression (json.xxx format)
        if arg.startswith('json.'):
            json_path = arg[5:]  # Remove 'json.' prefix
            logger.debug("Resolving json expression argument: %s", arg)
            if json_root is None:
                logger.warning("No JSON data available for argument %s", arg)
                return arg
            resolved = extract_json_path(json_root, json_path)
            if resolved is _NOT_FOUND:
                logger.warning("Could not resolve json argument %s", arg)
                return ''  # Return empty string for not found in arguments
            logger.debug("Resolved json argument %s to: %s", arg, str(resolved)[:100])
            return resolved
        
        # Otherwise, it's a literal string
        return arg
    
    def apply_operations(value, operations, json_root=None):
        logger.debug("Applying %d operations to value (type: %s)", len(operations), type(value).__name__)
        original_value = value
        for i, op in enumerate(operations):
            if not op:
                continue
            logger.debug("Applying operation %d: %s", i+1, op)

            if op.startswith('each:'):
                func_expr = op[len('each:'):].strip()
                func_name, func_arg = parse_function_call(func_expr)
                if func_name == 'prefix':
                    if not isinstance(value, (list, tuple)):
                        logger.warning(
                            "each:prefix operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    prefix_arg = resolve_argument(func_arg[0], json_root) if func_arg else ''
                    prefix = '' if not prefix_arg else str(prefix_arg)
                    value = [prefix + str(item) for item in value]
                    logger.debug("Applied each:prefix('%s') to list", prefix)
                elif func_name.startswith('case_'):
                    if not isinstance(value, (list, tuple)):
                        logger.warning(
                            "each:%s operation requires list input but received %s", func_name, type(value).__name__
                        )
                        continue
                    value = [apply_case_transformation(str(item), func_name) for item in value]
                    logger.debug("Applied each:%s to list items", func_name)
                elif func_name == 'max_length':
                    if not isinstance(value, (list, tuple)):
                        logger.warning(
                            "each:max_length operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    if not func_arg or len(func_arg) < 1:
                        logger.warning("each:max_length requires at least 1 argument (max_length)")
                        continue
                    try:
                        max_len = int(func_arg[0])
                        suffix = func_arg[1] if len(func_arg) > 1 else ''
                        value = [apply_max_length(str(item), max_len, str(suffix)) for item in value]
                        logger.debug("Applied each:max_length(%d, '%s') to list items", max_len, suffix)
                    except (ValueError, IndexError) as e:
                        logger.warning("Invalid arguments for each:max_length: %s", e)
                else:
                    logger.warning("Unsupported each operation '%s'", func_name)
            else:
                func_name, func_arg = parse_function_call(op)
                if func_name == 'join':
                    if not isinstance(value, (list, tuple)):
                        logger.warning(
                            "join operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    separator_arg = resolve_argument(func_arg[0], json_root) if func_arg else ''
                    separator = '' if not separator_arg else str(separator_arg)
                    value = separator.join(str(item) for item in value)
                    logger.debug("Applied join('%s') to list", separator)
                elif func_name == 'max_length':
                    if not func_arg or len(func_arg) < 1:
                        logger.warning("max_length requires at least 1 argument (max_length)")
                        continue
                    try:
                        max_len = int(func_arg[0])
                        suffix = func_arg[1] if len(func_arg) > 1 else ''
                        value = apply_max_length(str(value), max_len, str(suffix))
                        logger.debug("Applied max_length(%d, '%s') to string", max_len, suffix)
                    except (ValueError, IndexError) as e:
                        logger.warning("Invalid arguments for max_length: %s", e)
                elif func_name == 'join_while':
                    if not isinstance(value, (list, tuple)):
                        logger.warning(
                            "join_while operation requires list input but received %s", type(value).__name__
                        )
                        continue
                    if not func_arg or len(func_arg) < 2:
                        logger.warning("join_while requires 2 arguments (separator, max_length)")
                        continue
                    try:
                        separator_arg = resolve_argument(func_arg[0], json_root)
                        separator = str(separator_arg)
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
                        logger.debug("Applied join_while('%s', %d) resulting in %d items", separator, max_len, len(result_parts))
                    except (ValueError, IndexError) as e:
                        logger.warning("Invalid arguments for join_while: %s", e)
                elif func_name == 'random':
                    if not isinstance(value, (list, tuple)):
                        raise ValueError("random() operation requires list input")
                    if not value:
                        raise ValueError("random() operation requires non-empty list")
                    import random
                    idx = random.randint(0, len(value) - 1)
                    value = value[idx]
                    logger.info("Applied random() selecting index %d - obtained %s", idx, value)
                elif func_name == 'attr':
                    if not isinstance(value, dict):
                        raise ValueError("attr() operation requires dict input but provided %s of type %s", value, type(value).__name__)
                    if not func_arg or len(func_arg) < 1:
                        raise ValueError("attr() requires at least 1 argument (attribute name)")
                    attr_name = func_arg[0]
                    if attr_name not in value:
                        raise ValueError(f"attr() attribute '{attr_name}' not found in object")
                    value = value[attr_name]
                    logger.debug("Applied attr('%s')", attr_name)
                elif func_name == 'or':
                    # v1.17.0: or operation - return left-hand-side if truthy, else evaluate and return right-hand-side
                    def is_truthy(val):
                        """Check if a value is truthy (not null, not empty, not blank)."""
                        if val is None:
                            return False
                        if isinstance(val, str):
                            return val.strip() != ''
                        if isinstance(val, (list, tuple, dict)):
                            return len(val) > 0
                        return bool(val)
                    
                    if is_truthy(value):
                        logger.debug("or: Left-hand-side is truthy, keeping value: %s", str(value)[:100])
                    else:
                        # Value is not truthy, evaluate the right-hand-side
                        if not func_arg or len(func_arg) < 1:
                            logger.warning("or operation requires at least 1 argument (fallback value)")
                            continue
                        
                        fallback_arg = func_arg[0]
                        logger.debug("or: Left-hand-side is falsy, evaluating fallback: %s", fallback_arg)
                        
                        # The fallback can be a literal string or a json expression
                        fallback_value = resolve_argument(fallback_arg, json_root)
                        value = fallback_value
                        logger.debug("or: Using fallback value: %s", str(value)[:100])
                else:
                    logger.warning("Unsupported pipeline operation '%s'", func_name)

        if value != original_value:
            logger.debug("Operations transformed value from '%s' to '%s'", str(original_value)[:50], str(value)[:50])
        return value

    def replace_placeholder(match):
        source, expression = match.group(1), match.group(2)
        logger.debug("Processing placeholder: source=%s, expression=%s", source, expression)

        segments = split_pipeline(expression)
        logger.debug("Split expression into %d segments: %s", len(segments), segments)
        if not segments:
            logger.warning("Empty placeholder expression for source '%s'", source)
            return match.group(0)

        key = segments[0]
        operations = segments[1:]
        logger.debug("Key: %s, Operations: %s", key, operations)

        if source == 'env':
            val = os.getenv(key, '')
            logger.debug("Resolved env.%s to '%s'", key, val)
        elif source == 'builtin':
            val = builtin_value(key)
            logger.debug("Resolved builtin.%s to '%s'", key, val)
        elif source == 'json':
            data = json_root
            logger.debug("Using JSON root for lookup: %s", data is not None)
            if data is None:
                logger.warning("No JSON data available for %s.%s", source, key)
                return match.group(0)
            val = extract_json_path(data, key)
            # v1.17.0: Check if path was not found (sentinel value)
            if val is _NOT_FOUND:
                logger.warning("Could not resolve %s.%s, leaving placeholder as-is.", source, key)
                return match.group(0)
            # v1.17.0: Allow empty strings and None to be processed by operations (e.g., 'or')
            logger.debug("Resolved %s.%s to '%s'", source, key, str(val)[:100])
        else:
            logger.warning("Unknown placeholder source: %s", source)
            return match.group(0)

        if operations:
            logger.debug("Applying %d operations to resolved value", len(operations))
            val = apply_operations(val, operations, json_root)

        result = str(val)
        logger.debug("Placeholder replacement result: '%s'", result[:100])
        return result

    # Updated pattern to support env, builtin, json sources with flexible keys/paths
    pattern = re.compile(r'\@\{(env|builtin|json)\.([^}]+)\}')
    logger.debug("Searching for placeholders in content using pattern: %s", pattern.pattern)
    
    # Apply replacements
    result = pattern.sub(replace_placeholder, content)
    logger.debug("Processed templated content: from %s --> '%s'", content, result[:100])
    return result


def process_templated_contents(*contents: str) -> tuple[str, ...]:
    """Process multiple templated content strings using the same JSON root.

    Fetches CONTENT_JSON only once and applies it to all provided content strings.
    Returns a tuple of processed strings in the same order.
    """
    logger.info("Processing %d content strings with templating", len(contents))
    json_root = get_json_data()
    logger.debug("Fetched JSON root for template processing")
    
    results = []
    for i, content in enumerate(contents):
        logger.info("Processing content string %d (length: %d): %s", i+1, len(content), content)
        processed = _process_content_with_json_root(content, json_root)
        results.append(processed)
        logger.info("Content string %d processed (result length: %d): %s", i+1, len(processed), processed)
    
    logger.info("Completed template processing for %d content strings", len(contents))
    return tuple(results)
