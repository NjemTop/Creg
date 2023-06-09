import json
from django import template

register = template.Library()

@register.filter(is_safe=True)
def tojson(value):
    return json.dumps(value)
