from django.core.management.base import BaseCommand
from Home.models import Brochure
from django.core.files.base import ContentFile
from django.core.files import File
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings

class Command(BaseCommand):
    help = "Seed database with sample brochures"

    def create_placeholder_image(self, title, color):
        """Create a placeholder image for brochures"""
        # Create a new image with given color
        img = Image.new('RGB', (800, 600), color=color)
        draw = ImageDraw.Draw(img)

        # Add text to image
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None

        # Draw text
        text = title[:30]  # Limit text length
        # Get text size (approximate for default font)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the text
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2
        draw.text((x, y), text, fill='white', font=font)

        # Save to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)

        return ContentFile(img_byte_arr.read(), name=f"{title[:20]}.jpg")

    def create_placeholder_pdf(self, title):
        """Create a simple placeholder PDF"""
        # This creates a basic PDF using reportlab if available
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import simpleSplit

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Add title
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, height - 50, title)

            # Add content
            c.setFont("Helvetica", 12)
            y = height - 100
            content = [
                f"Welcome to our {title}",
                "",
                "This brochure contains detailed information about our safari packages,",
                "tour itineraries, accommodation options, and travel tips for East Africa.",
                "",
                "Key Highlights:",
                "• Expert safari guides",
                "• Luxury accommodation",
                "• Wildlife viewing opportunities",
                "• Cultural experiences",
                "• Best time to visit",
                "",
                "Contact us for more information:",
                "Email: info@dayssafaris.com",
                "Phone: +254 700 000 000",
                "",
                "Visit our website: www.dayssafaris.com"
            ]

            for line in content:
                c.drawString(50, y, line)
                y -= 20
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 50

            c.save()
            buffer.seek(0)
            return ContentFile(buffer.read(), name=f"{title[:30]}.pdf")

        except ImportError:
            # If reportlab is not installed, create a text file instead
            content = f"""
            {title}
            {'=' * len(title)}

            This brochure contains detailed information about our safari packages,
            tour itineraries, accommodation options, and travel tips for East Africa.

            Key Highlights:
            - Expert safari guides
            - Luxury accommodation
            - Wildlife viewing opportunities
            - Cultural experiences
            - Best time to visit

            Contact us for more information:
            Email: info@dayssafaris.com
            Phone: +254 700 000 000

            Visit our website: www.dayssafaris.com
            """
            return ContentFile(content.encode(), name=f"{title[:30]}.txt")

    def handle(self, *args, **kwargs):
        brochures_data = [
            {
                "title": "East Africa Safari Adventure 2025",
                "description": "Experience the ultimate East African safari adventure with visits to Masai Mara, Serengeti, Ngorongoro Crater, and Amboseli. This comprehensive guide includes detailed itineraries, accommodation options, wildlife viewing tips, and pricing information for the perfect safari experience.",
                "color": "#1a472a",  # Dark green
            },
            {
                "title": "Kenya & Tanzania Wildlife Guide",
                "description": "Discover the best of Kenya and Tanzania's wildlife destinations. This brochure covers the Great Wildebeest Migration, Big Five sightings, bird watching hotspots, and conservation efforts. Perfect for wildlife enthusiasts and photographers.",
                "color": "#d2691e",  # Chocolate brown
            },
            {
                "title": "Luxury Safari & Beach Holidays",
                "description": "Combine the thrill of safari with relaxation on pristine beaches. Explore luxury lodges in the bush and beachfront resorts in Zanzibar, Diani, and Mombasa. Includes honeymoon packages, family deals, and exclusive offers.",
                "color": "#006994",  # Ocean blue
            }
        ]

        created_count = 0
        updated_count = 0

        for brochure_data in brochures_data:
            # Check if brochure already exists
            obj, created = Brochure.objects.get_or_create(
                title=brochure_data["title"],
                defaults={
                    "description": brochure_data["description"],
                }
            )

            if created:
                # Create placeholder image
                if not obj.image:
                    image_file = self.create_placeholder_image(
                        brochure_data["title"],
                        brochure_data["color"]
                    )
                    obj.image.save(f"{brochure_data['title'][:20]}.jpg", image_file, save=False)

                # Create placeholder PDF
                if not obj.pdf_file:
                    pdf_file = self.create_placeholder_pdf(brochure_data["title"])
                    obj.pdf_file.save(f"{brochure_data['title'][:30]}.pdf", pdf_file, save=False)

                obj.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Added: {obj.title}"))
                self.stdout.write(f"  - Image: {obj.image.url if obj.image else 'Not created'}")
                self.stdout.write(f"  - PDF: {obj.pdf_file.url if obj.pdf_file else 'Not created'}")
            else:
                self.stdout.write(self.style.WARNING(f"○ Already exists: {obj.title}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Done! Added {created_count} new brochures."))

        if created_count == 0:
            self.stdout.write(self.style.WARNING("\n💡 Tip: To re-seed, delete existing brochures first:"))
            self.stdout.write("   python manage.py shell -c 'from Home.models import Brochure; Brochure.objects.all().delete()'")