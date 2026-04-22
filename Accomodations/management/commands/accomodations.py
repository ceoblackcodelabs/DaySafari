from django.core.management.base import BaseCommand
from django.core.files import File
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
from Accomodations.models import Accomodations, AccomodationsImage  # Change to your app name

class Command(BaseCommand):
    help = 'Seed accommodations with multiple images'

    def handle(self, *args, **options):
        # Create media directory
        media_root = Path('media/Accomodations')
        media_root.mkdir(parents=True, exist_ok=True)
        
        # Accommodation data
        accommodations_data = [
            {
                'name': 'Serenity Beach Villa',
                'location': 'Diani Beach, Kenya',
                'specification': '3b',
                'description': 'Luxurious beachfront villa with private pool, stunning ocean views, and direct beach access. Perfect for families and groups seeking a tropical paradise experience.',
                'price_per_night': 450.00,
                'max_guests': 8,
                'num_images': 4,
                'color1': '#1e3c72',
                'color2': '#2a5298'
            },
            {
                'name': 'Safari Edge Camp',
                'location': 'Masai Mara, Kenya',
                'specification': '2b',
                'description': 'Unique glamping experience at the edge of Masai Mara. Watch wildlife from your private deck while enjoying luxury tented accommodation.',
                'price_per_night': 350.00,
                'max_guests': 5,
                'num_images': 4,
                'color1': '#cb356b',
                'color2': '#bd3f32'
            },
            {
                'name': 'Stone Town Heritage Suite',
                'location': 'Zanzibar, Tanzania',
                'specification': 'Studio',
                'description': 'Beautiful studio in the heart of Stone Town. Authentic Zanzibari architecture with modern amenities and rich cultural atmosphere.',
                'price_per_night': 180.00,
                'max_guests': 2,
                'num_images': 3,
                'color1': '#134e5e',
                'color2': '#71b280'
            },
            {
                'name': 'Karen Luxury Loft',
                'location': 'Nairobi, Kenya',
                'specification': '1b',
                'description': 'Modern loft in Nairobi\'s upscale Karen neighborhood. Close to Giraffe Centre and Sheldrick Wildlife Trust. Perfect for business travelers.',
                'price_per_night': 220.00,
                'max_guests': 2,
                'num_images': 3,
                'color1': '#2c3e50',
                'color2': '#3498db'
            },
            {
                'name': 'Nyali Beach Mansion',
                'location': 'Mombasa, Kenya',
                'specification': '4b',
                'description': 'Spacious beachfront mansion with 4 bedrooms, private pool, and stunning Indian Ocean views. Ideal for large groups and special occasions.',
                'price_per_night': 650.00,
                'max_guests': 10,
                'num_images': 5,
                'color1': '#e96443',
                'color2': '#904e95'
            },
            {
                'name': 'Mount Meru View Lodge',
                'location': 'Arusha, Tanzania',
                'specification': '2b',
                'description': 'Cozy lodge with spectacular views of Mount Meru. Gateway to Serengeti and Ngorongoro safaris. Features local architecture and warm hospitality.',
                'price_per_night': 280.00,
                'max_guests': 4,
                'num_images': 4,
                'color1': '#11998e',
                'color2': '#38ef7d'
            },
            {
                'name': 'Kigali Heights Apartment',
                'location': 'Kigali, Rwanda',
                'specification': '1b',
                'description': 'Modern apartment in Kigali\'s business district. Panoramic city views, rooftop pool, and convenient access to business centers.',
                'price_per_night': 150.00,
                'max_guests': 2,
                'num_images': 3,
                'color1': '#4facfe',
                'color2': '#00f2fe'
            },
            {
                'name': 'Lake Victoria Resort',
                'location': 'Kampala, Uganda',
                'specification': '3b',
                'description': 'Beautiful lakeside property with private beach, boat access, and stunning sunsets. Perfect for romantic getaways and family vacations.',
                'price_per_night': 320.00,
                'max_guests': 6,
                'num_images': 4,
                'color1': '#fa709a',
                'color2': '#fee140'
            },
            {
                'name': 'Lake Naivasha Eco Cabin',
                'location': 'Naivasha, Kenya',
                'specification': 'Studio',
                'description': 'Eco-friendly cabin near Lake Naivasha. Perfect for bird watching, nature lovers, and those seeking tranquility away from city life.',
                'price_per_night': 140.00,
                'max_guests': 2,
                'num_images': 3,
                'color1': '#a8c0ff',
                'color2': '#3f2b96'
            },
            {
                'name': 'Amboseli Safari Lodge',
                'location': 'Amboseli, Kenya',
                'specification': '2b',
                'description': 'Luxury lodge with breathtaking views of Mount Kilimanjaro. Watch elephants roam against Africa\'s highest peak from your private balcony.',
                'price_per_night': 390.00,
                'max_guests': 4,
                'num_images': 4,
                'color1': '#f12711',
                'color2': '#f5af19'
            },
            {
                'name': 'Zanzibar Beach Bungalow',
                'location': 'Zanzibar, Tanzania',
                'specification': '1b',
                'description': 'Charming beach bungalow with direct ocean access. Perfect for honeymooners and couples seeking a romantic tropical escape.',
                'price_per_night': 210.00,
                'max_guests': 2,
                'num_images': 3,
                'color1': '#00b4db',
                'color2': '#0083b0'
            },
            {
                'name': 'Ngorongoro Crater View',
                'location': 'Ngorongoro, Tanzania',
                'specification': '3b',
                'description': 'Stunning property overlooking the famous Ngorongoro Crater. Unique location for wildlife enthusiasts and photographers.',
                'price_per_night': 520.00,
                'max_guests': 6,
                'num_images': 4,
                'color1': '#42275a',
                'color2': '#734b6d'
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for data in accommodations_data:
            # Check if accommodation already exists
            if Accomodations.objects.filter(name=data['name'], location=data['location']).exists():
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'○ Accommodation exists: {data["name"]}'))
                continue
            
            # Create accommodation
            accommodation = Accomodations.objects.create(
                name=data['name'],
                location=data['location'],
                specification=data['specification'],
                description=data['description'],
                price_per_night=data['price_per_night'],
                max_guests=data['max_guests']
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created accommodation: {accommodation.name}'))
            
            # Create images for this accommodation
            for i in range(data['num_images']):
                # Create image with different colors for each photo
                color1 = data['color1']
                color2 = data['color2']
                
                # Slight variation for each image
                if i == 1:
                    color1 = data['color2']
                    color2 = data['color1']
                elif i == 2:
                    # Mix colors
                    color1 = data['color1']
                    color2 = '#ffffff'
                
                # Create image
                img = Image.new('RGB', (800, 600), color=color1)
                draw = ImageDraw.Draw(img)
                
                # Create gradient effect
                for y in range(600):
                    ratio = y / 600
                    r1 = int(color1[1:3], 16) if color1[1:3] else 0
                    g1 = int(color1[3:5], 16) if color1[3:5] else 0
                    b1 = int(color1[5:7], 16) if color1[5:7] else 0
                    r2 = int(color2[1:3], 16) if color2[1:3] else 0
                    g2 = int(color2[3:5], 16) if color2[3:5] else 0
                    b2 = int(color2[5:7], 16) if color2[5:7] else 0
                    
                    r = int(r1 * (1 - ratio) + r2 * ratio)
                    g = int(g1 * (1 - ratio) + g2 * ratio)
                    b = int(b1 * (1 - ratio) + b2 * ratio)
                    
                    draw.line([(0, y), (800, y)], fill=(r, g, b))
                
                # Add text
                try:
                    font = ImageFont.truetype("arial.ttf", 32)
                    small_font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
                
                # Center text
                bbox = draw.textbbox((0, 0), accommodation.name, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (800 - text_width) // 2
                y = (600 - text_height) // 2 - 30
                
                draw.text((x, y), accommodation.name, fill='white', font=font)
                
                # Add specification
                spec_text = accommodation.get_specification_display()
                bbox = draw.textbbox((0, 0), spec_text, font=small_font)
                text_width = bbox[2] - bbox[0]
                x = (800 - text_width) // 2
                draw.text((x, y + 60), spec_text, fill='white', font=small_font)
                
                # Add price
                price_text = f"${accommodation.price_per_night}/night"
                bbox = draw.textbbox((0, 0), price_text, font=small_font)
                text_width = bbox[2] - bbox[0]
                x = (800 - text_width) // 2
                draw.text((x, y + 100), price_text, fill='#FFD700', font=small_font)
                
                # Add photo number
                photo_text = f"Photo {i+1} of {data['num_images']}"
                bbox = draw.textbbox((0, 0), photo_text, font=small_font)
                text_width = bbox[2] - bbox[0]
                x = (800 - text_width) // 2
                draw.text((x, y + 140), photo_text, fill='white', font=small_font)
                
                # Save image
                image_name = f"{accommodation.name.replace(' ', '_').lower()}_image_{i+1}.jpg"
                image_path = media_root / image_name
                img.save(image_path, 'JPEG', quality=85)
                
                # Create AccommodationImage record
                with open(image_path, 'rb') as f:
                    image_file = File(f)
                    accom_image = AccomodationsImage.objects.create(
                        accomodation=accommodation,
                        image=image_file,
                        caption=f"Beautiful view of {accommodation.name} - Photo {i+1}",
                        is_featured=(i == 0),  # First image is featured
                        order=i
                    )
                
                self.stdout.write(f'  └─ Added image {i+1}/{data["num_images"]}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Accommodations created: {created_count}\n'
            f'  Accommodations skipped: {skipped_count}\n'
            f'  Total accommodations: {Accomodations.objects.count()}\n'
            f'  Total images: {AccomodationsImage.objects.count()}'
        ))