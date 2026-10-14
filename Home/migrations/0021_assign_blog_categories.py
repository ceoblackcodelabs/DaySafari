from django.db import migrations

CATS = [
    # slug, English, fr, sw, es, de, it
    ('safari-itineraries', 'Safari Itineraries', "Itinéraires de safari", "Ratiba za Safari", "Itinerarios de safari", "Safari-Reiserouten", "Itinerari safari"),
    ('planning-tips', 'Planning & Tips', "Préparation et conseils", "Mipango na Vidokezo", "Planificación y consejos", "Planung & Tipps", "Pianificazione e consigli"),
    ('wildlife-conservation', 'Wildlife & Conservation', "Faune et conservation", "Wanyamapori na Uhifadhi", "Fauna y conservación", "Tierwelt & Naturschutz", "Fauna e conservazione"),
    ('culture-lifestyle', 'Culture & Lifestyle', "Culture et mode de vie", "Utamaduni na Maisha", "Cultura y estilo de vida", "Kultur & Lebensstil", "Cultura e stile di vita"),
]
# title keyword -> category slug (first match wins); posts that match nothing stay uncategorised
RULES = [
    ('itinerary', 'safari-itineraries'), ('safari packages', 'safari-itineraries'), ('safari from nairobi', 'safari-itineraries'),
    ('conservation', 'wildlife-conservation'), ('migration', 'wildlife-conservation'), ('photography', 'wildlife-conservation'),
    ('cultur', 'culture-lifestyle'), ('call home', 'culture-lifestyle'),
    ('best time', 'planning-tips'), ('packing', 'planning-tips'), ('tips', 'planning-tips'), ('guide', 'planning-tips'),
]


def forwards(apps, schema_editor):
    Cat = apps.get_model('Home', 'BlogCategory')
    Blogs = apps.get_model('Home', 'Blogs')
    made = {}
    for order, (slug, en, fr, sw, es, de, it) in enumerate(CATS):
        made[slug], _ = Cat.objects.get_or_create(slug=slug, defaults=dict(
            name=en, name_en=en, name_fr=fr, name_sw=sw, name_es=es, name_de=de, name_it=it, order=order))
    for post in Blogs.objects.filter(category__isnull=True):
        title = (post.title or '').lower()
        for word, slug in RULES:
            if word in title:
                post.category = made[slug]
                post.save(update_fields=['category'])
                break


class Migration(migrations.Migration):
    dependencies = [('Home', '0020_blog_categories')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
