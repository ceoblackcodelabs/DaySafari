import django_ckeditor_5.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Home", "0013_alter_blogs_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogs",
            name="content",
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name="Content"),
        ),
    ]
