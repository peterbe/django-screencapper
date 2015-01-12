import json

from django.contrib.staticfiles.templatetags.staticfiles import static
from jingo import register


static = register.function(static)

@register.function
def pretty_print_json(data, indent=4, sort_keys=False):
    return json.dumps(data, indent=indent, sort_keys=sort_keys)
