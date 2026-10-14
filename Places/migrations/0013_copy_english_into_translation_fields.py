"""Copy the existing (English) text into the new English translation columns.

modeltranslation reads the active language's column, so without this the English pages would be empty.
Safe to run twice: it only fills columns that are still empty.
"""
from django.db import migrations

FIELDS = {'DestinationImage': ['caption'], 'DestinationsCategory': ['location', 'category'], 'Destinations': ['name', 'description'], 'IncluisiveExcluisive': ['name'], 'AwesomePackages': ['name', 'location', 'description'], 'Itinerary': ['title', 'description', 'activities', 'accommodation', 'meals']}


def copy_english(apps, schema_editor):
    for model_name, fields in FIELDS.items():
        Model = apps.get_model('Places', model_name)
        for obj in Model.objects.all().iterator():
            changed = []
            for field in fields:
                if not getattr(obj, field + '_en') and getattr(obj, field):
                    setattr(obj, field + '_en', getattr(obj, field))
                    changed.append(field + '_en')
            if changed:
                obj.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [('Places', '0012_content_translation_fields')]

    operations = [migrations.RunPython(copy_english, migrations.RunPython.noop)]
