"""Responsive, modern-format images without changing any stored file.

    {% load image_tags %}
    <img src="{{ package.image|thumb:640 }}" ...>

Creates (once, lazily) a resized WebP copy under MEDIA_ROOT/thumbs/<width>/ and
returns its URL. Falls back to the original image on any problem, so a template
never breaks because of a missing or odd file.
"""
import hashlib
import os

from django import template
from django.conf import settings
from PIL import Image, ImageOps

register = template.Library()


@register.filter
def thumb(image, width=640):
    try:
        width = int(width)
        if not image:
            return ''
        src = image.path
        mtime = int(os.path.getmtime(src))
        key = hashlib.md5(f'{image.name}:{mtime}'.encode()).hexdigest()[:12]
        rel = f'thumbs/{width}/{os.path.splitext(os.path.basename(image.name))[0]}_{key}.webp'
        dest = os.path.join(settings.MEDIA_ROOT, rel)
        if not os.path.exists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                if im.width > width:
                    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
                im.convert('RGB').save(dest + '.tmp', 'WEBP', quality=78, method=4)
            os.replace(dest + '.tmp', dest)
        return settings.MEDIA_URL + rel
    except Exception:
        try:
            return image.url
        except Exception:
            return ''
