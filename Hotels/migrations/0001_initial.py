"""Airbnb stays, moved here from the removed `Accomodations` app.

`replaces` tells Django that databases which already ran the old app's four
migrations are up to date: nothing runs against them, and the existing
`Accomodations_airbnb*` tables (with all their rows) simply become this app's.
A brand-new database runs this migration normally and creates the same tables.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    replaces = [
        ('Accomodations', '0001_initial'),
        ('Accomodations', '0002_mealplan_accomodations_contact_person_and_more'),
        ('Accomodations', '0003_accomodations_child_policy_and_more'),
        ('Accomodations', '0004_delete_airbnbbooking'),
    ]

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AirBNB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=100)),
                ('specification', models.CharField(choices=[('1b', '1 Bedroom'), ('2b', '2 Bedroom'), ('3b', '3 Bedroom'), ('4b', '4 Bedroom'), ('Studio', 'Studio')], max_length=50)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('price_per_night', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('max_guests', models.IntegerField(default=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'Accomodations_airbnb'},
        ),
        migrations.CreateModel(
            name='AirBNBImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default='AirBNB/default.jpg', upload_to='AirBNB/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('is_featured', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('airbnb', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='Hotels.airbnb')),
            ],
            options={'db_table': 'Accomodations_airbnbimage', 'ordering': ['order', '-uploaded_at']},
        ),
    ]
