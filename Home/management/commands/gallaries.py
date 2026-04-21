from django.core.management.base import BaseCommand
from django.core.files import File
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
from Home.models import Gallery, GalleryCategory  # Change to your app name

class Command(BaseCommand):
    help = 'Seed gallery with categories and images'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            'Wildlife Safari',
            'Beach Holiday', 
            'Mountain Treks',
            'Cultural Tours',
            'Luxury Lodges',
            'Aerial Views'
        ]
        
        categories = {}
        for cat_name in categories_data:
            category, created = GalleryCategory.objects.get_or_create(name=cat_name)
            categories[cat_name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {cat_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Category exists: {cat_name}'))
        
        # Create media directory
        media_root = Path('media/gallery_images')
        media_root.mkdir(parents=True, exist_ok=True)
        
        # Gallery images data
        gallery_data = [
            # Wildlife Safari
            {'name': 'Lion Pride in Masai Mara', 'category': 'Wildlife Safari', 'color1': '#e67e22', 'color2': '#d35400'},
            {'name': 'Elephant Herd at Amboseli', 'category': 'Wildlife Safari', 'color1': '#2c3e50', 'color2': '#34495e'},
            {'name': 'Giraffe Family', 'category': 'Wildlife Safari', 'color1': '#16a085', 'color2': '#1abc9c'},
            {'name': 'Zebra Crossing River', 'category': 'Wildlife Safari', 'color1': '#f39c12', 'color2': '#e67e22'},
            {'name': 'Leopard in Tree', 'category': 'Wildlife Safari', 'color1': '#8e44ad', 'color2': '#9b59b6'},
            {'name': 'Cheetah Running', 'category': 'Wildlife Safari', 'color1': '#d35400', 'color2': '#e67e22'},
            {'name': 'Buffalo Herd', 'category': 'Wildlife Safari', 'color1': '#2c3e50', 'color2': '#34495e'},
            {'name': 'Rhinoceros Grazing', 'category': 'Wildlife Safari', 'color1': '#7f8c8d', 'color2': '#95a5a6'},
            {'name': 'Hippo Pool', 'category': 'Wildlife Safari', 'color1': '#1abc9c', 'color2': '#16a085'},
            
            # Beach Holiday
            {'name': 'Diani Beach Sunset', 'category': 'Beach Holiday', 'color1': '#ff6b6b', 'color2': '#ee5a24'},
            {'name': 'Zanzibar Ocean View', 'category': 'Beach Holiday', 'color1': '#0abde3', 'color2': '#0984e3'},
            {'name': 'Watamu Beach', 'category': 'Beach Holiday', 'color1': '#00cec9', 'color2': '#00b894'},
            {'name': 'Malindi Beach Resort', 'category': 'Beach Holiday', 'color1': '#fd79a8', 'color2': '#e84393'},
            {'name': 'Mombasa North Coast', 'category': 'Beach Holiday', 'color1': '#74b9ff', 'color2': '#0984e3'},
            {'name': 'Lamu Archipelago', 'category': 'Beach Holiday', 'color1': '#fdcb6e', 'color2': '#f39c12'},
            
            # Mountain Treks
            {'name': 'Mt Kilimanjaro Summit', 'category': 'Mountain Treks', 'color1': '#2d3436', 'color2': '#636e72'},
            {'name': 'Mt Kenya Peak', 'category': 'Mountain Treks', 'color1': '#4a69bd', 'color2': '#1e3799'},
            {'name': 'Mt Rwenzori', 'category': 'Mountain Treks', 'color1': '#38ada9', 'color2': '#079992'},
            {'name': 'Mt Elgon', 'category': 'Mountain Treks', 'color1': '#b71540', 'color2': '#eb2f06'},
            {'name': 'Mt Meru', 'category': 'Mountain Treks', 'color1': '#0c2461', 'color2': '#1e3799'},
            
            # Cultural Tours
            {'name': 'Maasai Village Dance', 'category': 'Cultural Tours', 'color1': '#c0392b', 'color2': '#e74c3c'},
            {'name': 'Stone Town Zanzibar', 'category': 'Cultural Tours', 'color1': '#d35400', 'color2': '#e67e22'},
            {'name': 'Kibera Art', 'category': 'Cultural Tours', 'color1': '#8e44ad', 'color2': '#9b59b6'},
            {'name': 'Samburu Culture', 'category': 'Cultural Tours', 'color1': '#27ae60', 'color2': '#2ecc71'},
            {'name': 'Lamu Fort', 'category': 'Cultural Tours', 'color1': '#2980b9', 'color2': '#3498db'},
            {'name': 'Turkana Village', 'category': 'Cultural Tours', 'color1': '#f39c12', 'color2': '#e67e22'},
            
            # Luxury Lodges
            {'name': 'Mara Serena Lodge', 'category': 'Luxury Lodges', 'color1': '#6c5ce7', 'color2': '#a29bfe'},
            {'name': 'Angama Mara', 'category': 'Luxury Lodges', 'color1': '#fd79a8', 'color2': '#e84393'},
            {'name': 'Giraffe Manor', 'category': 'Luxury Lodges', 'color1': '#00b894', 'color2': '#55efc4'},
            {'name': '&Beyond Ngorongoro', 'category': 'Luxury Lodges', 'color1': '#0984e3', 'color2': '#74b9ff'},
            {'name': 'Four Seasons Serengeti', 'category': 'Luxury Lodges', 'color1': '#d63031', 'color2': '#ff7675'},
            
            # Aerial Views
            {'name': 'Balloon Safari', 'category': 'Aerial Views', 'color1': '#fdcb6e', 'color2': '#f39c12'},
            {'name': 'Helicopter Tour', 'category': 'Aerial Views', 'color1': '#00cec9', 'color2': '#00b894'},
            {'name': 'Mara River Aerial', 'category': 'Aerial Views', 'color1': '#0984e3', 'color2': '#74b9ff'},
            {'name': 'Kilimanjaro from Above', 'category': 'Aerial Views', 'color1': '#2d3436', 'color2': '#636e72'},
            {'name': 'Great Rift Valley', 'category': 'Aerial Views', 'color1': '#27ae60', 'color2': '#2ecc71'},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for data in gallery_data:
            category = categories.get(data['category'])
            if not category:
                continue
            
            # Check if gallery item already exists
            if Gallery.objects.filter(name=data['name'], category=category).exists():
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'○ Gallery exists: {data["name"]}'))
                continue
            
            # Create placeholder image
            img = Image.new('RGB', (800, 600), color=data['color1'])
            draw = ImageDraw.Draw(img)
            
            # Create gradient effect
            for y in range(600):
                ratio = y / 600
                r1 = int(data['color1'][1:3], 16)
                g1 = int(data['color1'][3:5], 16)
                b1 = int(data['color1'][5:7], 16)
                r2 = int(data['color2'][1:3], 16)
                g2 = int(data['color2'][3:5], 16)
                b2 = int(data['color2'][5:7], 16)
                
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                
                draw.line([(0, y), (800, y)], fill=(r, g, b))
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 36)
                small_font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Center text
            bbox = draw.textbbox((0, 0), data['name'], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (800 - text_width) // 2
            y = (600 - text_height) // 2
            
            draw.text((x, y), data['name'], fill='white', font=font)
            draw.text((x, y + 50), data['category'], fill='white', font=small_font)
            
            # Save image
            image_name = f"{data['name'].replace(' ', '_').lower()}.jpg"
            image_path = media_root / image_name
            img.save(image_path, 'JPEG', quality=85)
            
            # Create Gallery record
            with open(image_path, 'rb') as f:
                image_file = File(f)
                gallery = Gallery.objects.create(
                    name=data['name'],
                    category=category
                )
                gallery.image.save(image_name, image_file, save=True)
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Created gallery: {data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Gallery items created: {created_count}\n'
            f'  Gallery items skipped: {skipped_count}\n'
            f'  Total categories: {GalleryCategory.objects.count()}\n'
            f'  Total images: {Gallery.objects.count()}'
        ))