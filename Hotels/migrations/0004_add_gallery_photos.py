"""Give hotels a small photo gallery, using real photos already in the site's media.

Each hotel imported from the old app had a single photo, so the gallery strip on the hotel page would
have been empty. This adds 1-3 matching photos (same place or nearby landmarks) to hotels that have
fewer than two. Safe to re-run: hotels that already have a gallery, and files that don't exist, are skipped.
Hotels without a suitable match keep their single photo; add more in the admin any time.
"""
import os

from django.conf import settings
from django.db import migrations

EXTRA_PHOTOS = {
    'Amboseli Safari Lodge': ['destinations/kilimanjaro.jpg'],
    'Safari Edge Camp': ['destinations/Maasai_0kY8WC4.jpg', 'destinations/Maasai_8aXJLhf.jpg'],
    'Serenity Beach Villa': ['destinations/watamu.jpg'],
    'Nyali Beach Mansion': ['destinations/fort.jpg', 'destinations/diani.jpg'],
    'Stone Town Heritage Suite': ['destinations/zanzibar.jpg'],
    'Zanzibar Beach Bungalow': ['destinations/mafia.jpg', 'destinations/stone.jpg'],
    'Ngorongoro Crater View': ['destinations/serengeti.jpg.jpg', 'destinations/olduvai.jpg'],
    'Mount Meru View Lodge': ['awesome_packages/MERU_2.jpg', 'awesome_packages/MERU_3.jpg', 'awesome_packages/MERU_4.jpg'],
}


def copy_photo(source_rel, dest_rel):
    src = os.path.join(settings.MEDIA_ROOT, source_rel)
    if not os.path.isfile(src):
        return None
    try:
        from PIL import Image
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'hotels'), exist_ok=True)
        with Image.open(src) as im:
            im = im.convert('RGB')
            if im.width > 1600:
                im = im.resize((1600, round(im.height * 1600 / im.width)))
            im.save(os.path.join(settings.MEDIA_ROOT, dest_rel), 'JPEG', quality=80, optimize=True, progressive=True)
        return dest_rel
    except Exception:
        return None


def forwards(apps, schema_editor):
    Hotel = apps.get_model('Hotels', 'Hotel')
    HotelImage = apps.get_model('Hotels', 'HotelImage')
    for hotel in Hotel.objects.filter(name__in=EXTRA_PHOTOS):
        if HotelImage.objects.filter(hotel=hotel).count() >= 2:
            continue
        n = HotelImage.objects.filter(hotel=hotel).count()
        for source in EXTRA_PHOTOS[hotel.name]:
            n += 1
            rel = copy_photo(source, f'hotels/{hotel.slug}-{n}.jpg')
            if rel:
                HotelImage.objects.create(hotel=hotel, image=rel, caption=f'{hotel.name} - photo {n}', order=n)
            else:
                n -= 1


class Migration(migrations.Migration):

    dependencies = [('Hotels', '0003_import_old_accommodations')]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
