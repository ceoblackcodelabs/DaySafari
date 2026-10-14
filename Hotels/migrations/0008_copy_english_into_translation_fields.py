"""Copy the existing (English) text into the new English translation columns.

modeltranslation reads the active language's column, so without this the English pages would be empty.
Safe to run twice: it only fills columns that are still empty.
"""
from django.db import migrations

FIELDS = {'Hotel': ['location', 'summary', 'description', 'amenities', 'child_policy'], 'HotelImage': ['caption'], 'AirBNB': ['title', 'location', 'description'], 'AirBNBImage': ['caption']}


def copy_english(apps, schema_editor):
    for model_name, fields in FIELDS.items():
        Model = apps.get_model('Hotels', model_name)
        for obj in Model.objects.all().iterator():
            changed = []
            for field in fields:
                if not getattr(obj, field + '_en') and getattr(obj, field):
                    setattr(obj, field + '_en', getattr(obj, field))
                    changed.append(field + '_en')
            if changed:
                obj.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [('Hotels', '0007_content_translation_fields')]

    operations = [migrations.RunPython(copy_english, migrations.RunPython.noop)]
