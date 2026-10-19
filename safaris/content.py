"""Site content. The original pages/trips live in data/content.json; the cruise, service and hotel
sections are defined below."""
import json
from pathlib import Path
from urllib.parse import quote

DATA = Path(__file__).resolve().parent / 'data'
WHATSAPP = '254759379600'
EMAIL = 'info@daysafarisadventures.co.ke'
GOOGLE_REVIEWS_URL = 'https://maps.app.goo.gl/tian1a39WNTSTz3U8'

_raw = json.loads((DATA / 'content.json').read_text(encoding='utf-8'))
CREDITS = json.loads((DATA / 'photo_credits.json').read_text(encoding='utf-8'))

DESTINATIONS = {}
for _key, _d in _raw['destinations'].items():
    DESTINATIONS[_key] = {**_d, 'key': _key, 'group': 'safari', 'menu': True,
                          'short': {'kenya': 'Kenya', 'tanzania': 'Tanzania', 'uganda': 'Uganda', 'mara': 'Masai Mara',
                                    'kilimanjaro': 'Kilimanjaro', 'beach': 'Safari & beach'}[_key]}

_HELP = 'Help me choose'
_extra = {
    'cruises': ('Cruises', '/cruises', 'cruise', [
        {'key': 'cruise_type', 'label': 'What kind of cruise?', 'options': [_HELP, 'Sunset dhow cruise', 'Snorkelling & dolphin day trip', 'Lake boat ride', 'Private charter']},
        {'key': 'cruise_party', 'label': 'Who is travelling?', 'options': ['Couple', 'Family with children', 'Friends or a group', 'Special occasion']}]),
    'cruise_zanzibar': ('Zanzibar dhow cruise', '/zanzibar-dhow-cruises', 'cruise', [
        {'key': 'zanzibar_cruise', 'label': 'Which experience?', 'options': [_HELP, 'Sunset dhow cruise', 'Snorkelling & sandbank day trip', 'Private charter']},
        {'key': 'cruise_party', 'label': 'Who is travelling?', 'options': ['Couple', 'Family with children', 'Friends or a group', 'Special occasion']}]),
    'cruise_diani': ('Diani dhow cruise', '/diani-dhow-cruises', 'cruise', [
        {'key': 'diani_cruise', 'label': 'Which experience?', 'options': [_HELP, 'Dhow cruise & snorkelling', 'Dolphin-spotting trip', 'Sunset cruise']},
        {'key': 'cruise_party', 'label': 'Who is travelling?', 'options': ['Couple', 'Family with children', 'Friends or a group', 'Special occasion']}]),
    'cruise_naivasha': ('Lake Naivasha boat ride', '/lake-naivasha-boat-cruises', 'cruise', [
        {'key': 'naivasha_cruise', 'label': 'Which experience?', 'options': [_HELP, 'Boat ride & birdlife', 'Crescent Island walk', 'Add to a Kenya safari']},
        {'key': 'cruise_party', 'label': 'Who is travelling?', 'options': ['Couple', 'Family with children', 'Friends or a group', 'Special occasion']}]),
    'services': ('Travel services', '/services', 'service', [
        {'key': 'service_needed', 'label': 'What do you need help with?', 'options': [_HELP, 'Airport & city transfers', 'Vehicle hire with driver-guide', 'Visa & travel-document guidance', 'Tailor-made itinerary', 'Group or corporate travel']},
        {'key': 'service_timing', 'label': 'How soon do you need it?', 'options': ['Within a month', 'In 1–3 months', 'Just researching']}]),
    'hotels': ('Hotels & stays', '/hotels', 'hotel', [
        {'key': 'stay_type', 'label': 'What kind of stay?', 'options': [_HELP, 'Safari lodge or tented camp', 'Zanzibar beach hotel', 'Diani beach resort', 'Nairobi city hotel']},
        {'key': 'comfort', 'label': 'Your stay preference', 'options': [_HELP, 'Comfortable mid-range', 'Luxury', 'Budget-conscious']}]),
}
for _key, (_label, _path, _group, _qs) in _extra.items():
    DESTINATIONS[_key] = {'key': _key, 'label': _label, 'path': _path, 'group': _group, 'menu': False, 'questions': _qs, 'short': _label}

CRUISE_MENU = [DESTINATIONS[k] for k in ('cruise_zanzibar', 'cruise_diani', 'cruise_naivasha')]

