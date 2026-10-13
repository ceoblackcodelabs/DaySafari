from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Places", "0004_incluisiveexcluisive_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="awesomepackages",
            name="description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="destinations",
            name="description",
            field=models.TextField(),
        ),
    ]
