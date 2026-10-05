"""Upload storage that shrinks images as they are saved.

Photos straight from a camera are 3-8 MB; the site never shows them larger
than ~1400px wide. Every ImageField upload now goes through this storage, so
admins can upload originals and visitors still get fast pages.
"""
import io
import os

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageOps

MAX_WIDTH = 1600
JPEG_QUALITY = 78
MIN_BYTES_TO_OPTIMIZE = 200 * 1024
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


class OptimizedMediaStorage(FileSystemStorage):
    def _save(self, name, content):
        if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS and getattr(content, 'size', 0) > MIN_BYTES_TO_OPTIMIZE:
            try:
                content = self._optimize(name, content)
            except Exception:  # never block an upload because optimisation failed
                content.seek(0)
        return super()._save(name, content)

    @staticmethod
    def _optimize(name, content):
        content.seek(0)
        original = content.read()
        image = Image.open(io.BytesIO(original))
        fmt = image.format
        image = ImageOps.exif_transpose(image)
        if image.width > MAX_WIDTH:
            image = image.resize((MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)), Image.LANCZOS)
        out = io.BytesIO()
        if fmt == 'JPEG':
            image.convert('RGB').save(out, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
        elif fmt == 'PNG':
            image.save(out, 'PNG', optimize=True)
        else:
            return ContentFile(original, name=name)
        smaller = out.getvalue()
        return ContentFile(smaller if len(smaller) < len(original) else original, name=name)
