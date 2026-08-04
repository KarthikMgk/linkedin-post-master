"""Shared helpers for tests that consume Server-Sent Events responses."""

import json


def parse_sse_data(response):
    """
    Parse a Server-Sent Events response and return the first 'variants' or 'error'
    event payload as a dict (with the 'type' key included).
    Returns None if no such event is found.
    """
    for line in response.text.splitlines():
        if line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                if event.get("type") in ("variants", "error"):
                    return event
            except json.JSONDecodeError:
                continue
    return None
