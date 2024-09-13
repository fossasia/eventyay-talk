from django import template
from django.template.defaulttags import url as built_in_url
from django.conf import settings

register = template.Library()


class URLNodeWithBasePath(template.Node):
    def __init__(self, node):
        self.node = node

    def render(self, context):
        # Get the URL from the original node
        resolved_url = self.node.render(context)

        # Prepend the base path (if defined) to the resolved URL
        base_path = settings.BASE_PATH.strip('/') if settings.BASE_PATH else ''
        if base_path:
            return f"/{base_path}/{resolved_url.lstrip('/')}"
        return resolved_url


@register.tag('url')
def base_url(parser, token):
    # Parse the original url tag and pass it to the wrapper
    original_node = built_in_url(parser, token)
    return URLNodeWithBasePath(original_node)
