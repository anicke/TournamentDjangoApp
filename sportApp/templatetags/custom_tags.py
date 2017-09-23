__author__ = 'Niklas Aronsson'
from django.conf import settings
from django import template
import django

register = template.Library()

@register.simple_tag
def get_admin():
    try:
        return django.utils.safestring.mark_safe(
            'Responsible: <a href="mailto:{1}">{0}</a>'.format(settings.ADMINS[0][0], settings.ADMINS[0][1]))
    except:
        return None

@register.simple_tag
def get_includes_path():
    return settings.INCLUDES_PATH

@register.filter
def substract(value, arg):
    return value - arg