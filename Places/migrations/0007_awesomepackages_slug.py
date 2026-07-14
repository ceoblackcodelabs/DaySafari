from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Places", "0006_alter_awesomepackages_description_ckeditor5"),
    ]

    operations = [
        migrations.AddField(
            model_name="awesomepackages",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, null=True, unique=True),
        ),
    ]
