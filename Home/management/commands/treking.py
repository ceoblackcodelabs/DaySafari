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

    def seed_trekking_packages(self, clear_existing=True):
        """Main seeding function"""
        if clear_existing:
            self.clear_existing_data()

        self.stdout.write(self.style.SUCCESS("🌄 Seeding trekking packages..."))

        # ==================== MOUNT KILIMANJARO - 7 DAYS MACHAME ROUTE ====================
        kilimanjaro, created = Trekking.objects.get_or_create(
            name="Mount Kilimanjaro Climb - Machame Route (7 Days)",
            defaults={
                "location": "Kilimanjaro National Park, Tanzania",
                "starRating": 5,
                "days": 7,
                "price": Decimal("1850.00"),
                "persons": 1,
                "description": "Experience the ultimate challenge of climbing Mount Kilimanjaro via the scenic Machame Route. This 7-day adventure takes you through five distinct climate zones, from lush rainforest to arctic summit. Known as the 'Whiskey Route', Machame offers breathtaking views and higher acclimatization success rates. You'll traverse stunning landscapes including the Shira Plateau, Barranco Wall, and the majestic glaciers of Uhuru Peak, the highest point in Africa at 5,895 meters. Our experienced guides, porters, and cooks ensure your safety and comfort throughout this life-changing journey. All camping equipment, meals, and park fees included.",
                "category": "Kilimanjaro",
                "image": "awesome_packages/kilimanjaro_machame.jpg"
            }
        )

        if created:
            # Kilimanjaro Itinerary Days
            itinerary_kili = [
                {
                    "day": 1,
                    "title": "Machame Gate to Machame Camp",
                    "description": """Your Kilimanjaro adventure begins with a morning drive from Moshi/Arusha to Machame Gate (1,640 meters). After completing park registration formalities, your trek commences through the magnificent montane rainforest. The trail is often muddy and slippery, but the path winds through ancient trees draped with moss and lichen. Keep an eye out for colobus monkeys and various bird species. After approximately 5-6 hours of trekking covering 11 km, you'll reach Machame Camp at 2,835 meters. This evening, your first night on the mountain offers spectacular views of the surrounding valleys and the opportunity to hear the sounds of the rainforest. Your guides will conduct health checks and provide orientation for the days ahead.""",
                    "activities": "Park registration, Rainforest trekking, Wildlife spotting, Photography, Camp setup orientation, Evening health briefing",
                    "accommodation": "Machame Camp (2,835m) - Mountain tents with sleeping mats",
                    "meals": "Full Board"
                },
                {
                    "day": 2,
                    "title": "Machame Camp to Shira Camp",
                    "description": """Today's trek takes you out of the rainforest and into heath and moorland zones. The morning begins with a steep climb through the forest edge, emerging onto a heath-covered ridge. The trail ascends steadily, offering spectacular views of Mount Meru floating on the clouds. After approximately 5 hours of trekking covering 5 km, you'll reach Shira Camp at 3,840 meters, situated on the Shira Plateau - a high-altitude desert formed by a collapsed volcanic crater. The afternoon is spent acclimatizing with a short exploration walk to Shira Cathedral (3,950m) before returning to camp. The panoramic views of Kibo Peak and the expansive plateau are breathtaking. Your crew will serve hot lunch and dinner while you adjust to the increasing altitude.""",
                    "activities": "Moorland trekking, Acclimatization walk to Shira Cathedral, Photography of Kibo Peak, Health monitoring, Plateau exploration",
                    "accommodation": "Shira Camp (3,840m) - Mountain tents with full camping amenities",
                    "meals": "Full Board"
                },
                {
                    "day": 3,
                    "title": "Shira Camp to Barranco Camp via Lava Tower",
                    "description": """This is a crucial acclimatization day using the 'climb high, sleep low' principle. You'll trek east toward Kibo's jagged peak, ascending to Lava Tower at 4,630 meters. The landscape transforms into alpine desert with strange Senecio and Lobelia plants dotting the terrain. After reaching Lava Tower (approximately 4-5 hours, 7 km), you'll have lunch and rest, experiencing high altitude before descending to Barranco Camp. The afternoon descent takes you down the rocky trail to Barranco Camp at 3,960 meters, nestled in a valley beneath the imposing Barranco Wall. This descent helps your body acclimatize while the vegetation returns to lush heather. The views of the evening sunset on Kibo's glaciers from camp are absolutely spectacular.""",
                    "activities": "Alpine desert trekking, Lava Tower exploration (4,630m), Photography of Kibo glaciers, Afternoon descent for acclimatization, Campfire evening briefing",
                    "accommodation": "Barranco Camp (3,960m) - Scenic valley camp with tent accommodation",
                    "meals": "Full Board"
                },
                {
                    "day": 4,
                    "title": "Barranco Camp to Karanga Camp",
                    "description": """The day starts with the famous Barranco Wall, a seemingly intimidating but non-technical scramble up a 300-meter cliff face. This exciting climb offers fantastic views and a sense of adventure. Your guides will assist you on the steeper sections. Once at the top, the trail undulates across the Karanga Valley with stunning views of the Southern Glaciers of Kibo. The trek today is shorter but involves steep ascents and descents, taking approximately 4-5 hours covering 6 km. You'll arrive at Karanga Camp (4,035 meters), strategically located for the final ascent preparation. The afternoon is reserved for rest and acclimatization, with optional short walks to explore the surrounding ridges. Your guides will conduct thorough health checks and provide detailed briefing for the summit night.""",
                    "activities": "Barranco Wall scrambling, Valley traversing, Glacier photography, Summit preparation briefing, Health and equipment checks",
                    "accommodation": "Karanga Camp (4,035m) - Strategic base camp with mountain views",
                    "meals": "Full Board"
                },
                {
                    "day": 5,
                    "title": "Karanga Camp to Barafu Summit Camp",
                    "description": """Today you trek to Barafu Camp, the final camp before summit night. The trail climbs steadily out of Karanga Valley, traversing rocky terrain with sparse vegetation. The air becomes noticeably thinner as you approach the high camp. After approximately 4-5 hours covering 4 km, you'll reach Barafu Camp at 4,640 meters, perched on a rocky ridge with panoramic views of Mawenzi Peak and the vast plains below. Upon arrival, you'll rest and prepare for the midnight summit attempt. Your guides provide a thorough briefing about the summit night strategy, what to expect, and how to pace yourself. Organize your gear, eat an early dinner, and attempt to sleep by 7 PM. The camp is exposed and cold, so proper layering is essential.""",
                    "activities": "High altitude trekking, Final camp preparation, Summit strategy briefing, Gear organization, Early dinner and rest",
                    "accommodation": "Barafu Camp (4,640m) - High camp with extreme mountain exposure",
                    "meals": "Full Board"
                },
                {
                    "day": 6,
                    "title": "Summit Day! Barafu Camp to Uhuru Peak to Mweka Camp",
                    "description": """THE SUMMIT! Wake at midnight for a light snack and warm-up before beginning the most challenging but rewarding day. The trail ascends steeply over loose scree to Stella Point (5,756 meters) on the crater rim, taking approximately 6-7 hours. The climb is mentally and physically demanding in the dark, cold, and thin air. From Stella Point, you'll follow the crater rim for another hour to Uhuru Peak (5,895 meters) - the Roof of Africa! Celebrate your incredible achievement with photos and tears of joy. After a short stay (no more than 15 minutes due to altitude), you'll descend back to Barafu Camp for brunch and rest. The afternoon continues the descent to Mweka Camp (3,100 meters) through moorland and forest, taking another 3-4 hours. This is the longest day (12-15 hours of walking) but the most triumphant!""",
                    "activities": "Midnight summit attempt, Uhuru Peak achievement (5,895m), Crater rim walking, Sunrise photography, Certificate collection, Celebration at summit",
                    "accommodation": "Mweka Camp (3,100m) - Forest camp with celebratory atmosphere",
                    "meals": "Full Board"
                },
                {
                    "day": 7,
                    "title": "Mweka Camp to Mweka Gate - Return to Moshi/Arusha",
                    "description": """Your final morning on Kilimanjaro includes a hearty breakfast before descending through lush tropical rainforest to Mweka Gate. The 3-4 hour trek covers 10 km through beautifully restored forest, where you might spot colobus monkeys and tropical birds. At Mweka Gate, you'll sign out and receive your official summit certificate (green for Stella Point or gold for Uhuru Peak). Successful climbers celebrate with high-fives and photos with their incredible mountain crew. Your vehicle awaits to transfer you back to your hotel in Moshi or Arusha for a well-deserved hot shower, celebration dinner, and rest after conquering Africa's highest peak. Congratulations, you are now a Kilimanjaro summiteer!""",
                    "activities": "Rainforest descent, Wildlife spotting, Certificate ceremony, Crew tipping and farewell, Celebration transfer to hotel",
                    "accommodation": "Hotel in Moshi/Arusha (own arrangement - ask for recommendations)",
                    "meals": "Breakfast"
                }
            ]

            for day in itinerary_kili:
                ItineraryTreking.objects.create(
                    package=kilimanjaro,
                    day_number=day["day"],
                    title=day["title"],
                    description=day["description"],
                    activities=day["activities"],
                    accommodation=day["accommodation"],
                    meals=day["meals"]
                )
            self.stdout.write(self.style.SUCCESS(f"✓ Created {kilimanjaro.name} with {len(itinerary_kili)} days"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ {kilimanjaro.name} already exists, skipping..."))

        # ==================== MOUNT KENYA - 5 DAYS SIRIMON ROUTE ====================
        mount_kenya, created = Trekking.objects.get_or_create(
            name="Mount Kenya Climb - Sirimon Route (5 Days)",
            defaults={
                "location": "Mount Kenya National Park, Kenya",
                "starRating": 5,
                "days": 5,
                "price": Decimal("950.00"),
                "persons": 1,
                "description": "Conquer Mount Kenya, Africa's second-highest peak at 4,985 meters, via the scenic Sirimon Route. This 5-day adventure offers the best acclimatization profile and highest success rate for reaching Point Lenana, the trekking summit. The route traverses through unique Afro-alpine vegetation, giant lobelias, and spectacular valleys. You'll experience breathtaking views of Batian and Nelion peaks, the true technical summits. Our experienced mountain guides, trained in altitude safety and first aid, ensure your comfort and success. This expedition combines physical challenge with the discovery of Kenya's glacial heritage and unique mountain ecology.",
                "category": "Kenya",
                "image": "awesome_packages/mount_kenya_sirimon.jpg"
            }
        )

        if created:
            itinerary_kenya = [
                {
                    "day": 1,
                    "title": "Nanyuki to Sirimon Gate to Old Moses Camp",
                    "description": """Your Mount Kenya adventure begins with a morning drive from Nanyuki to Sirimon Gate (2,650 meters). After park registration and briefing, your trek commences through magnificent mountain forest and heathland. The trail follows the Sirimon Track, gently ascending through stands of giant heather and unique Senecio forests. This 3-4 hour trek covering 9 km offers spectacular views of the surrounding valleys and Mount Kenya's peaks emerging in the distance. You'll reach Old Moses Camp (3,300 meters), also known as Likii North Camp, situated on a grassy ridge with panoramic mountain views. The afternoon includes an acclimatization walk to nearby viewpoints and orientation about the mountain's ecology and geology. Your first evening at altitude includes health monitoring and preparation for the days ahead.""",
                    "activities": "Forest trekking, Giant heather exploration, Wildlife spotting (colobus monkeys, hyrax), Acclimatization walk, Mountain ecology briefing",
                    "accommodation": "Old Moses Camp (3,300m) - Mountain hut with bunk beds and dining area",
                    "meals": "Full Board"
                },
                {
                    "day": 2,
                    "title": "Old Moses Camp to Shipton Camp",
                    "description": """Today involves a significant altitude gain as you trek from Old Moses Camp to Shipton Camp. The trail ascends through the Mackinder Valley, named after the first European to map the mountain. You'll pass through unique Afro-alpine vegetation zones featuring giant lobelias (Lobelia telekii) and groundsels (Senecio keniodendron), which can grow up to 6 meters tall. The landscape transforms into high-altitude desert with spectacular views of the main peaks. The trek takes approximately 6-7 hours covering 14 km, with a steady climb to Shipton Camp at 4,200 meters, nestled in a wide valley beneath the imposing peaks of Batian and Nelion. Upon arrival, rest and hydrate while your body adjusts to the altitude. The afternoon includes an acclimatization walk to nearby viewpoints with stunning glacier views.""",
                    "activities": "Afro-alpine trekking, Giant lobelia photography, Mackinder Valley exploration, Acclimatization walks, Peak identification lesson",
                    "accommodation": "Shipton Camp (4,200m) - Basic mountain huts with sleeping platforms",
                    "meals": "Full Board"
                },
                {
                    "day": 3,
                    "title": "Acclimatization Day - Shipton Camp to Kami Hut and Return",
                    "description": """This crucial acclimatization day follows the 'climb high, sleep low' principle. After breakfast, you'll trek toward Kami Hut (4,500 meters) on the approach to Point Lenana. The morning ascent takes approximately 2-3 hours, offering increasingly spectacular views of the Lewis Glacier and the jagged peaks of Batian (5,199m) and Nelion (5,188m). The route traverses rocky moraines and passes by small tarns (alpine lakes). Your guides will teach you about glacial geology and mountain ecology during the ascent. After reaching Kami Hut and enjoying the panoramic views, you'll descend back to Shipton Camp for lunch and afternoon rest. The descent helps your body acclimatize more effectively while the afternoon allows for rest, hydration, and final preparation for the summit attempt. Your guides conduct thorough health checks and summit briefing before an early dinner.""",
                    "activities": "High-altitude acclimatization hike, Glacial geology lesson, Lake tarns exploration, Summit preparation briefing, Health and equipment checks",
                    "accommodation": "Shipton Camp (4,200m) - Rest day with multiple short hikes",
                    "meals": "Full Board"
                },
                {
                    "day": 4,
                    "title": "Summit Day! Shipton Camp to Point Lenana to Old Moses Camp",
                    "description": """SUMMIT DAY! Wake at 2:00 AM for tea and biscuits before beginning the challenging ascent to Point Lenana (4,985 meters), the trekking summit of Mount Kenya. The initial climb follows a rocky ridge in darkness, requiring warm clothing and headlamps. After approximately 3-4 hours of careful scrambling over scree and rock, you'll reach Point Lenana just as dawn breaks over the African plains - a magical moment as the sun illuminates the glaciers and surrounding peaks. Celebrate your achievement with photos at the summit, taking in the 360-degree views of Mount Kilimanjaro to the south and the Aberdare Range to the west. After a short stay, descend via the same route back to Shipton Camp for breakfast and short rest. The descent continues to Old Moses Camp (3,300 meters), taking approximately 5-6 hours through the scenic Mackinder Valley. This long but triumphant day concludes with well-deserved rest and celebrations.""",
                    "activities": "Early morning summit attempt (2 AM start), Sunrise at Point Lenana (4,985m), Glacier photography, Celebration at summit, Long descent through Mackinder Valley",
                    "accommodation": "Old Moses Camp (3,300m) - Returning to lower altitude for better sleep",
                    "meals": "Full Board"
                },
                {
                    "day": 5,
                    "title": "Old Moses Camp to Sirimon Gate - Return to Nanyuki",
                    "description": """Your final morning on Mount Kenya includes a leisurely breakfast before the descent through the lush mountain forest to Sirimon Gate. The 3-4 hour trek covering 9 km offers final opportunities to spot wildlife including colobus monkeys, Sykes monkeys, and various bird species. The trail winds through giant heather zones and pristine forest, providing a gentle conclusion to your mountain adventure. At Sirimon Gate, you'll complete park exit formalities and receive your summit certificate from the Kenya Wildlife Service. Successful climbers celebrate with their mountain crew and guides, exchanging farewells and gratitude. Your vehicle transfers you back to Nanyuki for a hot shower, celebration lunch, and rest after conquering Africa's second-highest peak. Many climbers describe this as a more scenic and ecologically diverse experience than Kilimanjaro!""",
                    "activities": "Forest descent trekking, Wildlife spotting (colobus monkeys, birds), Certificate ceremony, Crew farewell and tipping, Transfer to Nanyuki",
                    "accommodation": "Hotel in Nanyuki (own arrangement - recommendations provided)",
                    "meals": "Breakfast"
                }
            ]

            for day in itinerary_kenya:
                ItineraryTreking.objects.create(
                    package=mount_kenya,
                    day_number=day["day"],
                    title=day["title"],
                    description=day["description"],
                    activities=day["activities"],
                    accommodation=day["accommodation"],
                    meals=day["meals"]
                )
            self.stdout.write(self.style.SUCCESS(f"✓ Created {mount_kenya.name} with {len(itinerary_kenya)} days"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ {mount_kenya.name} already exists, skipping..."))

        # ==================== MOUNT LONGONOT - 1 DAY HIKE ====================
        longonot, created = Trekking.objects.get_or_create(
            name="Mount Longonot Day Hike",
            defaults={
                "location": "Longonot National Park, Kenya",
                "starRating": 4,
                "days": 1,
                "price": Decimal("85.00"),
                "persons": 1,
                "description": "Experience the thrill of hiking Mount Longonot, a dormant stratovolcano in the Great Rift Valley. This 1-day adventure takes you to the crater rim at 2,776 meters, offering spectacular views of Lake Naivasha, Lake Elementaita, and the surrounding Rift Valley floor. The 3.1 km trail to the rim is steep but rewarding, with the option to circle the entire crater rim (7.2 km) for more adventurous hikers. Mount Longonot last erupted in the 1860s and features a fascinating forest inside the crater. This is the perfect half-day or full-day excursion from Nairobi, combining physical activity with incredible geology and wildlife spotting opportunities (buffalo, antelope, giraffe, and various birds).",
                "category": "Longonot",
                "image": "awesome_packages/longonot_hike.jpg"
            }
        )

        if created:
            itinerary_longonot = [
                {
                    "day": 1,
                    "title": "Mount Longonot Crater Rim Hike",
                    "description": """Your Mount Longonot adventure begins with an early morning departure from Nairobi (approx 7 AM) for the 90-minute drive along the scenic Rift Valley escarpment. Upon arrival at Longonot National Park gate (2,200 meters), complete registration and briefing from park rangers about safety and the trail. The initial ascent follows a steep, well-maintained trail through savannah grassland, taking approximately 45-60 minutes to reach the crater rim at 2,776 meters. This challenging climb rewards you with breathtaking views of the 1.8 km wide crater below, featuring a unique forest ecosystem inside the volcanic cone. At the rim, you have options: relax and enjoy the views, or tackle the full crater rim circuit (approximately 3-4 hours, 7.2 km). The rim walk offers spectacular 360-degree views of Lake Naivasha, Hell's Gate National Park, Mount Suswa, and the sprawling Rift Valley floor. Keep an eye out for wildlife including buffalo, eland, grant's gazelle, and various bird species. After lunch at the rim viewpoint (packed lunch), begin your descent back to the park gate (45 minutes). The afternoon includes a post-hike rest and optional short visit to nearby Lake Naivasha or Hell's Gate for further exploration. Return to Nairobi by late afternoon (approx 5-6 PM), completing an exhilarating day at one of Kenya's most accessible volcanoes. Your guides provide interpretation of the volcanic geology, Rift Valley formation, and local ecology throughout the day.""",
                    "activities": "Rift Valley scenic drive, Volcanic crater climbing, Crater rim circuit walk, Wildlife spotting (buffalo, antelope), Geology interpretation, Photography of crater floor forest, Optional Lake Naivasha visit",
                    "accommodation": "No accommodation (day hike - return to Nairobi or Naivasha hotels)",
                    "meals": "Breakfast"
                }
            ]

            for day in itinerary_longonot:
                ItineraryTreking.objects.create(
                    package=longonot,
                    day_number=day["day"],
                    title=day["title"],
                    description=day["description"],
                    activities=day["activities"],
                    accommodation=day["accommodation"],
                    meals=day["meals"]
                )
            self.stdout.write(self.style.SUCCESS(f"✓ Created {longonot.name} with {len(itinerary_longonot)} days"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ {longonot.name} already exists, skipping..."))

        # ==================== MOUNT SUSWA - 2 DAYS VOLCANIC ADVENTURE ====================
        suswa, created = Trekking.objects.get_or_create(
            name="Mount Suswa Expedition (2 Days)",
            defaults={
                "location": "Suswa National Park, Kenya",
                "starRating": 4,
                "days": 2,
                "price": Decimal("350.00"),
                "persons": 1,
                "description": "Explore the unique volcanic wonderland of Mount Suswa, a massive shield volcano in the Rift Valley. This 2-day expedition takes you into an ancient caldera featuring the world's unique double-crater structure, lava tube caves inhabited by hyrax and owls, and spectacular views from the rim. Mount Suswa's last eruption was approximately 400 years ago, leaving behind a fascinating landscape of lava flows, volcanic plugs, and dramatic escarpments. This less-visited mountain offers true off-the-beaten-path adventure combined with Maasai cultural experiences. You'll explore lava tubes, descend into the inner crater, enjoy wildlife spotting (giraffe, zebra, buffalo, leopard), and camp under the stars in the remote caldera. Perfect for volcanology enthusiasts and adventure seekers looking beyond the typical tourist routes.",
                "category": "Suswa",
                "image": "awesome_packages/mount_suswa.jpg"
            }
        )

        if created:
            itinerary_suswa = [
                {
                    "day": 1,
                    "title": "Nairobi to Mount Suswa - Crater Exploration and Lava Tubes",
                    "description": """Your Suswa expedition begins with an early 7 AM departure from Nairobi, driving through the scenic Rift Valley escarpment with stops at viewpoints overlooking Lake Naivasha and Mount Longonot. After approximately 2-3 hours, arrive at the Mount Suswa access point near the Maasai village of Ilngarua. After briefing by your guides and local Maasai elders, begin your exploration with a visit to the famous lava tube system (Olbaltata Caves). These massive tubes were formed by flowing lava and extend for kilometers underground, some large enough to drive a truck through! With headlamps, explore the main chamber where Maasai warriors historically sought refuge during tribal conflicts. Inside, you'll find unique soda pillars, stalactites formed by dripping minerals, and potential sightings of hyrax, owls, and bats. After the cave exploration, drive or hike toward the outer crater rim for lunch with spectacular views of the caldera below. The afternoon involves descending into the outer crater via 4x4 vehicle (or hiking for more adventurous groups) to reach the inner crater. Set up camp at a designated campsite near the base of the inner crater (1,800 meters). The late afternoon offers a guided walk along the inner crater rim, where you'll witness the sun setting over the Rift Valley with Mount Kilimanjaro visible on clear days. Evening includes a campfire briefing, Maasai cultural stories, and stargazing in the remote volcanic landscape, far from any light pollution.""",
                    "activities": "Rift Valley scenic drive, Lava tube exploration (Olbaltata Caves), Soda pillar photography, Crater rim lunch with views, 4x4 crater descent, Inner crater rim sunset walk, Maasai cultural stories, Night sky stargazing",
                    "accommodation": "Camping inside Suswa Caldera - Dome tents with sleeping mats, campfire area",
                    "meals": "Full Board"
                },
                {
                    "day": 2,
                    "title": "Inner Crater Descent and Return to Nairobi",
                    "description": """Wake early to the sounds of the African wilderness with sunrise over the ancient volcanic caldera. After a hearty breakfast, prepare for the highlight of the expedition - descending into the inner crater of Mount Suswa. This steep but manageable descent takes approximately 1-2 hours, requiring careful footing on volcanic scree. Your guide will point out unique geological features including fumaroles (steam vents), volcanic bombs, and different lava flow formations. At the floor of the inner crater (1,650 meters), you'll find a unique ecosystem featuring an enclosed forest, swampy areas fed by underground springs, and potential wildlife sightings including buffalo, bushbuck, and an incredible variety of birds. This isolated crater forest provides habitat for species rarely seen elsewhere. After exploring the crater floor and enjoying your packed lunch in this surreal environment, ascend back to the inner crater rim (1-1.5 hours). The afternoon involves driving (or hiking) out of the caldera, navigating the same dramatic escarpment. En route, stop at a traditional Maasai manyatta (village) for cultural interaction, learning about traditional medicine, beadwork, and cattle herding life. Your guides arrange a farewell ceremony with the local Maasai elders, complete with singing and dancing. Begin the return drive to Nairobi (2-3 hours), arriving by early evening (approx 6-7 PM). This expedition offers a rare combination of volcanic geology, cave exploration, wildlife, and authentic cultural experience unmatched by more commercialized destinations.""",
                    "activities": "Sunrise over caldera, Inner crater descent on volcanic scree, Fumarole and volcanic bomb identification, Crater floor forest exploration, Wildlife tracking (buffalo, bushbuck), Bird watching (endemic species), Maasai village cultural visit, Traditional ceremony and farewell, Rift Valley photography",
                    "accommodation": "No accommodation (return to Nairobi - hotel recommended)",
                    "meals": "Full Board"
                }
            ]

            for day in itinerary_suswa:
                ItineraryTreking.objects.create(
                    package=suswa,
                    day_number=day["day"],
                    title=day["title"],
                    description=day["description"],
                    activities=day["activities"],
                    accommodation=day["accommodation"],
                    meals=day["meals"]
                )
            self.stdout.write(self.style.SUCCESS(f"✓ Created {suswa.name} with {len(itinerary_suswa)} days"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ {suswa.name} already exists, skipping..."))

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✅ SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write("="*50)
        self.stdout.write(f"📊 Total Trekking Packages: {Trekking.objects.count()}")
        self.stdout.write(f"📋 Total Itinerary Days: {ItineraryTreking.objects.count()}")
        self.stdout.write("\n📦 Packages created:")
        for package in Trekking.objects.all():
            self.stdout.write(f"  • {package.name} ({package.days} days)")
            self.stdout.write(f"    Itinerary days: {package.itinerary_days.count()}")