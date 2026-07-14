import django_ckeditor_5.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Places", "0005_alter_awesomepackages_description_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="awesomepackages",
            name="description",
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="destinations",
            name="description",
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name="Description"),
        ),
    ]
