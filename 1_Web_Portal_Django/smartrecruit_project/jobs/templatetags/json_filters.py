from django import template
import json

register = template.Library()

@register.filter
def json_load(value):
    """Parses a JSON string into a Python object."""
    try:
        if isinstance(value, dict):
             return value
        return json.loads(value)
    except (ValueError, TypeError):
        return {}
