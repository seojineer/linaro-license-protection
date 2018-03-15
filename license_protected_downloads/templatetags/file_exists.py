from django import template
from django.core.files.storage import default_storage
from django.conf import settings

register = template.Library()

@register.filter(name='file_exists')
def file_exists(filepath):
    if default_storage.exists(settings.PROJECT_ROOT + '/license_protected_downloads/' + filepath):
        return filepath
    else:
        new_filepath = settings.STATIC_URL + 'other.png'
        return new_filepath
