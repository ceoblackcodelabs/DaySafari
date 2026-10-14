"""Copy the existing (English) text into the new English translation columns.

modeltranslation reads the active language's column, so without this the English pages would be empty.
Safe to run twice: it only fills columns that are still empty.
"""
from django.db import migrations

FIELDS = {'Services': ['name', 'description'], 'GalleryCategory': ['name'], 'AboutImage': ['caption'], 'HeroSlide': ['eyebrow_text', 'title', 'subtitle', 'button_text'], 'Testimonials': ['location', 'feedback'], 'Blogs': ['title', 'seo_title', 'seo_description', 'content'], 'Brochure': ['title', 'description'], 'ItineraryTreking': ['title', 'description', 'activities', 'accommodation', 'meals'], 'Trekking': ['name', 'location', 'description'], 'Ad': ['title', 'description', 'button_text']}


def copy_english(apps, schema_editor):
    for model_name, fields in FIELDS.items():
        Model = apps.get_model('Home', model_name)
        for obj in Model.objects.all().iterator():
            changed = []
            for field in fields:
                if not getattr(obj, field + '_en') and getattr(obj, field):
                    setattr(obj, field + '_en', getattr(obj, field))
                    changed.append(field + '_en')
            if changed:
                obj.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [('Home', '0018_content_translation_fields')]

    operations = [migrations.RunPython(copy_english, migrations.RunPython.noop)]
