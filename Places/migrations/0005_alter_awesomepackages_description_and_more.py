import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Places", "0004_incluisiveexcluisive_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="awesomepackages",
            name="description",
            field=ckeditor_uploader.fields.RichTextUploadingField(),
        ),
        migrations.AlterField(
            model_name="destinations",
            name="description",
            field=ckeditor_uploader.fields.RichTextUploadingField(),
        ),
    ]
