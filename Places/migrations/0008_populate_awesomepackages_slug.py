from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    AwesomePackages = apps.get_model("Places", "AwesomePackages")
    seen = set()

    for package in AwesomePackages.objects.filter(slug__isnull=True).iterator():
        base_slug = slugify(f"{package.name}-{package.location}") or slugify(package.name) or f"package-{package.pk}"
        slug = base_slug
        counter = 2

        while slug in seen or AwesomePackages.objects.filter(slug=slug).exclude(pk=package.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        seen.add(slug)
        package.slug = slug
        package.save(update_fields=["slug"])


def reverse_populate_slugs(apps, schema_editor):
    AwesomePackages = apps.get_model("Places", "AwesomePackages")
    AwesomePackages.objects.update(slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ("Places", "0007_awesomepackages_slug"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, reverse_populate_slugs),
    ]