_shared = [
    {'q': 'Does sending an enquiry confirm my booking?', 'a': 'No. An enquiry starts the planning conversation. Your trip is confirmed only after a written confirmation and the payment required in that confirmation.'},
    {'q': 'What will my quotation include?', 'a': 'Your quote will set out the itinerary, accommodation, transport, included activities, exclusions, price, payment schedule and applicable cancellation conditions.'},
    {'q': 'Can I travel with flexible dates?', 'a': 'Yes. Select “Still deciding” in the form. Tell us your preferred season or approximate month and we can discuss suitable options.'},
]


def _page(slug, destination, title, eyebrow, headline, accent, intro, image, alt, facts, description, story_title, story, highlights, faqs, catalog=None):
    return {'slug': slug, 'destination': destination, 'title': title, 'eyebrow': eyebrow, 'headline': headline, 'accent': accent,
            'intro': intro, 'image': image, 'alt': alt, 'facts': facts, 'description': description, 'storyTitle': story_title,
            'story': story, 'highlights': highlights, 'faqs': faqs + _shared, 'catalog': catalog}


_cruise_party_faq = {'q': 'Are cruise prices and times fixed?', 'a': 'No. Operators, tides, weather and group size affect timings and cost. Your written quotation sets out the timing, inclusions, exclusions and price for your dates.'}

