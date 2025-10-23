"""
Core templating functions.

This module defines process_text() which resolves template tags (delimited by {{ and }})
using the provided context. Both "normal" and "table" modes are supported. In
"normal" mode, all tags are replaced inline (with list results joined by a delimiter).
In "table" mode, if the text contains exactly one tag, its resolved value is used
to produce the final output (if a list then a list of outputs is returned).
Permission checking is enforced during parsing.
"""

import re
from typing import Callable, Optional

from .exceptions import BadTemplateModeError, EmptyDataException
from .resolve import resolve_formatted_tag


def get_matching_tags(text: str):
    pattern = re.compile(r"\{\{(.*?)\}\}")
    return list(pattern.finditer(text))


def process_text(
    text: str,
    context: dict,
    check_permissions: Optional[Callable[[object], bool]] = None,
    mode: str = "normal",
    delimiter: str = ", ",
    fail_if_empty: bool = False,
):
    """
    Process text containing template tags.

    This implementation searches for all tags via re.finditer and rebuilds the text.

    In "normal" mode, every tag is replaced inline: if a resolved tag is a list,
    its items are joined with the specified delimiter.

    In "table" mode, the text must contain exactly one tag. If the resolved value is a list,
    a list of strings is returned, where each string is the original text with that tag replaced
    by one of the list items. Otherwise, the tag is replaced inline.
    """
    matches = get_matching_tags(text)

    # For table mode, ensure exactly one tag is present.
    if mode == "table" and len(matches) != 1:
        raise BadTemplateModeError(
            "Table mode supports mixed text with exactly one placeholder."
        )

    # If no tags found, return text as-is.
    if not matches:
        return text

    # For normal mode, we rebuild the text by replacing each tag
    # with its processed value.
    result_parts = []
    last_index = 0
    for m in matches:
        start, end = m.span()
        before = text[last_index:start]
        result_parts.append(before)

        # Raw match.
        raw_expr = m.group(1).strip()

        # Process the actual tag expression.
        value = resolve_formatted_tag(
            expr=raw_expr,
            context=context,
            check_permissions=check_permissions,
        )

        # If the value is empty and fail_if_empty is set, raise an error.
        if fail_if_empty and value in ("", None):
            raise EmptyDataException(
                f"Processed value for '{raw_expr}' is empty, but it is required - check context."
            )

        if isinstance(value, list):
            # Special case: table mode with a list value. Only one placeholder
            # is present, so we return now (a list of strings).
            if mode == "table":
                after = text[end:]
                return [before + str(x or "") + after for x in value]

            # In normal mode, list values are joined using the delimiter.
            else:
                replacement = delimiter.join(str(x or "") for x in value)

        # Not a list: the replacement is simply the value.
        else:
            replacement = str(value)

        # Append the resolved value to the result.
        result_parts.append(replacement)

        # Move the last index to the end of the current match.
        last_index = end

    # Append the remaining text after the last match.
    result_parts.append(text[last_index:])

    # Join the parts to get the final result.
    return "".join(result_parts)


def process_text_recursive(
    obj,
    context: dict,
    check_permissions: Optional[Callable[[object], bool]] = None,
    mode: str = "normal",
    delimiter: str = ", ",
    fail_if_empty: bool = False,
):

    if isinstance(obj, str):
        return process_text(
            obj, context, check_permissions, mode, delimiter, fail_if_empty
        )

    elif isinstance(obj, list):
        return [
            process_text_recursive(
                item, context, check_permissions, mode, delimiter, fail_if_empty
            )
            for item in obj
        ]

    elif isinstance(obj, dict):
        return {
            key: process_text_recursive(
                value, context, check_permissions, mode, delimiter, fail_if_empty
            )
            for key, value in obj.items()
        }

    return obj
