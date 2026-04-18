from django.core.management.base import BaseCommand
from Home.models import Blogs, BlogComments
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed blogs data into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed blogs...'))
        
        blogs_data = [
            {
                'title': 'Top 10 Tips for Your First Safari',
                'author': 'Sarah Johnson',
                'content': 'Planning your first African safari? Here are essential tips to make your experience unforgettable. First, pack neutral-colored clothing to blend in with the environment. Second, bring binoculars for better wildlife viewing. Third, always listen to your guide - they have invaluable local knowledge. Fourth, carry a good camera with zoom lens. Fifth, stay hydrated and protect yourself from the sun. Sixth, be patient - wildlife sightings require time. Seventh, respect the animals by maintaining safe distance. Eighth, keep noise levels down to not disturb wildlife. Ninth, ask questions - guides love sharing knowledge. Tenth, embrace the experience and create lasting memories!',
                'likes': 2300,
                'author_image': 'sarah-johnson.jpg',
                'category': 'Safari Tips'
            },
            {
                'title': 'Complete Guide to the Great Migration',
                'author': 'Michael Otieno',
                'content': 'The Great Wildebeest Migration is one of nature\'s most spectacular events. Over 1.5 million wildebeest, along with hundreds of thousands of zebras and gazelles, travel in a continuous cycle across the Serengeti-Mara ecosystem. The best time to witness river crossings is between July and October. Key locations include the Mara River in Kenya and the Grumeti River in Tanzania. For photography, early morning light provides the best conditions. Remember to book accommodations well in advance as this is peak season. A hot air balloon safari offers the most breathtaking aerial views of the migration.',
                'likes': 3100,
                'author_image': 'michael-otieno.jpg',
                'category': 'Wildlife Guide'
            },
            {
                'title': 'Immersive Cultural Experiences in Kenya',
                'author': 'Grace Mwangi',
                'content': 'Beyond wildlife, Kenya offers rich cultural experiences that connect you with local communities. Visit a traditional Maasai village to learn about their customs, jumping dances, and sustainable practices. Try authentic Kenyan dishes like ugali, nyama choma, and sukuma wiki. Visit local markets in Nairobi for handmade crafts and jewelry. The Bomas of Kenya showcases traditional music and dance from various tribes. Remember to ask permission before taking photos of people, and support community-based tourism initiatives that directly benefit local families.',
                'likes': 1800,
                'author_image': 'grace-mwangi.jpg',
                'category': 'Cultural Travel'
            },
            {
                'title': 'Best Photography Spots in Serengeti',
                'author': 'James Kamau',
                'content': 'The Serengeti offers incredible photography opportunities. Top spots include: Retina Hippo Pool for close-up hippo shots, Moru Kopjes for lion sightings against rocky backdrops, Seronera River for year-round wildlife, and the Ndutu area for calving season (January-February). For sunrise photos, position yourself facing east near the Simba Kopjes. Use a lens with at least 200-400mm reach for wildlife. Golden hour (just after sunrise and before sunset) provides the most dramatic lighting. Always prioritize safety over getting the perfect shot.',
                'likes': 2500,
                'author_image': 'james-kamau.jpg',
                'category': 'Photography Tips'
            },
            {
                'title': 'Packing Essentials for East Africa Safari',
                'author': 'Lisa Anderson',
                'content': 'Packing smart can make or break your safari experience. Essential items include: lightweight neutral-colored clothing (avoid white and black), comfortable walking shoes, wide-brimmed hat, sunglasses, high-SPF sunscreen, insect repellent with DEET, binoculars, camera with extra batteries and memory cards, power bank, basic first-aid kit, prescription medications, reusable water bottle, and a daypack for game drives. Don\'t forget a warm jacket for early morning drives - it can get surprisingly chilly! Laundry services are available at most lodges, so you don\'t need to pack for every day.',
                'likes': 4200,
                'author_image': 'lisa-anderson.jpg',
                'category': 'Travel Tips'
            },
            {
                'title': 'Conservation Success Stories in East Africa',
                'author': 'Dr. Richard Leakey',
                'content': 'East Africa has seen remarkable conservation successes. Elephant populations in Kenya have more than doubled since the 1980s thanks to anti-poaching efforts. The mountain gorilla population in Uganda and Rwanda has increased by 25% in the last decade. Community conservancies in northern Kenya have created wildlife corridors that benefit both animals and local people. The banning of plastic bags in Kenya and Rwanda has significantly reduced environmental pollution. These successes show that with political will and community involvement, we can protect Africa\'s natural heritage for future generations.',
                'likes': 1700,
                'author_image': 'dr-richard-leakey.jpg',
                'category': 'Conservation'
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for blog_data in blogs_data:
            blog, created = Blogs.objects.get_or_create(
                title=blog_data['title'],
                defaults={
                    'author': blog_data['author'],
                    'content': blog_data['content'],
                    'likes': blog_data['likes']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created blog: {blog.title}'))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  ○ Already exists: {blog.title}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Blogs seeding complete!\n'
            f'  Blogs created: {created_count}\n'
            f'  Blogs skipped: {skipped_count}\n'
            f'  Total blogs: {Blogs.objects.count()}'
        ))