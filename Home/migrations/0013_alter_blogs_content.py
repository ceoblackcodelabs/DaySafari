from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Home", "0012_alter_blogs_seo_description_alter_blogs_seo_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogs",
            name="content",
            field=models.TextField(),
        ),
    ]
