from django import template
from django.conf import settings
from django.utils.html import format_html, format_html_join

register = template.Library()
SITE = 'https://daysafarisadventures.co.ke'


@register.simple_tag
def hreflang_links(request):
    """<link rel="alternate" hreflang> for every site language (same page, other prefix)."""
    codes = [code for code, _ in settings.LANGUAGES]
    path = request.path
    for code in codes:
        if path == f'/{code}' or path.startswith(f'/{code}/'):
            path = path[len(code) + 1:] or '/'
            break
    else:
        return ''
    links = [(code, f'{SITE}/{code}{path}') for code in codes]
    links.append(('x-default', f'{SITE}/{settings.LANGUAGE_CODE}{path}'))
    return format_html_join('\n        ', '<link rel="alternate" hreflang="{}" href="{}">', links)
