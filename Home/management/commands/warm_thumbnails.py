"""Pre-generate the WebP thumbnails the templates use, so the first visitor
never pays for image resizing.   python manage.py warm_thumbnails"""
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import ImageField

from Home.templatetags.image_tags import thumb

# Only the sizes the templates actually request (see {{ x|thumb:N }} usages)
WIDTHS = {
    'HeroSlide': (640, 800, 1200, 1600),
    'AboutImage': (900,),
    'Testimonials': (200,),
}
DEFAULT_WIDTHS = (640,)


class Command(BaseCommand):
    help = 'Generate WebP thumbnails for every image in the database'

    def handle(self, *args, **opts):
        made = 0
        for model in apps.get_models():
            fields = [f for f in model._meta.get_fields() if isinstance(f, ImageField)]
            if not fields or model._meta.app_label in ('admin', 'auth'):
                continue
            for obj in model.objects.all().iterator():
                for field in fields:
                    image = getattr(obj, field.name)
                    if not image:
                        continue
                    for width in WIDTHS.get(model.__name__, DEFAULT_WIDTHS):
                        thumb(image, width)
                        made += 1
        self.stdout.write(self.style.SUCCESS(f'Checked/created {made} thumbnails.'))
