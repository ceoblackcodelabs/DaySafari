"""One-off: turn the old Accomodations rows into Hotels, then remove the old tables and photos.

* Hotel rows (name, description, price, guests, contacts...) are copied as they are.
* The old "photos" were generated gradient placeholders; they are deleted and each hotel gets one real
  photo from the site's own media where a matching place exists (hotels without a match show a neutral
  placeholder until real photos are uploaded in the admin).
* Airbnb tables are NOT touched.
Safe on any database: if the old tables are absent (fresh install) it does nothing.
"""
import os
import re
import shutil

from django.conf import settings
from django.db import migrations, transaction
from django.utils.text import slugify

OLD_TABLES = ['Accomodations_accomodationsimage', 'Accomodations_accomodations_meal_plan',
              'Accomodations_mealplan', 'Accomodations_accomodations']

# existing real photos in the site's media, matched to each hotel's place
PHOTO_FOR = {
    'Serenity Beach Villa': 'destinations/diani.jpg',
    'Safari Edge Camp': 'destinations/Maasai.jpg',
    'Stone Town Heritage Suite': 'destinations/stone.jpg',
    'Nyali Beach Mansion': 'destinations/watamu.jpg',
    'Mount Meru View Lodge': 'awesome_packages/MERU.jpg',
    'Lake Victoria Resort': 'destinations/victoria.jpg',
    'Lake Naivasha Eco Cabin': 'destinations/nakuru.jpg',
    'Amboseli Safari Lodge': 'destinations/amboseli.jpg',
    'Zanzibar Beach Bungalow': 'destinations/zanzibar.jpg',
    'Ngorongoro Crater View': 'destinations/ngoro.jpg',
}


def property_type(name):
    n = name.lower()
    for key, kind in (('lodge', 'lodge'), ('camp', 'camp'), ('resort', 'resort'), ('villa', 'villa'),
                      ('mansion', 'villa'), ('bungalow', 'villa'), ('apartment', 'apartment'), ('loft', 'apartment'),
                      ('suite', 'apartment'), ('cabin', 'cabin')):
        if key in n:
            return kind
    return 'hotel'


def first_sentence(text, limit=200):
    text = (text or '').strip()
    if not text:
        return ''
    sentence = re.split(r'(?<=[.!?])\s', text, maxsplit=1)[0]
    return sentence if len(sentence) <= limit else sentence[:limit].rsplit(' ', 1)[0] + '…'


def copy_photo(source_rel, slug):
    src = os.path.join(settings.MEDIA_ROOT, source_rel)
    if not os.path.isfile(src):
        return None
    try:
        from PIL import Image
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'hotels'), exist_ok=True)
        rel = f'hotels/{slug}.jpg'
        with Image.open(src) as im:
            im = im.convert('RGB')
            if im.width > 1600:
                im = im.resize((1600, round(im.height * 1600 / im.width)))
            im.save(os.path.join(settings.MEDIA_ROOT, rel), 'JPEG', quality=80, optimize=True, progressive=True)
        return rel
    except Exception:
        return None


def forwards(apps, schema_editor):
    connection = schema_editor.connection
    if 'Accomodations_accomodations' not in connection.introspection.table_names():
        return
    Hotel = apps.get_model('Hotels', 'Hotel')
    HotelImage = apps.get_model('Hotels', 'HotelImage')
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM "Accomodations_accomodations" ORDER BY id')
        columns = [c[0] for c in cursor.description]
        rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
        old_files = []
        if 'Accomodations_accomodationsimage' in connection.introspection.table_names():
            cursor.execute('SELECT image FROM "Accomodations_accomodationsimage"')
            old_files = [r[0] for r in cursor.fetchall() if r[0]]

    for row in rows:
        if Hotel.objects.filter(name=row['name']).exists():
            continue
        place = (row.get('location') or '').strip()
        area, _, country = place.rpartition(',')
        area, country = (area.strip() or place), (country.strip() or 'Kenya')
        slug, n = slugify(f"{row['name']}-{area}") or 'hotel', 2
        base = slug
        while Hotel.objects.filter(slug=slug).exists():
            slug, n = f'{base}-{n}', n + 1
        try:
            stars = int(row.get('rating') or 4)
        except (TypeError, ValueError):
            stars = 4
        hotel = Hotel.objects.create(
            name=row['name'], slug=slug, country=country, location=area,
            property_type=property_type(row['name']), star_rating=min(max(stars, 1), 5),
            rooms=row.get('specification') or '', summary=first_sentence(row.get('description')),
            description=row.get('description') or '', price_per_night=row.get('price_per_night'),
            max_guests=row.get('max_guests') or 2, child_policy=row.get('child_policy') or '',
            contact_person=row.get('contact_person') or '', email=row.get('email') or '',
            phone_number=row.get('phone_number') or '', contract_validity=row.get('contract_validity'),
            remarks=row.get('remarks') or '',
        )
        if row.get('created_at'):
            Hotel.objects.filter(pk=hotel.pk).update(created_at=row['created_at'])
        photo = copy_photo(PHOTO_FOR[row['name']], slug) if row['name'] in PHOTO_FOR else None
        if photo:
            HotelImage.objects.create(hotel=hotel, image=photo, caption=row['name'], is_featured=True, order=0)

    # Orphan link tables left by the removed SuperMode app still point at the old placeholder photos.
    existing = connection.introspection.table_names()
    if 'SuperMode_itinerarybuilder_hotel_images' in existing:
        schema_editor.execute('DELETE FROM "SuperMode_itinerarybuilder_hotel_images"')

    # remove the old tables ...
    for table in OLD_TABLES:
        schema_editor.execute(f'DROP TABLE IF EXISTS "{table}"')

    # ... and, only AFTER the database change has committed successfully, their placeholder photos
    media = str(settings.MEDIA_ROOT)

    def remove_files():
        for rel in old_files:
            path = os.path.normpath(os.path.join(media, rel))
            if path.startswith(media) and os.path.isfile(path):
                os.remove(path)
        shutil.rmtree(os.path.join(media, 'Accomodations'), ignore_errors=True)

    transaction.on_commit(remove_files, using=connection.alias)


class Migration(migrations.Migration):

    dependencies = [('Hotels', '0002_hotel_hotelimage')]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
