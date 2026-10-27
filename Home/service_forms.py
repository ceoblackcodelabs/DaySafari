"""Quote-form wording and questions for each service page. The popup shows the set that matches the page the visitor is on."""

_PARTY = ['Couple', 'Family with children', 'Friends or a group', 'Solo traveller', 'Special occasion']

FORMS = {
    'airport_transfers': {
        'service': 'Airport transfer', 'eyebrow': 'Airport transfers', 'title': 'Book your airport transfer',
        'intro': 'Tell us where and when you land, and we will arrange your pick-up and send a clear quote.',
        'submit': 'Request my transfer', 'when_label': 'Travel month', 'people_label': 'Passengers',
        'questions': [
            {'key': 'airport', 'label': 'Which airport?', 'options': ['Jomo Kenyatta (JKIA), Nairobi', 'Wilson Airport, Nairobi', 'Moi International, Mombasa', 'Kisumu', 'Other or not sure']},
            {'key': 'transfer', 'label': 'What do you need?', 'options': ['Arrival pick-up', 'Departure drop-off', 'Both ways', 'Shuttle to a hotel or park']},
            {'key': 'vehicle', 'label': 'Vehicle', 'options': ['Private car', 'Shared shuttle', 'Minivan for a group', 'Help me choose'], 'more': True}],
        'notes': 'Flight number, arrival time, where you are going…'},
    'travel_partnerships': {
        'service': 'Travel partnership', 'eyebrow': 'Travel partners', 'title': 'Become a travel partner',
        'intro': 'Tell us about your business and we will share how we can support your clients on the ground.',
        'submit': 'Send my partnership request', 'when_label': 'Start date', 'people_label': 'Groups per year', 'show_people': False,
        'questions': [
            {'key': 'business', 'label': 'What best describes you?', 'options': ['Travel agent', 'Tour operator', 'Hotel or lodge', 'Corporate or events', 'Other']},
            {'key': 'need', 'label': 'What do you need from us?', 'options': ['Ground handling (DMC)', 'Itineraries and rates', 'Group and incentive trips', 'Hotel and transport booking', 'Other']}],
        'notes': 'Your company, markets and the kind of clients you send…'},
    'holiday_tailor_made_tours': {
        'service': 'Tailor-made holiday', 'eyebrow': 'Tailor-made holidays', 'title': 'Design my tailor-made holiday',
        'intro': 'A few details and our consultants will shape a trip around you.',
        'submit': 'Plan my holiday',
        'questions': [
            {'key': 'party', 'label': 'Who is travelling?', 'options': _PARTY},
            {'key': 'where', 'label': 'Where would you like to go?', 'options': ['Kenya', 'Tanzania', 'Uganda or Rwanda', 'South Africa', 'Safari and beach', 'Not sure yet']},
            {'key': 'style', 'label': 'Travel style', 'options': ['Comfortable', 'Luxury', 'Budget-friendly', 'Adventurous'], 'more': True}],
        'notes': 'Must-see places, special occasions, dietary needs…'},
    'african_wildlife_tours': {
        'service': 'Wildlife safari', 'eyebrow': 'African wildlife safaris', 'title': 'Plan my wildlife safari',
        'intro': 'Tell us what you want to see and we will suggest parks, lodges and dates.',
        'submit': 'Plan my safari',
        'questions': [
            {'key': 'experience', 'label': 'What would you love to see?', 'options': ['Big Five game drives', 'The Great Migration', 'Gorilla or chimpanzee trekking', 'Birds and photography', 'Help me choose']},
            {'key': 'length', 'label': 'How long?', 'options': ['1 to 3 days', '4 to 6 days', '7 to 10 days', 'More than 10 days']},
            {'key': 'party', 'label': 'Who is travelling?', 'options': _PARTY, 'more': True}],
        'notes': 'Parks you have in mind, photography needs, mobility…'},
    'airline': {
        'service': 'Flight tickets', 'eyebrow': 'Airline tickets', 'title': 'Find me a flight',
        'intro': 'Share your route and we will search domestic and international fares for you.',
        'submit': 'Request my fares', 'when_label': 'Travel month', 'people_label': 'Passengers',
        'questions': [
            {'key': 'route', 'label': 'Where are you flying?', 'type': 'text', 'placeholder': 'e.g. Nairobi to Dubai'},
            {'key': 'trip', 'label': 'Trip type', 'options': ['Return', 'One way', 'Multi-city']},
            {'key': 'cabin', 'label': 'Cabin', 'options': ['Economy', 'Premium economy', 'Business', 'First'], 'more': True}],
        'notes': 'Preferred dates, airlines, baggage needs…'},
    'cruises': {
        'service': 'Cruise', 'eyebrow': 'Cruises', 'title': 'Plan my cruise',
        'intro': 'From Indian Ocean voyages to Nile and dhow cruises, tell us what suits you.',
        'submit': 'Request my cruise quote',
        'questions': [
            {'key': 'kind', 'label': 'What kind of cruise?', 'options': ['Ocean cruise', 'Nile river cruise', 'Mediterranean or Europe', 'Dhow cruise (Zanzibar or Diani)', 'Help me choose']},
            {'key': 'party', 'label': 'Who is travelling?', 'options': _PARTY}],
        'notes': 'Ports you like, cabin type, special occasions…'},
    'hotels': {
        'service': 'Hotel stay', 'eyebrow': 'Hotels and lodges', 'title': 'Find me a place to stay',
        'intro': 'Tell us where and what kind of stay, and we will recommend and book it.',
        'submit': 'Find my stay', 'when_label': 'Check-in month', 'people_label': 'Guests',
        'questions': [
            {'key': 'where', 'label': 'Where?', 'type': 'text', 'placeholder': 'City, park or beach'},
            {'key': 'type', 'label': 'Type of stay', 'options': ['Safari lodge', 'Beach resort', 'City hotel', 'Tented camp', 'Anything suitable']},
            {'key': 'nights', 'label': 'Nights', 'options': ['1 to 2', '3 to 5', '6 to 9', '10 or more'], 'more': True}],
        'notes': 'Room type, meals, accessibility, a favourite hotel…'},
    'services': {
        'service': 'Travel service', 'eyebrow': 'Our services', 'title': 'How can we help?',
        'intro': 'Pick the service you need and a consultant will come back to you.',
        'submit': 'Send my request',
        'questions': [
            {'key': 'service', 'label': 'Which service?', 'options': ['Wildlife safaris', 'Airport transfers and shuttles', 'Tailor-made tours', 'Hotel accommodation', 'Travel partnership', 'Visa processing', 'Flights', 'Something else']}],
        'notes': 'Tell us a little more…'},
}

DEFAULT = {
    'service': '', 'eyebrow': 'Free quote · reply in minutes', 'title': "Hello! What's your next adventure?",
    'intro': 'Tell us where you dream of going and our team will contact you with a free, no-obligation quote.',
    'submit': 'Submit',
    'questions': [
        {'key': 'interest', 'label': 'What would you love to experience?', 'options': ['Safari', 'Mountain trekking', 'Beach holiday', 'Hotels and lodges', 'Cruise', 'Flights', 'Airport transfer', 'Tailor-made trip', 'Help me choose']}],
    'notes': 'Anything else we should know…',
}

SERVICE_PAGES = set(FORMS)


def config_for(url_name):
    cfg = dict(FORMS.get(url_name) or DEFAULT)
    cfg['key'] = url_name if url_name in FORMS else 'default'
    cfg.setdefault('when_label', 'When would you travel?')
    cfg.setdefault('people_label', 'Travellers')
    cfg.setdefault('show_people', True)
    cfg['visible_q'] = [q for q in cfg['questions'] if not q.get('more')]
    cfg['more_q'] = [q for q in cfg['questions'] if q.get('more')]
    return cfg


def config_by_key(key):
    return config_for(key if key in FORMS else '')
