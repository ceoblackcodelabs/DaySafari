from django.core.management.base import BaseCommand
from django.core.files import File
from pathlib import Path
import os
from Home.models import AirBNB, AirBNBImage  # Change to your app name

class Command(BaseCommand):
    help = 'Seed 9 AirBNB properties with multiple images'

    def handle(self, *args, **options):
        # Create default images directory if it doesn't exist
        media_root = Path('media/AirBNB')
        media_root.mkdir(parents=True, exist_ok=True)
        
        bnb_data = [
            {
                'location': 'Diani Beach, Kenya',
                'specification': '3b',
                'title': 'Ocean View Villa Diani',
                'description': 'Luxurious beachfront villa with private pool, stunning ocean views, and direct beach access. Perfect for families and groups.',
                'price_per_night': 350.00,
                'max_guests': 8,
                'num_images': 4
            },
            {
                'location': 'Masai Mara, Kenya',
                'specification': '2b',
                'title': 'Safari Edge Camp',
                'description': 'Unique glamping experience at the edge of Masai Mara. Watch wildlife from your private deck.',
                'price_per_night': 280.00,
                'max_guests': 5,
                'num_images': 3
            },
            {
                'location': 'Zanzibar, Tanzania',
                'specification': 'Studio',
                'title': 'Stone Town Heritage Suite',
                'description': 'Beautiful studio in the heart of Stone Town. Authentic Zanzibari architecture with modern amenities.',
                'price_per_night': 120.00,
                'max_guests': 2,
                'num_images': 3
            },
            {
                'location': 'Nairobi, Kenya',
                'specification': '1b',
                'title': 'Karen Luxury Loft',
                'description': 'Modern loft in Nairobi\'s upscale Karen neighborhood. Close to Giraffe Centre and Sheldrick Wildlife Trust.',
                'price_per_night': 150.00,
                'max_guests': 2,
                'num_images': 3
            },
            {
                'location': 'Mombasa, Kenya',
                'specification': '4b',
                'title': 'Nyali Beach Mansion',
                'description': 'Spacious beachfront mansion with 4 bedrooms, private pool, and stunning Indian Ocean views.',
                'price_per_night': 450.00,
                'max_guests': 10,
                'num_images': 5
            },
            {
                'location': 'Arusha, Tanzania',
                'specification': '2b',
                'title': 'Mount Meru View Lodge',
                'description': 'Cozy lodge with spectacular views of Mount Meru. Gateway to Serengeti and Ngorongoro safaris.',
                'price_per_night': 180.00,
                'max_guests': 4,
                'num_images': 3
            },
            {
                'location': 'Kigali, Rwanda',
                'specification': '1b',
                'title': 'Kigali Heights Apartment',
                'description': 'Modern apartment in Kigali\'s business district. Panoramic city views and rooftop pool.',
                'price_per_night': 110.00,
                'max_guests': 2,
                'num_images': 3
            },
            {
                'location': 'Kampala, Uganda',
                'specification': '3b',
                'title': 'Lake Victoria Resort',
                'description': 'Beautiful lakeside property with private beach, boat access, and stunning sunsets.',
                'price_per_night': 220.00,
                'max_guests': 6,
                'num_images': 4
            },
            {
                'location': 'Naivasha, Kenya',
                'specification': 'Studio',
                'title': 'Lake Naivasha Eco Cabin',
                'description': 'Eco-friendly cabin near Lake Naivasha. Perfect for bird watching and nature lovers.',
                'price_per_night': 95.00,
                'max_guests': 2,
                'num_images': 3
            }
        ]
        
        created_count = 0
        
        for data in bnb_data:
            # Create BNB
            bnb, created = AirBNB.objects.get_or_create(
                location=data['location'],
                defaults={
                    'specification': data['specification'],
                    'title': data['title'],
                    'description': data['description'],
                    'price_per_night': data['price_per_night'],
                    'max_guests': data['max_guests']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created BNB: {bnb.title}'))
                
                # Create placeholder images
                for i in range(data['num_images']):
                    # Create a simple colored placeholder image
                    from PIL import Image, ImageDraw
                    import random
                    
                    # Generate random colors for variety
                    colors = [
                        ('#420d24', '#5a1233'),  # Brand colors
                        ('#1e3c72', '#2a5298'),
                        ('#cb356b', '#bd3f32'),
                        ('#134e5e', '#71b280'),
                        ('#2c3e50', '#3498db'),
                        ('#e96443', '#904e95'),
                    ]
                    color1, color2 = random.choice(colors)
                    
                    # Create image
                    img = Image.new('RGB', (800, 600), color=color1)
                    draw = ImageDraw.Draw(img)
                    
                    # Add gradient effect (simple)
                    for y in range(600):
                        ratio = y / 600
                        r = int(int(color1[1:3], 16) * (1 - ratio) + int(color2[1:3], 16) * ratio)
                        g = int(int(color1[3:5], 16) * (1 - ratio) + int(color2[3:5], 16) * ratio)
                        b = int(int(color1[5:7], 16) * (1 - ratio) + int(color2[5:7], 16) * ratio)
                        draw.line([(0, y), (800, y)], fill=(r, g, b))
                    
                    # Add text
                    from PIL import ImageFont
                    try:
                        font = ImageFont.truetype("arial.ttf", 40)
                    except:
                        font = ImageFont.load_default()
                    
                    draw.text((400, 250), bnb.title, fill='white', anchor='mm', font=font)
                    draw.text((400, 320), f"Photo {i+1} of {data['num_images']}", fill='white', anchor='mm', font=font)
                    draw.text((400, 380), bnb.location, fill='white', anchor='mm', font=font)
                    
                    # Save image
                    image_name = f"{bnb.id}_image_{i+1}.jpg"
                    image_path = media_root / image_name
                    img.save(image_path, 'JPEG', quality=85)
                    
                    # Create AirBNBImage record
                    with open(image_path, 'rb') as f:
                        image_file = File(f)
                        AirBNBImage.objects.create(
                            airbnb=bnb,
                            image=image_file,
                            caption=f"Beautiful view of {bnb.title} - Photo {i+1}",
                            is_featured=(i == 0),  # First image is featured
                            order=i
                        )
                    
                    self.stdout.write(f'  └─ Added image {i+1}/{data["num_images"]}')
            else:
                self.stdout.write(self.style.WARNING(f'○ BNB already exists: {bnb.title}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  BNBs created: {created_count}\n'
            f'  Total BNBs: {AirBNB.objects.count()}'
        ))