NEW_PAGES = [
    _page('cruises', 'cruises', 'Cruises in East Africa: Dhow, Lake & Ocean | Day Safaris Adventures', 'Kenya • Zanzibar • Indian Ocean',
          'Slow days', 'on the water.', 'Add a dhow cruise, a snorkelling day or a lake boat ride to your safari, or plan a coastal escape built around the water.',
          'zanzibar', 'The Indian Ocean coastline of Zanzibar, Tanzania', ['Dhow & lake cruises', 'Zanzibar, Diani & Naivasha', 'Private or shared enquiries'],
          'Plan dhow cruises in Zanzibar and Diani or a Lake Naivasha boat ride with Day Safaris Adventures. Request a quote for your dates and group.',
          'A change of pace, on the water.', 'After the game drives, the coast and the lakes offer a gentler rhythm. Tell us when you travel and who is with you, and we will discuss suitable cruise options and how to fit them around the rest of your trip.',
          [{'title': 'Zanzibar dhow cruises', 'text': 'Sunset sails and snorkelling days on the Indian Ocean.', 'image': 'zanzibar'},
           {'title': 'Diani dhow cruises', 'text': 'Dhow trips and snorkelling from Kenya’s south coast.', 'image': 'diani'},
           {'title': 'Lake Naivasha', 'text': 'A boat ride among birdlife, easy to add to a Kenya safari.', 'image': 'nakuru'}],
          [_cruise_party_faq], catalog='cruise'),
    _page('zanzibar-dhow-cruises', 'cruise_zanzibar', 'Zanzibar Dhow Cruises & Snorkelling Trips | Day Safaris Adventures', 'Zanzibar • Indian Ocean',
          'Sail the', 'Zanzibar coast.', 'Plan a traditional dhow cruise at sunset, or a day of snorkelling and swimming, as part of a beach stay or a Tanzania safari.',
          'zanzibar', 'The Indian Ocean coastline of Zanzibar, Tanzania', ['Sunset & day cruises', 'Pair with a safari', 'Couples, families & groups'],
          'Request a quote for a Zanzibar dhow cruise or snorkelling day trip with Day Safaris Adventures.',
          'Let the tide set the pace.', 'Tell us your dates and who is travelling. We will discuss the cruise style, timing and what is included, and write it all down in your quotation.',
          [{'title': 'Sunset on a dhow', 'text': 'A relaxed evening sail along the coast.', 'image': 'zanzibar'},
           {'title': 'Snorkelling days', 'text': 'Time in the water, with the details confirmed in your quote.'},
           {'title': 'After the safari', 'text': 'Combine with Serengeti or Ngorongoro for wild days and ocean endings.', 'image': 'ngorongoro'}],
          [{'q': 'Can I combine a cruise with a safari?', 'a': 'Yes. Many travellers finish a Tanzania safari in Zanzibar. We will discuss routing and any flights, which are included only if your quotation says so.'}, _cruise_party_faq], catalog='cruise'),
    _page('diani-dhow-cruises', 'cruise_diani', 'Diani Dhow Cruises & Snorkelling | Day Safaris Adventures', 'Kenya • Diani coast',
          'Out on', 'the blue.', 'Plan a dhow cruise, dolphin-spotting trip or snorkelling day from Diani, on Kenya’s south coast.',
          'diani', 'The white-sand coast at Diani, Kenya', ['Dhow & snorkelling trips', 'Add to a Kenya safari', 'Family-friendly options'],
          'Request a quote for a Diani dhow cruise or snorkelling trip with Day Safaris Adventures.',
          'The coast, from the water.', 'Kenya’s coast is a natural ending to a safari. Share your dates and group, and we will discuss the water experiences that suit you.',
          [{'title': 'Dhow cruise', 'text': 'A traditional sailing boat and a slower day at sea.', 'image': 'diani'},
           {'title': 'Snorkelling', 'text': 'Time in the reefs, with conditions and inclusions confirmed in writing.'},
           {'title': 'Safari first', 'text': 'Start in the Mara or Amboseli, then head to the coast.', 'image': 'amboseli'}],
          [_cruise_party_faq], catalog='cruise'),
    _page('lake-naivasha-boat-cruises', 'cruise_naivasha', 'Lake Naivasha Boat Rides | Day Safaris Adventures', 'Kenya • Rift Valley',
          'Birdlife', 'by boat.', 'A gentle boat ride on Lake Naivasha is an easy addition to a Kenya safari from Nairobi.',
          'nakuru', 'Rift Valley lake landscape in Kenya', ['Easy from Nairobi', 'Birdlife & scenery', 'Add to any Kenya route'],
          'Request a quote for a Lake Naivasha boat ride as part of a Kenya safari from Nairobi.',
          'A quiet morning on the lake.', 'Naivasha fits neatly between Nairobi and the Mara. Tell us your route and we will discuss how a boat ride and a lakeside stop can work in your itinerary.',
          [{'title': 'On the water', 'text': 'A boat ride with views of the lake and its birdlife.', 'image': 'nakuru'},
           {'title': 'On the way', 'text': 'A natural stop between Nairobi and the Masai Mara.', 'image': 'mara'},
           {'title': 'Plan the whole route', 'text': 'Transfers and timings are set out in your quotation.'}],
          [_cruise_party_faq], catalog='cruise'),
    _page('services', 'services', 'Travel Services in Nairobi: Transfers, Vehicles & Planning | Day Safaris Adventures', 'Nairobi • East Africa',
          'Everything around', 'the journey.', 'Airport transfers, vehicles with driver-guides, itinerary planning and travel support from a local team in Nairobi.',
          'team', 'The Day Safaris Adventures team at a travel event', ['Local Nairobi team', 'Transfers & vehicles', 'Planning & guidance'],
          'Day Safaris Adventures services in Nairobi: airport transfers, vehicle hire with driver-guide, tailor-made itineraries, group travel and travel guidance.',
          'The practical details, handled.', 'Beyond the safari itself, a good trip depends on the details. Tell us what you need and we will set out what we can arrange, and what is excluded, in writing.',
          [{'title': 'Airport & city transfers', 'text': 'Meet-and-greet and transfers planned around your arrival details.'},
           {'title': 'Vehicles with driver-guides', 'text': 'Safari vehicles with an experienced local driver-guide.'},
           {'title': 'Tailor-made itineraries', 'text': 'A route built around your dates, interests and budget.'},
           {'title': 'Travel guidance', 'text': 'Practical guidance on documents, seasons and what to pack. Visa rules depend on your nationality; always confirm with official sources.'},
           {'title': 'Group & corporate travel', 'text': 'Family reunions, incentive trips and group departures.'},
           {'title': 'Stays & activities', 'text': 'Accommodation and optional activities such as cruises, set out in your quote.'}],
          [{'q': 'Do you handle visas?', 'a': 'We can share general guidance, but entry rules depend on your nationality and change. Please confirm requirements with the official immigration authority.'}]),
    _page('hotels', 'hotels', 'Hotels, Lodges & Beach Stays in East Africa | Day Safaris Adventures', 'Safari lodges • Beach hotels • Nairobi',
          'Wake up', 'somewhere special.', 'From safari lodges and tented camps to beach hotels in Zanzibar and Diani, tell us your style and we will suggest where to stay.',
          'mara', 'Wildebeest and zebra in the Masai Mara, Kenya', ['Lodges, camps & hotels', 'Mid-range to luxury', 'Matched to your route'],
          'Find hotels, safari lodges and beach stays in Kenya, Tanzania and Zanzibar. Request suggestions for your dates and budget with Day Safaris Adventures.',
          'Where you stay shapes the trip.', 'Location, comfort and budget all matter. Share your route and preferences and we will suggest suitable stays; availability and rates are confirmed in your written quotation.',
          [{'title': 'Safari lodges & camps', 'text': 'Stay close to the wildlife in the Mara, Amboseli or Serengeti.', 'image': 'mara'},
           {'title': 'Beach hotels', 'text': 'Zanzibar and Diani stays for the end of your journey.', 'image': 'zanzibar'},
           {'title': 'Nairobi stays', 'text': 'A comfortable base before or after your safari.'}],
          [{'q': 'Are hotel rates shown on the website?', 'a': 'No. Rates change with season and availability. We confirm current options and prices in your written quotation.'}], catalog='hotel'),
]

