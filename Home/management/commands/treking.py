from django.core.management.base import BaseCommand
from django.core.management import call_command
from Home.models import Trekking, ItineraryTreking
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed trekking packages and itineraries with detailed day-by-day descriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-only',
            action='store_true',
            help='Only clear existing trekking data without seeding new data',
        )
        parser.add_argument(
            '--keep-existing',
            action='store_true',
            help='Keep existing data and append new packages (avoid duplicates)',
        )

    def handle(self, *args, **options):
        if options['clear_only']:
            self.clear_existing_data()
            return

        if options['keep_existing']:
            self.stdout.write(self.style.WARNING("Appending data without clearing existing..."))
            self.seed_trekking_packages(clear_existing=False)
        else:
            self.seed_trekking_packages(clear_existing=True)

    def clear_existing_data(self):
        """Clear all existing trekking and itinerary data"""
        itinerary_count = ItineraryTreking.objects.count()
        trekking_count = Trekking.objects.count()

        ItineraryTreking.objects.all().delete()
        Trekking.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f"Cleared existing data: {trekking_count} packages, {itinerary_count} itinerary days"
        ))

    def create_itinerary(self, package, days_data):
        """Helper method to create itineraries for a package"""
        for day in days_data:
            ItineraryTreking.objects.create(
                package=package,
                day_number=day["day"],
                title=day["title"],
                description=day["description"],
                activities=day["activities"],
                accommodation=day["accommodation"],
                meals=day["meals"]
            )

    def seed_trekking_packages(self, clear_existing=True):
        """Main seeding function"""
        if clear_existing:
            self.clear_existing_data()

        self.stdout.write(self.style.SUCCESS("🌄 Seeding trekking packages..."))

        # ==================== KILIMANJARO CATEGORY (3 PACKAGES) ====================

        # Package 1: Machame Route (7 days)
        kilimanjaro1, created = Trekking.objects.get_or_create(
            name="Mount Kilimanjaro Climb - Machame Route (7 Days)",
            defaults={
                "location": "Kilimanjaro National Park, Tanzania",
                "starRating": 5,
                "days": 7,
                "price": Decimal("1850.00"),
                "persons": 8,
                "description": "Experience the ultimate challenge of climbing Mount Kilimanjaro via the scenic Machame Route. Known as the 'Whiskey Route', this 7-day adventure offers breathtaking views and higher acclimatization success rates. You'll traverse stunning landscapes including the Shira Plateau, Barranco Wall, and the majestic glaciers of Uhuru Peak, the highest point in Africa at 5,895 meters.",
                "category": "Kilimanjaro",
                "image": "awesome_packages/kilimanjaro_machame.jpg"
            }
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Machame Gate to Machame Camp", "description": "Your Kilimanjaro adventure begins with a morning drive to Machame Gate (1,640m). Trek through magnificent montane rainforest for 5-6 hours covering 11km to Machame Camp at 2,835m.", "activities": "Rainforest trekking, Wildlife spotting, Photography", "accommodation": "Machame Camp (2,835m) - Mountain tents", "meals": "Full Board"},
                {"day": 2, "title": "Machame Camp to Shira Camp", "description": "Trek out of the rainforest into heath and moorland zones. After 5 hours covering 5km, reach Shira Camp at 3,840m on the Shira Plateau.", "activities": "Moorland trekking, Acclimatization walk", "accommodation": "Shira Camp (3,840m) - Mountain tents", "meals": "Full Board"},
                {"day": 3, "title": "Shira Camp to Barranco Camp via Lava Tower", "description": "Crucial acclimatization day. Trek to Lava Tower at 4,630m before descending to Barranco Camp at 3,960m.", "activities": "Alpine desert trekking, Lava Tower exploration", "accommodation": "Barranco Camp (3,960m)", "meals": "Full Board"},
                {"day": 4, "title": "Barranco Camp to Karanga Camp", "description": "Tackle the famous Barranco Wall, a 300-meter scramble, then traverse to Karanga Camp at 4,035m.", "activities": "Barranco Wall scrambling, Glacier photography", "accommodation": "Karanga Camp (4,035m)", "meals": "Full Board"},
                {"day": 5, "title": "Karanga Camp to Barafu Summit Camp", "description": "Trek to Barafu Camp at 4,640m, the final camp before summit night.", "activities": "High altitude trekking, Summit briefing", "accommodation": "Barafu Camp (4,640m)", "meals": "Full Board"},
                {"day": 6, "title": "Summit Day! Barafu Camp to Uhuru Peak", "description": "Midnight ascent to Uhuru Peak (5,895m) - the Roof of Africa! Descend to Mweka Camp at 3,100m.", "activities": "Summit attempt, Sunrise photography", "accommodation": "Mweka Camp (3,100m)", "meals": "Full Board"},
                {"day": 7, "title": "Mweka Camp to Mweka Gate", "description": "Final descent through rainforest to Mweka Gate. Receive certificate and transfer to hotel.", "activities": "Rainforest descent, Certificate ceremony", "accommodation": "Hotel in Moshi/Arusha", "meals": "Breakfast"},
            ]
            self.create_itinerary(kilimanjaro1, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kilimanjaro1.name}"))

        # Package 2: Lemosho Route (8 days)
        kilimanjaro2, created = Trekking.objects.get_or_create(
            name="Mount Kilimanjaro Climb - Lemosho Route (8 Days)",
            location="Kilimanjaro National Park, Tanzania",
            starRating=5,
            days=8,
            price=Decimal("2100.00"),
            persons=8,
            description="The Lemosho Route is considered the most scenic path to Uhuru Peak. This 8-day trek offers excellent acclimatization and stunning views from the western side of the mountain, with higher success rates due to the longer duration.",
            category="Kilimanjaro",
            image="awesome_packages/kilimanjaro_lemosho.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Londorossi Gate to Mti Mkubwa Camp", "description": "Drive to Londorossi Gate (2,100m). Trek through pristine rainforest to Mti Mkubwa Camp at 2,750m.", "activities": "Forest trekking, Wildlife viewing", "accommodation": "Mti Mkubwa Camp (2,750m)", "meals": "Full Board"},
                {"day": 2, "title": "Mti Mkubwa Camp to Shira 1 Camp", "description": "Trek out of the forest into heathland with views of Kibo. Reach Shira 1 Camp at 3,500m.", "activities": "Heathland trekking, Photography", "accommodation": "Shira 1 Camp (3,500m)", "meals": "Full Board"},
                {"day": 3, "title": "Shira 1 Camp to Shira 2 Camp", "description": "Trek across the Shira Plateau to Shira 2 Camp at 3,850m for acclimatization.", "activities": "Plateau trekking, Acclimatization", "accommodation": "Shira 2 Camp (3,850m)", "meals": "Full Board"},
                {"day": 4, "title": "Shira 2 Camp to Barranco Camp via Lava Tower", "description": "Climb to Lava Tower (4,630m) then descend to Barranco Camp (3,960m).", "activities": "High altitude trekking, Lava Tower", "accommodation": "Barranco Camp (3,960m)", "meals": "Full Board"},
                {"day": 5, "title": "Barranco Camp to Karanga Camp", "description": "Scramble up Barranco Wall and traverse to Karanga Camp at 4,035m.", "activities": "Wall scrambling, Valley views", "accommodation": "Karanga Camp (4,035m)", "meals": "Full Board"},
                {"day": 6, "title": "Karanga Camp to Barafu Camp", "description": "Trek to Barafu Camp at 4,640m for final summit preparation.", "activities": "Summit preparation, Rest", "accommodation": "Barafu Camp (4,640m)", "meals": "Full Board"},
                {"day": 7, "title": "Summit Day! Barafu to Uhuru Peak to Mweka Camp", "description": "Midnight summit attempt to Uhuru Peak (5,895m). Descend to Mweka Camp at 3,100m.", "activities": "Summit success, Celebration", "accommodation": "Mweka Camp (3,100m)", "meals": "Full Board"},
                {"day": 8, "title": "Mweka Camp to Mweka Gate", "description": "Final descent through forest. Receive summit certificates and transfer to hotel.", "activities": "Certificate ceremony, Transfer", "accommodation": "Hotel in Moshi", "meals": "Breakfast"},
            ]
            self.create_itinerary(kilimanjaro2, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kilimanjaro2.name}"))

        # Package 3: Rongai Route (6 days)
        kilimanjaro3, created = Trekking.objects.get_or_create(
            name="Mount Kilimanjaro Climb - Rongai Route (6 Days)",
            location="Kilimanjaro National Park, Tanzania",
            starRating=4,
            days=6,
            price=Decimal("1650.00"),
            persons=8,
            description="The Rongai Route approaches Kilimanjaro from the north, near the Kenyan border. This less-crowded route offers a unique perspective of the mountain and is considered easier than other routes.",
            category="Kilimanjaro",
            image="awesome_packages/kilimanjaro_rongai.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Rongai Gate to Simba Camp", "description": "Drive to Rongai Gate (1,950m). Trek through pine forest to Simba Camp at 2,600m.", "activities": "Forest trekking, Bird watching", "accommodation": "Simba Camp (2,600m)", "meals": "Full Board"},
                {"day": 2, "title": "Simba Camp to Kikelewa Camp", "description": "Trek through heath and moorland to Kikelewa Camp at 3,600m.", "activities": "Moorland trekking, Views of Kibo", "accommodation": "Kikelewa Camp (3,600m)", "meals": "Full Board"},
                {"day": 3, "title": "Kikelewa Camp to Mawenzi Tarn Camp", "description": "Steep ascent to Mawenzi Tarn Camp at 4,300m with views of Mawenzi Peak.", "activities": "Alpine trekking, Photography", "accommodation": "Mawenzi Tarn Camp (4,300m)", "meals": "Full Board"},
                {"day": 4, "title": "Mawenzi Tarn Camp to Kibo Camp", "description": "Trek across the lunar landscape to Kibo Camp at 4,700m, the final camp.", "activities": "High desert trekking, Summit prep", "accommodation": "Kibo Camp (4,700m)", "meals": "Full Board"},
                {"day": 5, "title": "Summit Day! Kibo Camp to Uhuru Peak to Horombo Camp", "description": "Midnight ascent to Uhuru Peak (5,895m). Descend to Horombo Camp at 3,700m.", "activities": "Summit success, Celebration", "accommodation": "Horombo Camp (3,700m)", "meals": "Full Board"},
                {"day": 6, "title": "Horombo Camp to Marangu Gate", "description": "Final descent through rainforest to Marangu Gate. Receive certificates and transfer.", "activities": "Forest descent, Certificate ceremony", "accommodation": "Hotel in Moshi", "meals": "Breakfast"},
            ]
            self.create_itinerary(kilimanjaro3, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kilimanjaro3.name}"))

        # ==================== KENYA CATEGORY (3 PACKAGES) ====================

        # Package 1: Sirimon Route (5 days)
        kenya1, created = Trekking.objects.get_or_create(
            name="Mount Kenya Climb - Sirimon Route (5 Days)",
            location="Mount Kenya National Park, Kenya",
            starRating=5,
            days=5,
            price=Decimal("950.00"),
            persons=8,
            description="Conquer Mount Kenya via the scenic Sirimon Route. This 5-day adventure offers the best acclimatization profile for reaching Point Lenana, the trekking summit at 4,985 meters.",
            category="Kenya",
            image="awesome_packages/mount_kenya_sirimon.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nanyuki to Sirimon Gate to Old Moses Camp", "description": "Drive to Sirimon Gate (2,650m). Trek 9km to Old Moses Camp at 3,300m.", "activities": "Forest trekking, Wildlife spotting", "accommodation": "Old Moses Camp (3,300m)", "meals": "Full Board"},
                {"day": 2, "title": "Old Moses Camp to Shipton Camp", "description": "Trek 14km through Afro-alpine vegetation to Shipton Camp at 4,200m.", "activities": "Alpine trekking, Giant lobelia photography", "accommodation": "Shipton Camp (4,200m)", "meals": "Full Board"},
                {"day": 3, "title": "Acclimatization Day - Shipton Camp to Kami Hut", "description": "Climb high to Kami Hut (4,500m) and return for acclimatization.", "activities": "Acclimatization hike, Glacier views", "accommodation": "Shipton Camp (4,200m)", "meals": "Full Board"},
                {"day": 4, "title": "Summit Day! Shipton Camp to Point Lenana to Old Moses Camp", "description": "Early ascent to Point Lenana (4,985m) for sunrise. Descend to Old Moses Camp.", "activities": "Summit sunrise, Glacier photography", "accommodation": "Old Moses Camp (3,300m)", "meals": "Full Board"},
                {"day": 5, "title": "Old Moses Camp to Sirimon Gate", "description": "Final descent through forest to Sirimon Gate. Receive certificates.", "activities": "Forest descent, Certificate ceremony", "accommodation": "Hotel in Nanyuki", "meals": "Breakfast"},
            ]
            self.create_itinerary(kenya1, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kenya1.name}"))

        # Package 2: Chogoria Route (6 days)
        kenya2, created = Trekking.objects.get_or_create(
            name="Mount Kenya Climb - Chogoria Route (6 Days)",
            location="Mount Kenya National Park, Kenya",
            starRating=5,
            days=6,
            price=Decimal("1100.00"),
            persons=8,
            description="The Chogoria Route is considered the most scenic ascent of Mount Kenya, passing through dramatic gorges, waterfalls, and the stunning Lake Ellis before reaching Point Lenana.",
            category="Kenya",
            image="awesome_packages/mount_kenya_chogoria.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Chogoria Town to Road Head", "description": "Drive to Chogoria Town. Transfer to Road Head at 2,950m.", "activities": "Scenic drive, Forest views", "accommodation": "Road Head Camp (2,950m)", "meals": "Full Board"},
                {"day": 2, "title": "Road Head to Lake Ellis Camp", "description": "Trek through bamboo and montane forest to Lake Ellis at 3,500m.", "activities": "Forest trekking, Waterfall views", "accommodation": "Lake Ellis Camp (3,500m)", "meals": "Full Board"},
                {"day": 3, "title": "Lake Ellis Camp to Mintosa Camp", "description": "Trek to Mintosa Camp at 4,100m with stunning views of the peaks.", "activities": "Alpine trekking, Photography", "accommodation": "Mintosa Camp (4,100m)", "meals": "Full Board"},
                {"day": 4, "title": "Mintosa Camp to Austrian Hut", "description": "Trek across the Gorges Valley to Austrian Hut at 4,800m.", "activities": "Glacial valley trekking", "accommodation": "Austrian Hut (4,800m)", "meals": "Full Board"},
                {"day": 5, "title": "Summit Day! Austrian Hut to Point Lenana to Mintosa Camp", "description": "Early ascent to Point Lenana (4,985m). Descend back to Mintosa Camp.", "activities": "Summit sunrise, Celebration", "accommodation": "Mintosa Camp (4,100m)", "meals": "Full Board"},
                {"day": 6, "title": "Mintosa Camp to Chogoria Gate", "description": "Final descent through forest to Chogoria Gate. Transfer back to Nairobi.", "activities": "Forest descent, Certificate ceremony", "accommodation": "Hotel in Nairobi", "meals": "Breakfast"},
            ]
            self.create_itinerary(kenya2, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kenya2.name}"))

        # Package 3: Naro Moru Route (4 days)
        kenya3, created = Trekking.objects.get_or_create(
            name="Mount Kenya Climb - Naro Moru Route (4 Days)",
            location="Mount Kenya National Park, Kenya",
            starRating=4,
            days=4,
            price=Decimal("750.00"),
            persons=10,
            description="The Naro Moru Route is the quickest way to Point Lenana, but also the steepest. It's known for the infamous 'Vertical Bog' but offers a fast and challenging ascent.",
            category="Kenya",
            image="awesome_packages/mount_kenya_naro_moru.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Naro Moru Gate to Met Station", "description": "Drive to Naro Moru Gate (2,400m). Trek to Met Station at 3,000m.", "activities": "Forest trekking, Bird watching", "accommodation": "Met Station (3,000m)", "meals": "Full Board"},
                {"day": 2, "title": "Met Station to Mackinders Camp", "description": "Trek through the Vertical Bog to Mackinders Camp at 4,200m.", "activities": "Bog crossing, Alpine trekking", "accommodation": "Mackinders Camp (4,200m)", "meals": "Full Board"},
                {"day": 3, "title": "Summit Day! Mackinders Camp to Point Lenana to Met Station", "description": "Early ascent to Point Lenana (4,985m). Descend to Met Station.", "activities": "Summit sunrise, Glacier views", "accommodation": "Met Station (3,000m)", "meals": "Full Board"},
                {"day": 4, "title": "Met Station to Naro Moru Gate", "description": "Final descent through forest to Naro Moru Gate. Transfer to Nairobi.", "activities": "Forest descent, Certificate ceremony", "accommodation": "Hotel in Nairobi", "meals": "Breakfast"},
            ]
            self.create_itinerary(kenya3, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kenya3.name}"))

        # ==================== LONGONOT CATEGORY (3 PACKAGES) ====================

        # Package 1: Standard Crater Rim (1 day)
        longonot1, created = Trekking.objects.get_or_create(
            name="Mount Longonot Crater Rim Hike (1 Day)",
            location="Longonot National Park, Kenya",
            starRating=4,
            days=1,
            price=Decimal("85.00"),
            persons=15,
            description="Hike to the crater rim of Mount Longonot, a dormant stratovolcano at 2,776m with spectacular Rift Valley views.",
            category="Longonot",
            image="awesome_packages/longonot_hike.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Mount Longonot Crater Rim Hike", "description": "Early departure from Nairobi. Climb to crater rim (2,776m). Optional full rim circuit (7.2km). Return to Nairobi.", "activities": "Crater climbing, Rim walk, Wildlife spotting", "accommodation": "No accommodation (day hike)", "meals": "Breakfast"},
            ]
            self.create_itinerary(longonot1, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {longonot1.name}"))

        # Package 2: Longonot & Hell's Gate Combo (2 days)
        longonot2, created = Trekking.objects.get_or_create(
            name="Longonot & Hell's Gate Combo (2 Days)",
            location="Longonot & Hell's Gate, Kenya",
            starRating=4,
            days=2,
            price=Decimal("250.00"),
            persons=12,
            description="Combine the volcanic crater of Mount Longonot with cycling and hiking in Hell's Gate National Park for an action-packed weekend adventure.",
            category="Longonot",
            image="awesome_packages/longonot_hellsgate.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Mount Longonot - Crater Hike", "description": "Morning drive to Longonot. Climb to crater rim (2,776m). Afternoon optional rim circuit. Overnight in Naivasha.", "activities": "Crater climbing, Photography, Rest", "accommodation": "Hotel in Naivasha", "meals": "Full Board"},
                {"day": 2, "title": "Hell's Gate National Park Adventure", "description": "Morning cycling through Hell's Gate, walk through Ol Njorowa Gorge. See geothermal features and wildlife. Return to Nairobi.", "activities": "Cycling, Gorge walking, Wildlife viewing", "accommodation": "No accommodation", "meals": "Breakfast"},
            ]
            self.create_itinerary(longonot2, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {longonot2.name}"))

        # Package 3: Longonot Summit & Lake Naivasha (2 days)
        longonot3, created = Trekking.objects.get_or_create(
            name="Longonot Summit & Lake Naivasha Boat Safari (2 Days)",
            location="Longonot & Lake Naivasha, Kenya",
            starRating=4,
            days=2,
            price=Decimal("220.00"),
            persons=12,
            description="Climb Mount Longonot and explore Lake Naivasha's hippos and birdlife on a boat safari. Perfect weekend getaway from Nairobi.",
            category="Longonot",
            image="awesome_packages/longonot_naivasha.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Mount Longonot - Crater Hike", "description": "Drive to Longonot. Hike to crater rim. Overnight at a lakeside resort in Naivasha.", "activities": "Crater climbing, Swimming, Relaxation", "accommodation": "Lake Naivasha Resort", "meals": "Full Board"},
                {"day": 2, "title": "Lake Naivasha Boat Safari & Crescent Island", "description": "Morning boat safari to see hippos and birds. Visit Crescent Island for walking safari among animals. Return to Nairobi.", "activities": "Boat safari, Walking safari, Bird watching", "accommodation": "No accommodation", "meals": "Breakfast"},
            ]
            self.create_itinerary(longonot3, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {longonot3.name}"))

        # ==================== SUSWA CATEGORY (3 PACKAGES) ====================

        # Package 1: Standard Expedition (2 days)
        suswa1, created = Trekking.objects.get_or_create(
            name="Mount Suswa Expedition (2 Days)",
            location="Suswa National Park, Kenya",
            starRating=4,
            days=2,
            price=Decimal("350.00"),
            persons=10,
            description="Explore the unique volcanic wonderland of Mount Suswa with lava tubes, double crater, and Maasai cultural experiences.",
            category="Suswa",
            image="awesome_packages/mount_suswa.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Mount Suswa - Lava Tubes", "description": "Drive to Suswa. Explore Olbaltata lava tubes. Descend into caldera. Camp overnight.", "activities": "Lava tube exploration, Crater descent", "accommodation": "Camping inside Caldera", "meals": "Full Board"},
                {"day": 2, "title": "Inner Crater Descent and Return", "description": "Descend into inner crater (1,650m). Explore crater forest. Visit Maasai village. Return to Nairobi.", "activities": "Crater descent, Wildlife tracking, Maasai cultural visit", "accommodation": "No accommodation", "meals": "Full Board"},
            ]
            self.create_itinerary(suswa1, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {suswa1.name}"))

        # Package 2: Extended Volcanic Adventure (3 days)
        suswa2, created = Trekking.objects.get_or_create(
            name="Mount Suswa Volcanic Adventure (3 Days)",
            location="Suswa National Park, Kenya",
            starRating=5,
            days=3,
            price=Decimal("550.00"),
            persons=8,
            description="Extended volcanic exploration with full crater exploration, lava tube mapping, and overnight Maasai cultural immersion.",
            category="Suswa",
            image="awesome_packages/suswa_volcanic.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Mount Suswa - Lava Tubes", "description": "Drive to Suswa. Explore main lava tube system. Camp near inner crater.", "activities": "Lava tube exploration, Sunset views", "accommodation": "Caldera Campsite", "meals": "Full Board"},
                {"day": 2, "title": "Full Crater Exploration", "description": "Descend into inner crater. Explore crater floor forest. Wildlife tracking. Evening Maasai cultural stories.", "activities": "Crater descent, Forest walk, Cultural stories", "accommodation": "Caldera Campsite", "meals": "Full Board"},
                {"day": 3, "title": "Second Lava Tube & Maasai Village", "description": "Explore secondary lava tube. Visit Maasai manyatta. Ceremony and farewell. Return to Nairobi.", "activities": "Cave exploration, Cultural ceremony", "accommodation": "No accommodation", "meals": "Full Board"},
            ]
            self.create_itinerary(suswa2, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {suswa2.name}"))

        # Package 3: Suswa & Magadi Combo (4 days)
        suswa3, created = Trekking.objects.get_or_create(
            name="Suswa Volcano & Lake Magadi Expedition (4 Days)",
            location="Suswa & Lake Magadi, Kenya",
            starRating=5,
            days=4,
            price=Decimal("750.00"),
            persons=8,
            description="Combine the volcanic wonders of Mount Suswa with the unique soda lake ecosystem of Lake Magadi, famous for its flamingos and hot springs.",
            category="Suswa",
            image="awesome_packages/suswa_magadi.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Nairobi to Mount Suswa - Lava Tubes", "description": "Drive to Suswa. Explore lava tubes. Camp in caldera.", "activities": "Lava tube exploration, Camp setup", "accommodation": "Caldera Campsite", "meals": "Full Board"},
                {"day": 2, "title": "Inner Crater Exploration", "description": "Descend into inner crater. Explore forest and wildlife. Evening Maasai cultural experience.", "activities": "Crater descent, Wildlife tracking, Cultural stories", "accommodation": "Caldera Campsite", "meals": "Full Board"},
                {"day": 3, "title": "Lake Magadi - Hot Springs & Flamingos", "description": "Drive to Lake Magadi. Explore hot springs, watch flamingos. Overnight at Magadi Camp.", "activities": "Hot springs bathing, Bird watching", "accommodation": "Magadi Camp", "meals": "Full Board"},
                {"day": 4, "title": "Lake Magadi Sunrise & Return to Nairobi", "description": "Sunrise at Lake Magadi. Visit salt pans. Drive back to Nairobi via scenic route.", "activities": "Sunrise photography, Salt pan visit", "accommodation": "No accommodation", "meals": "Breakfast"},
            ]
            self.create_itinerary(suswa3, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {suswa3.name}"))

        # ==================== MERU CATEGORY (3 PACKAGES) ====================

        # Package 1: Standard Meru Climb (4 days)
        meru1, created = Trekking.objects.get_or_create(
            name="Mount Meru Climb - Momella Route (4 Days)",
            location="Arusha National Park, Tanzania",
            starRating=4,
            days=4,
            price=Decimal("850.00"),
            persons=10,
            description="Climb Mount Meru, Tanzania's second-highest peak at 4,565m. This challenging trek offers incredible views of Kilimanjaro and is excellent Kilimanjaro preparation.",
            category="Meru",
            image="awesome_packages/mount_meru_momella.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Arusha to Momella Gate to Miriakamba Hut", "description": "Drive to Momella Gate (1,500m). Trek through rainforest to Miriakamba Hut at 2,500m.", "activities": "Forest trekking, Wildlife viewing", "accommodation": "Miriakamba Hut (2,500m)", "meals": "Full Board"},
                {"day": 2, "title": "Miriakamba Hut to Saddle Hut", "description": "Trek through heath and moorland to Saddle Hut at 3,500m.", "activities": "Alpine trekking, Views of Kilimanjaro", "accommodation": "Saddle Hut (3,500m)", "meals": "Full Board"},
                {"day": 3, "title": "Summit Day! Saddle Hut to Socialist Peak to Miriakamba Hut", "description": "Early ascent to Socialist Peak (4,565m). Descend to Miriakamba Hut.", "activities": "Summit sunrise, Volcano crater views", "accommodation": "Miriakamba Hut (2,500m)", "meals": "Full Board"},
                {"day": 4, "title": "Miriakamba Hut to Momella Gate", "description": "Final descent through rainforest. Receive certificates. Return to Arusha.", "activities": "Forest descent, Wildlife sightings", "accommodation": "Hotel in Arusha", "meals": "Breakfast"},
            ]
            self.create_itinerary(meru1, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {meru1.name}"))

        # Package 2: Extended Meru with Wildlife Safari (5 days)
        meru2, created = Trekking.objects.get_or_create(
            name="Mount Meru Climb & Arusha Safari (5 Days)",
            location="Arusha National Park, Tanzania",
            starRating=5,
            days=5,
            price=Decimal("1200.00"),
            persons=8,
            description="Climb Mount Meru followed by a wildlife safari in Arusha National Park. See giraffes, buffalos, and flamingos on the park's famous Momela Lakes.",
            category="Meru",
            image="awesome_packages/meru_safari.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Arusha to Momella Gate to Miriakamba Hut", "description": "Drive to Momella Gate. Trek to Miriakamba Hut at 2,500m.", "activities": "Forest trekking, Colobus monkeys", "accommodation": "Miriakamba Hut (2,500m)", "meals": "Full Board"},
                {"day": 2, "title": "Miriakamba Hut to Saddle Hut", "description": "Trek to Saddle Hut at 3,500m with spectacular views.", "activities": "Alpine trekking, Photography", "accommodation": "Saddle Hut (3,500m)", "meals": "Full Board"},
                {"day": 3, "title": "Summit Day! Socialist Peak", "description": "Ascent to Socialist Peak (4,565m). Descend to Miriakamba Hut.", "activities": "Summit success, Celebration", "accommodation": "Miriakamba Hut (2,500m)", "meals": "Full Board"},
                {"day": 4, "title": "Descend to Momella Gate - Afternoon Safari", "description": "Morning descent. Afternoon game drive in Arusha National Park.", "activities": "Forest descent, Wildlife safari", "accommodation": "Hotel in Arusha", "meals": "Full Board"},
                {"day": 5, "title": "Morning Safari & Return to Arusha", "description": "Morning walk to Momela Lakes for flamingos. Canoeing option. Return to Arusha.", "activities": "Bird watching, Canoeing", "accommodation": "No accommodation", "meals": "Breakfast"},
            ]
            self.create_itinerary(meru2, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {meru2.name}"))

        # Package 3: Meru Kilimanjaro Combo (14 days)
        meru3, created = Trekking.objects.get_or_create(
            name="Mount Meru & Kilimanjaro Combo (14 Days)",
            location="Arusha & Kilimanjaro, Tanzania",
            starRating=5,
            days=14,
            price=Decimal("2950.00"),
            persons=7,
            description="The ultimate Tanzanian mountain adventure! Climb Mount Meru for acclimatization, then tackle Kilimanjaro via the Machame Route with higher success rates.",
            category="Meru",
            image="awesome_packages/meru_kilimanjaro.jpg"
        )

        if created:
            itinerary = [
                {"day": 1, "title": "Arrival in Arusha", "description": "Arrive at Kilimanjaro Airport. Transfer to hotel. Gear check and briefing.", "activities": "Rest, Gear preparation, Orientation", "accommodation": "Hotel in Arusha", "meals": "Breakfast"},
                {"day": 2, "title": "Arusha to Momella Gate to Miriakamba Hut", "description": "Start Mount Meru climb. Trek to Miriakamba Hut at 2,500m.", "activities": "Rainforest trekking", "accommodation": "Miriakamba Hut", "meals": "Full Board"},
                {"day": 3, "title": "Miriakamba Hut to Saddle Hut", "description": "Trek to Saddle Hut at 3,500m.", "activities": "Alpine trekking", "accommodation": "Saddle Hut", "meals": "Full Board"},
                {"day": 4, "title": "Summit Mount Meru - Socialist Peak", "description": "Ascent to Socialist Peak (4,565m). Descend to Miriakamba Hut.", "activities": "Summit success", "accommodation": "Miriakamba Hut", "meals": "Full Board"},
                {"day": 5, "title": "Descend Mount Meru & Rest Day", "description": "Complete Meru descent. Rest and prepare for Kilimanjaro.", "activities": "Forest descent, Rest", "accommodation": "Hotel in Arusha", "meals": "Full Board"},
                {"day": 6, "title": "Transfer to Kilimanjaro - Machame Gate to Machame Camp", "description": "Drive to Machame Gate. Start Kilimanjaro climb to Machame Camp.", "activities": "Rainforest trekking", "accommodation": "Machame Camp", "meals": "Full Board"},
                {"day": 7, "title": "Machame Camp to Shira Camp", "description": "Trek to Shira Camp on the Shira Plateau.", "activities": "Moorland trekking", "accommodation": "Shira Camp", "meals": "Full Board"},
                {"day": 8, "title": "Shira Camp to Barranco Camp via Lava Tower", "description": "Acclimatization day via Lava Tower.", "activities": "Alpine trekking", "accommodation": "Barranco Camp", "meals": "Full Board"},
                {"day": 9, "title": "Barranco Camp to Karanga Camp", "description": "Scramble Barranco Wall to Karanga Camp.", "activities": "Wall scrambling", "accommodation": "Karanga Camp", "meals": "Full Board"},
                {"day": 10, "title": "Karanga Camp to Barafu Camp", "description": "Trek to Barafu Camp, the final camp.", "activities": "Summit preparation", "accommodation": "Barafu Camp", "meals": "Full Board"},
                {"day": 11, "title": "Summit Day! Uhuru Peak to Mweka Camp", "description": "Midnight ascent to Uhuru Peak (5,895m). Descend to Mweka Camp.", "activities": "Summit success!", "accommodation": "Mweka Camp", "meals": "Full Board"},
                {"day": 12, "title": "Mweka Camp to Mweka Gate", "description": "Final descent. Receive certificates.", "activities": "Certificate ceremony", "accommodation": "Hotel in Moshi", "meals": "Breakfast"},
                {"day": 13, "title": "Rest Day & Celebration", "description": "Free day for rest, shopping, or optional safari.", "activities": "Rest, Celebration dinner", "accommodation": "Hotel in Moshi", "meals": "Full Board"},
                {"day": 14, "title": "Departure", "description": "Transfer to Kilimanjaro Airport for departure.", "activities": "Farewell", "accommodation": "No accommodation", "meals": "Breakfast"},
            ]
            self.create_itinerary(meru3, itinerary)
            self.stdout.write(self.style.SUCCESS(f"✓ Created {meru3.name}"))

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✅ SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write("="*50)
        self.stdout.write(f"📊 Total Trekking Packages: {Trekking.objects.count()}")
        self.stdout.write(f"📋 Total Itinerary Days: {ItineraryTreking.objects.count()}")
        self.stdout.write("\n📦 Packages created by category:")

        for category in ["Kilimanjaro", "Kenya", "Longonot", "Suswa", "Meru"]:
            packages = Trekking.objects.filter(category=category)
            self.stdout.write(f"\n  🏔 {category}: {packages.count()} packages")
            for package in packages:
                self.stdout.write(f"    • {package.name} ({package.days} days, {package.itinerary_days.count()} itinerary days)")