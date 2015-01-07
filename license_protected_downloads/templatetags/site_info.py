import os

from django import template

register = template.Library()

_name = os.environ.get('SITE_NAME', 'Linaro Snapshots')


@register.simple_tag
def site_name():
    return _name
