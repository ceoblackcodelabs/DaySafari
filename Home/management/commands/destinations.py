from django.core.management.base import BaseCommand
from django.db import transaction
from Home.models import DestinationsCategory, Destinations 

class Command(BaseCommand):
    help = 'Seed East Africa destinations into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed destinations...'))
        
        with transaction.atomic():
            # Categories data
            categories_data = [
                {'category': 'National Parks', 'location': 'Various Locations', 'image_orientation': 'landscape'},
                {'category': 'Beach Destinations', 'location': 'Coastal Areas', 'image_orientation': 'landscape'},
                {'category': 'Mountain Treks', 'location': 'Mountain Regions', 'image_orientation': 'portrait'},
                {'category': 'Cultural Sites', 'location': 'Various Locations', 'image_orientation': 'landscape'},
                {'category': 'Lakes & Craters', 'location': 'Rift Valley & Beyond', 'image_orientation': 'landscape'},
                {'category': 'Wildlife Reserves', 'location': 'East Africa', 'image_orientation': 'landscape'},
                {'category': 'Historical Sites', 'location': 'East Africa', 'image_orientation': 'portrait'},
            ]
            
            # Create categories
            categories = {}
            for cat_data in categories_data:
                cat, created = DestinationsCategory.objects.get_or_create(
                    category=cat_data['category'],
                    defaults={
                        'location': cat_data['location'],
                        'image_orientation': cat_data['image_orientation']
                    }
                )
                categories[cat.category] = cat
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created category: {cat.category}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  Category exists: {cat.category}'))
            
            # Destinations data
            destinations_data = [
                # National Parks
                ('Masai Mara National Reserve', 'National Parks', 'Famous for the Great Wildebeest Migration and Big Five sightings.'),
                ('Serengeti National Park', 'National Parks', 'Tanzania\'s oldest national park, known for annual wildebeest migration.'),
                ('Amboseli National Park', 'National Parks', 'Famous for elephant herds and Mount Kilimanjaro views.'),
                ('Queen Elizabeth National Park', 'National Parks', 'Uganda\'s most visited park, known for tree-climbing lions.'),
                ('Tsavo National Park', 'National Parks', 'Kenya\'s largest park, known for red elephants.'),
                ('Bwindi Impenetrable National Park', 'National Parks', 'Home to half of the world\'s mountain gorillas.'),
                
                # Beach Destinations
                ('Zanzibar Beach', 'Beach Destinations', 'Spice Island with pristine white sand beaches and turquoise waters.'),
                ('Diani Beach', 'Beach Destinations', 'Kenya\'s premier beach with powdery white sand.'),
                ('Watamu Beach', 'Beach Destinations', 'Marine protected area with coral reefs.'),
                ('Mafia Island', 'Beach Destinations', 'Perfect for diving and swimming with whale sharks.'),
                
                # Mountain Treks
                ('Mount Kilimanjaro', 'Mountain Treks', 'Africa\'s highest peak at 5,895m with five ecological zones.'),
                ('Mount Kenya', 'Mountain Treks', 'Africa\'s second-highest mountain with stunning peaks.'),
                ('Mount Rwenzori', 'Mountain Treks', 'Mountains of the Moon, a UNESCO World Heritage site.'),
                ('Mount Elgon', 'Mountain Treks', 'Extinct volcano with the world\'s largest caldera.'),
                
                # Cultural Sites
                ('Maasai Village', 'Cultural Sites', 'Experience authentic Maasai culture and traditions.'),
                ('Stone Town', 'Cultural Sites', 'Zanzibar\'s historic center, a UNESCO World Heritage site.'),
                ('Olduvai Gorge', 'Cultural Sites', 'The Cradle of Humankind, important paleoanthropological site.'),
                ('Lamu Old Town', 'Cultural Sites', 'Kenya\'s oldest Swahili settlement, a UNESCO site.'),
                
                # Lakes & Craters
                ('Ngorongoro Crater', 'Lakes & Craters', 'World\'s largest inactive volcanic caldera.'),
                ('Lake Nakuru', 'Lakes & Craters', 'Famous for flamingos and rhino sanctuary.'),
                ('Lake Victoria', 'Lakes & Craters', 'Africa\'s largest lake, rich in biodiversity.'),
                ('Lake Naivasha', 'Lakes & Craters', 'Freshwater lake known for hippos and boat rides.'),
                
                # Wildlife Reserves
                ('Samburu Reserve', 'Wildlife Reserves', 'Unique wildlife including reticulated giraffe.'),
                ('Selous Game Reserve', 'Wildlife Reserves', 'Africa\'s largest game reserve, a UNESCO site.'),
                
                # Historical Sites
                ('Fort Jesus', 'Historical Sites', '16th-century Portuguese fort in Mombasa, UNESCO site.'),
                ('Gedi Ruins', 'Historical Sites', 'Abandoned Swahili town with fascinating history.'),
            ]
            
            # Create destinations
            created_count = 0
            for name, category_name, description in destinations_data:
                category = categories.get(category_name)
                if category:
                    dest, created = Destinations.objects.get_or_create(
                        name=name,
                        category=category,
                        defaults={'description': description}
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  Exists: {name}'))
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Seeding complete!\n'
                f'  Categories: {DestinationsCategory.objects.count()}\n'
                f'  Destinations created: {created_count}\n'
                f'  Total destinations: {Destinations.objects.count()}'
            ))