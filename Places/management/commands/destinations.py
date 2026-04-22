from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files import File
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
from Places.models import DestinationsCategory, Destinations

class Command(BaseCommand):
    help = 'Seed East Africa destinations into the database with images'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed destinations...'))
        
        # Create media directory
        media_root = Path('media/destinations')
        media_root.mkdir(parents=True, exist_ok=True)
        
        with transaction.atomic():
            # Categories data with colors
            categories_data = [
                {'category': 'National Parks', 'location': 'Various Locations', 'image_orientation': 'landscape', 'color1': '#2c3e50', 'color2': '#3498db'},
                {'category': 'Beach Destinations', 'location': 'Coastal Areas', 'image_orientation': 'landscape', 'color1': '#00b4db', 'color2': '#0083b0'},
                {'category': 'Mountain Treks', 'location': 'Mountain Regions', 'image_orientation': 'portrait', 'color1': '#4facfe', 'color2': '#00f2fe'},
                {'category': 'Cultural Sites', 'location': 'Various Locations', 'image_orientation': 'landscape', 'color1': '#cb356b', 'color2': '#bd3f32'},
                {'category': 'Lakes & Craters', 'location': 'Rift Valley & Beyond', 'image_orientation': 'landscape', 'color1': '#11998e', 'color2': '#38ef7d'},
                {'category': 'Wildlife Reserves', 'location': 'East Africa', 'image_orientation': 'landscape', 'color1': '#e96443', 'color2': '#904e95'},
                {'category': 'Historical Sites', 'location': 'East Africa', 'image_orientation': 'portrait', 'color1': '#42275a', 'color2': '#734b6d'},
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
            
            # Destinations data with descriptions
            destinations_data = [
                # National Parks
                ('Masai Mara National Reserve', 'National Parks', 'Famous for the Great Wildebeest Migration and Big Five sightings. Experience the thrill of watching over 1.5 million wildebeest crossing the Mara River.'),
                ('Serengeti National Park', 'National Parks', 'Tanzania\'s oldest national park, known for annual wildebeest migration. Home to the Big Five and endless plains that stretch to the horizon.'),
                ('Amboseli National Park', 'National Parks', 'Famous for elephant herds and Mount Kilimanjaro views. Capture stunning photos of elephants against Africa\'s highest peak.'),
                ('Queen Elizabeth National Park', 'National Parks', 'Uganda\'s most visited park, known for tree-climbing lions and the beautiful Kazinga Channel.'),
                ('Tsavo National Park', 'National Parks', 'Kenya\'s largest park, known for red elephants and dramatic lava landscapes. A true wilderness experience.'),
                ('Bwindi Impenetrable National Park', 'National Parks', 'Home to half of the world\'s mountain gorillas. An unforgettable jungle trekking experience.'),
                
                # Beach Destinations
                ('Zanzibar Beach', 'Beach Destinations', 'Spice Island with pristine white sand beaches and turquoise waters. Perfect for relaxation and water sports.'),
                ('Diani Beach', 'Beach Destinations', 'Kenya\'s premier beach with powdery white sand stretching 25km along the Indian Ocean.'),
                ('Watamu Beach', 'Beach Destinations', 'Marine protected area with coral reefs, ideal for snorkeling and diving with dolphins.'),
                ('Mafia Island', 'Beach Destinations', 'Perfect for diving and swimming with whale sharks. A hidden paradise off Tanzania\'s coast.'),
                
                # Mountain Treks
                ('Mount Kilimanjaro', 'Mountain Treks', 'Africa\'s highest peak at 5,895m with five ecological zones. The ultimate trekking challenge.'),
                ('Mount Kenya', 'Mountain Treks', 'Africa\'s second-highest mountain with stunning peaks and unique alpine vegetation.'),
                ('Mount Rwenzori', 'Mountain Treks', 'Mountains of the Moon, a UNESCO World Heritage site with glaciers and unique flora.'),
                ('Mount Elgon', 'Mountain Treks', 'Extinct volcano with the world\'s largest caldera, straddling Kenya-Uganda border.'),
                
                # Cultural Sites
                ('Maasai Village', 'Cultural Sites', 'Experience authentic Maasai culture and traditions. Learn about their customs, dances, and way of life.'),
                ('Stone Town', 'Cultural Sites', 'Zanzibar\'s historic center, a UNESCO World Heritage site with rich Swahili culture and architecture.'),
                ('Olduvai Gorge', 'Cultural Sites', 'The Cradle of Humankind, important paleoanthropological site with early hominid fossils.'),
                ('Lamu Old Town', 'Cultural Sites', 'Kenya\'s oldest Swahili settlement, a UNESCO site with preserved traditional architecture.'),
                
                # Lakes & Craters
                ('Ngorongoro Crater', 'Lakes & Craters', 'World\'s largest inactive volcanic caldera, a natural sanctuary for diverse wildlife.'),
                ('Lake Nakuru', 'Lakes & Craters', 'Famous for millions of flamingos and rhino sanctuary in Kenya\'s Rift Valley.'),
                ('Lake Victoria', 'Lakes & Craters', 'Africa\'s largest lake, shared by Kenya, Uganda, and Tanzania, rich in biodiversity.'),
                ('Lake Naivasha', 'Lakes & Craters', 'Freshwater lake known for hippos and boat rides, surrounded by acacia forests.'),
                
                # Wildlife Reserves
                ('Samburu Reserve', 'Wildlife Reserves', 'Unique wildlife including reticulated giraffe, Grevy\'s zebra, and Somali ostrich.'),
                ('Selous Game Reserve', 'Wildlife Reserves', 'Africa\'s largest game reserve, a UNESCO World Heritage site with diverse ecosystems.'),
                
                # Historical Sites
                ('Fort Jesus', 'Historical Sites', '16th-century Portuguese fort in Mombasa, a UNESCO World Heritage site.'),
                ('Gedi Ruins', 'Historical Sites', 'Abandoned Swahili town with fascinating history and unique architecture.'),
            ]
            
            # Create destinations with images
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
                        
                        # Generate image for this destination
                        color1 = categories_data[[c['category'] for c in categories_data].index(category_name)]['color1']
                        color2 = categories_data[[c['category'] for c in categories_data].index(category_name)]['color2']
                        orientation = category.image_orientation
                        
                        # Set dimensions based on orientation
                        if orientation == 'portrait':
                            width, height = 600, 800
                        else:
                            width, height = 800, 600
                        
                        # Create image
                        img = Image.new('RGB', (width, height), color=color1)
                        draw = ImageDraw.Draw(img)
                        
                        # Create gradient effect
                        for y in range(height):
                            ratio = y / height
                            r1 = int(color1[1:3], 16) if color1[1:3] else 0
                            g1 = int(color1[3:5], 16) if color1[3:5] else 0
                            b1 = int(color1[5:7], 16) if color1[5:7] else 0
                            r2 = int(color2[1:3], 16) if color2[1:3] else 0
                            g2 = int(color2[3:5], 16) if color2[3:5] else 0
                            b2 = int(color2[5:7], 16) if color2[5:7] else 0
                            
                            r = int(r1 * (1 - ratio) + r2 * ratio)
                            g = int(g1 * (1 - ratio) + g2 * ratio)
                            b = int(b1 * (1 - ratio) + b2 * ratio)
                            
                            draw.line([(0, y), (width, y)], fill=(r, g, b))
                        
                        # Add text
                        try:
                            font = ImageFont.truetype("arial.ttf", 36)
                            small_font = ImageFont.truetype("arial.ttf", 24)
                        except:
                            font = ImageFont.load_default()
                            small_font = ImageFont.load_default()
                        
                        # Center text
                        bbox = draw.textbbox((0, 0), name, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        
                        x = (width - text_width) // 2
                        y = (height - text_height) // 2 - 30
                        
                        draw.text((x, y), name, fill='white', font=font)
                        
                        # Add category
                        bbox = draw.textbbox((0, 0), category_name, font=small_font)
                        text_width = bbox[2] - bbox[0]
                        x = (width - text_width) // 2
                        draw.text((x, y + 60), category_name, fill='#FFD700', font=small_font)
                        
                        # Add location
                        bbox = draw.textbbox((0, 0), category.location, font=small_font)
                        text_width = bbox[2] - bbox[0]
                        x = (width - text_width) // 2
                        draw.text((x, y + 100), category.location, fill='white', font=small_font)
                        
                        # Save image
                        image_name = f"{name.replace(' ', '_').lower()}.jpg"
                        image_path = media_root / image_name
                        img.save(image_path, 'JPEG', quality=85)
                        
                        # Attach image to destination
                        with open(image_path, 'rb') as f:
                            image_file = File(f)
                            dest.image.save(image_name, image_file, save=True)
                        
                        self.stdout.write(self.style.SUCCESS(f'  Created: {name} with image'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  Exists: {name}'))
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Seeding complete!\n'
                f'  Categories: {DestinationsCategory.objects.count()}\n'
                f'  Destinations created: {created_count}\n'
                f'  Total destinations: {Destinations.objects.count()}'
            ))