from django.core.management.base import BaseCommand
from django.core.files import File
from Home.models import AwesomePackages
import os
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed awesome packages data into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed awesome packages...'))
        
        packages_data = [
            {
                'name': 'Masai Mara Safari Adventure',
                'location': 'Masai Mara, Kenya',
                'starRating': 5,
                'days': 4,
                'price': Decimal('849.00'),
                'persons': 6,
                'description': 'Experience the breathtaking Great Wildebeest Migration, spot the Big Five, and enjoy stunning sunsets over the African savannah. Includes game drives, accommodation, and meals.',
                'package_type': 'Wildlife Safari Package'
            },
            {
                'name': 'Zanzibar Beach Holiday',
                'location': 'Zanzibar, Tanzania',
                'starRating': 5,
                'days': 6,
                'price': Decimal('1299.00'),
                'persons': 2,
                'description': 'Relax on pristine white-sand beaches, swim in turquoise waters, explore Stone Town\'s rich history, and enjoy spice tours. Perfect for honeymooners and beach lovers.',
                'package_type': 'Tropical Paradise Package'
            },
            {
                'name': 'Serengeti Migration Safari',
                'location': 'Serengeti, Tanzania',
                'starRating': 5,
                'days': 5,
                'price': Decimal('1499.00'),
                'persons': 8,
                'description': 'Witness the world\'s largest animal migration with over 1.5 million wildebeest. Includes expert guides, luxury tented camps, and hot air balloon safari option.',
                'package_type': 'Wildlife Photography Package'
            },
            {
                'name': 'Amboseli Elephant Experience',
                'location': 'Amboseli, Kenya',
                'starRating': 5,
                'days': 3,
                'price': Decimal('649.00'),
                'persons': 4,
                'description': 'Get up close with massive elephant herds against the backdrop of Mount Kilimanjaro. Perfect for family safaris with guided nature walks and cultural visits.',
                'package_type': 'Family Safari Package'
            },
            {
                'name': 'Gorilla Trekking Adventure',
                'location': 'Bwindi, Uganda',
                'starRating': 5,
                'days': 4,
                'price': Decimal('1899.00'),
                'persons': 6,
                'description': 'Rare opportunity to track mountain gorillas in their natural habitat. Includes permits, expert guides, and comfortable lodging in the jungle.',
                'package_type': 'Primates Safari Package'
            },
            {
                'name': 'Victoria Falls Experience',
                'location': 'Victoria Falls, Zambia/Zimbabwe',
                'starRating': 4,
                'days': 3,
                'price': Decimal('899.00'),
                'persons': 4,
                'description': 'Experience the thunderous smoke that thunders, with activities including bungee jumping, white water rafting, and sunset cruises.',
                'package_type': 'Adventure Package'
            },
            {
                'name': 'Ngorongoro Crater Safari',
                'location': 'Ngorongoro, Tanzania',
                'starRating': 5,
                'days': 3,
                'price': Decimal('999.00'),
                'persons': 6,
                'description': 'Explore the world\'s largest inactive volcanic caldera, home to the Big Five and unique wildlife. Includes game drives and crater floor picnic.',
                'package_type': 'Wildlife Safari Package'
            },
            {
                'name': 'Kenya Highlights Safari',
                'location': 'Nairobi, Kenya',
                'starRating': 4,
                'days': 7,
                'price': Decimal('1599.00'),
                'persons': 8,
                'description': 'Comprehensive tour covering Amboseli, Lake Nakuru, and Masai Mara. Perfect for first-time visitors wanting the complete Kenyan safari experience.',
                'package_type': 'Combo Safari Package'
            },
            {
                'name': 'Mount Kilimanjaro Climb',
                'location': 'Moshi, Tanzania',
                'starRating': 5,
                'days': 7,
                'price': Decimal('1899.00'),
                'persons': 10,
                'description': 'Trek Africa\'s highest peak via the Machame route. Includes experienced guides, porters, camping equipment, and all meals on the mountain.',
                'package_type': 'Mountain Trekking Package'
            },
            {
                'name': 'Rwanda Cultural Tour',
                'location': 'Kigali, Rwanda',
                'starRating': 4,
                'days': 5,
                'price': Decimal('1199.00'),
                'persons': 6,
                'description': 'Immerse in Rwanda\'s rich culture, visit genocide memorials, experience traditional dance, and explore the beautiful Lake Kivu.',
                'package_type': 'Cultural Package'
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for package_data in packages_data:
            package, created = AwesomePackages.objects.get_or_create(
                name=package_data['name'],
                defaults={
                    'location': package_data['location'],
                    'starRating': package_data['starRating'],
                    'days': package_data['days'],
                    'price': package_data['price'],
                    'persons': package_data['persons'],
                    'description': package_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {package.name}'))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  ○ Already exists: {package.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Packages created: {created_count}\n'
            f'  Packages skipped: {skipped_count}\n'
            f'  Total packages: {AwesomePackages.objects.count()}'
        ))