PAGES = _raw['pages'] + NEW_PAGES
for _p in PAGES:
    _p.setdefault('catalog', None)
    _p.setdefault('destination', None)
PAGE_BY_SLUG = {p['slug']: p for p in PAGES}
# These slugs are served by the main site (Home app) with their own database-driven pages; the entries above are
# still used as form topics and for the enquiry form's per-page questions.
SITE_OWNED_SLUGS = {'', 'about', 'contact', 'services', 'cruises', 'hotels'}
LANDING_PAGES = [p for p in PAGES if p['slug'] not in SITE_OWNED_SLUGS]

# Trips and add-on offers. `kind` decides which section shows them; `also` lists extra destinations they appear under.
OFFERS = [{**t, 'kind': 'trip', 'also': []} for t in _raw['trips']]
for _t in OFFERS:
    _t.setdefault('price', None)
OFFERS += [
    {'id': 'zanzibar-dhow', 'name': 'Zanzibar Dhow Cruise', 'region': 'Zanzibar', 'destination': 'cruise_zanzibar', 'days': 'Half or full day', 'price': None, 'image': 'zanzibar', 'summary': 'A sunset sail or snorkelling day on the Indian Ocean.', 'tag': 'On the water', 'kind': 'cruise', 'also': ['cruises']},
    {'id': 'diani-dhow', 'name': 'Diani Dhow & Snorkelling', 'region': 'Kenya coast', 'destination': 'cruise_diani', 'days': 'Day trip', 'price': None, 'image': 'diani', 'summary': 'A dhow cruise and reef time from Kenya’s south coast.', 'tag': 'Coast & reef', 'kind': 'cruise', 'also': ['cruises']},
    {'id': 'naivasha-boat', 'name': 'Lake Naivasha Boat Ride', 'region': 'Kenya', 'destination': 'cruise_naivasha', 'days': 'Half day', 'price': None, 'image': 'nakuru', 'summary': 'Birdlife and lake scenery, easy to add to a Kenya safari.', 'tag': 'Rift Valley', 'kind': 'cruise', 'also': ['cruises']},
    {'id': 'hotel-safari-lodge', 'name': 'Safari Lodges & Tented Camps', 'region': 'Kenya & Tanzania', 'destination': 'hotels', 'days': 'Per your route', 'price': None, 'image': 'amboseli', 'summary': 'Stays near the wildlife in the Mara, Amboseli and the Serengeti.', 'tag': 'In the wild', 'kind': 'hotel', 'also': []},
    {'id': 'hotel-zanzibar', 'name': 'Zanzibar Beach Hotels', 'region': 'Zanzibar', 'destination': 'hotels', 'days': 'Per your dates', 'price': None, 'image': 'zanzibar_island', 'summary': 'Island stays for the end of your safari.', 'tag': 'By the sea', 'kind': 'hotel', 'also': []},
    {'id': 'hotel-diani', 'name': 'Diani Beach Resorts', 'region': 'Kenya coast', 'destination': 'hotels', 'days': 'Per your dates', 'price': None, 'image': 'diani', 'summary': 'White-sand resort stays on Kenya’s south coast.', 'tag': 'Beach escape', 'kind': 'hotel', 'also': []},
]
OFFER_BY_ID = {o['id']: o for o in OFFERS}
_ALSO_TRIPS = {'kenya': ['mara'], 'tanzania': ['beach']}


def offers_for(page):
    """Cards shown on a page (server-rendered; the /safaris filter bar works client-side)."""
    cat, dest = page['catalog'], page['destination']
    if cat:
        return [o for o in OFFERS if o['kind'] == cat and (dest in (None, o['destination']) or dest in o['also'] or dest in ('cruises', 'hotels'))]
    trips = [o for o in OFFERS if o['kind'] == 'trip']
    if page['slug'] == 'safaris':
        return trips
    if dest:
        allowed = {dest, *_ALSO_TRIPS.get(dest, [])}
        return [o for o in trips if o['destination'] in allowed]
    return trips[:4]


def offer_path(o):
    return f"{DESTINATIONS[o['destination']]['path']}?trip={o['id']}"


def whatsapp_url(origin, page=None):
    d = DESTINATIONS.get(page['destination']) if page and page.get('destination') else None
    topic = d['label'] if d else 'an East Africa trip'
    slug = page['slug'] if page else ''
    text = f'Hello Day Safaris Adventures, I would like to plan {topic}. I am enquiring from {origin}/{slug}.'
    return f'https://wa.me/{WHATSAPP}?text={quote(text, safe="")}'
