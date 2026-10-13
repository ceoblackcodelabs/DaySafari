"""Remove the 12 sample hotels that were carried over from the old Accomodations app.

They were invented placeholder records (stock photos, made-up descriptions), not real properties. Only these exact
records are removed (matched by name + place + country); hotels you add or seed afterwards are never touched.
Safety rules:
* a sample hotel that already has a customer enquiry is UNPUBLISHED instead of deleted, so no lead is ever lost;
* photo files are deleted only after the database change has committed successfully.
Safe to run repeatedly and on a fresh database (nothing matches, nothing happens).
"""
import glob
import os

from django.conf import settings
from django.db import migrations, transaction

SAMPLES = [
    ('Serenity Beach Villa', 'Diani Beach', 'Kenya'), ('Safari Edge Camp', 'Masai Mara', 'Kenya'),
    ('Stone Town Heritage Suite', 'Zanzibar', 'Tanzania'), ('Karen Luxury Loft', 'Nairobi', 'Kenya'),
    ('Nyali Beach Mansion', 'Mombasa', 'Kenya'), ('Mount Meru View Lodge', 'Arusha', 'Tanzania'),
    ('Kigali Heights Apartment', 'Kigali', 'Rwanda'), ('Lake Victoria Resort', 'Kampala', 'Uganda'),
    ('Lake Naivasha Eco Cabin', 'Naivasha', 'Kenya'), ('Amboseli Safari Lodge', 'Amboseli', 'Kenya'),
    ('Zanzibar Beach Bungalow', 'Zanzibar', 'Tanzania'), ('Ngorongoro Crater View', 'Ngorongoro', 'Tanzania'),
]


def forwards(apps, schema_editor):
    Hotel = apps.get_model('Hotels', 'Hotel')
    Bookings = apps.get_model('ClientRequests', 'Bookings')
    alias = schema_editor.connection.alias
    files = []
    for name, location, country in SAMPLES:
        for hotel in Hotel.objects.filter(name=name, location=location, country=country):
            if Bookings.objects.filter(hotel=hotel).exists():
                Hotel.objects.filter(pk=hotel.pk).update(is_published=False)   # keep the record behind a lead
                continue
            files += [img.image.name for img in hotel.images.all() if img.image]
            hotel.delete()                                                      # photos rows go with it

    media = str(settings.MEDIA_ROOT)

    def remove_files():
        for rel in files:
            path = os.path.normpath(os.path.join(media, rel))
            if path.startswith(media) and os.path.isfile(path):
                os.remove(path)
            stem = os.path.splitext(os.path.basename(rel))[0]
            for thumb in glob.glob(os.path.join(media, 'thumbs', '*', f'{stem}_*.webp')):
                os.remove(thumb)

    if files:
        transaction.on_commit(remove_files, using=alias)


class Migration(migrations.Migration):

    dependencies = [
        ('Hotels', '0005_apikey'),
        ('ClientRequests', '0004_bookings_hotel_alter_bookings_booking_type'),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
