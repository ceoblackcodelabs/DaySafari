from django.core.management.base import BaseCommand
from Home.models import Testimonials
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed testimonials data into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed testimonials...'))
        
        testimonials_data = [
            {
                'name': 'Sarah Thompson',
                'location': 'London, United Kingdom',
                'feedback': 'An absolutely incredible experience! Day Safaris planned every detail perfectly. Our guide was knowledgeable and passionate about wildlife. We saw the Big Five within three days! The accommodations were luxurious and the food was excellent. Highly recommend this company for anyone visiting East Africa.',
                'starRating': 5
            },
            {
                'name': 'David & Maria Chen',
                'location': 'Sydney, Australia',
                'feedback': 'Our family safari with Day Safaris exceeded all expectations. The team was professional, friendly, and went above and beyond to make our trip special. The kids loved the educational aspects, and we felt completely safe throughout. Will definitely book with them again!',
                'starRating': 5
            },
            {
                'name': 'Robert van der Berg',
                'location': 'Amsterdam, Netherlands',
                'feedback': 'The attention to detail was remarkable. From the moment we landed until our departure, everything was seamless. The hot air balloon safari over Masai Mara was breathtaking - a once-in-a-lifetime experience! Thank you Day Safaris for creating such wonderful memories.',
                'starRating': 5
            },
            {
                'name': 'Jennifer Williams',
                'location': 'New York, USA',
                'feedback': 'I\'ve traveled to over 30 countries, and Day Safaris provided one of the best tour experiences I\'ve ever had. Their guides are incredibly knowledgeable about wildlife behavior and local culture. The value for money is outstanding. Five stars isn\'t enough!',
                'starRating': 5
            },
            {
                'name': 'Ahmed & Fatima Khalid',
                'location': 'Dubai, UAE',
                'feedback': 'A seamless and unforgettable safari experience! From the warm welcome to the expertly guided game drives, everything was perfect. The lodge was stunning with amazing views. We\'ll cherish these memories forever.',
                'starRating': 5
            },
            {
                'name': 'Emma Watson',
                'location': 'Toronto, Canada',
                'feedback': 'Best decision we made choosing Day Safaris! Our guide James was incredible - he could spot animals from miles away and shared fascinating insights. The attention to COVID safety protocols was reassuring. Can\'t wait to come back!',
                'starRating': 5
            },
            {
                'name': 'Hans Mueller',
                'location': 'Berlin, Germany',
                'feedback': 'Professional, reliable, and truly passionate about wildlife conservation. The photography tips from our guide were invaluable. We got amazing shots of lions, elephants, and even a leopard! Highly recommend the sunrise game drive.',
                'starRating': 4
            },
            {
                'name': 'Priya Patel',
                'location': 'Mumbai, India',
                'feedback': 'As a solo female traveler, safety was my top concern. Day Safaris made me feel completely secure while delivering an incredible adventure. Met wonderful people and saw breathtaking landscapes. Thank you for the experience of a lifetime!',
                'starRating': 5
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for testimonial_data in testimonials_data:
            testimonial, created = Testimonials.objects.get_or_create(
                name=testimonial_data['name'],
                location=testimonial_data['location'],
                defaults={
                    'feedback': testimonial_data['feedback'],
                    'starRating': testimonial_data['starRating']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created testimonial for: {testimonial.name}'))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  ○ Already exists: {testimonial.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Testimonials seeding complete!\n'
            f'  Testimonials created: {created_count}\n'
            f'  Testimonials skipped: {skipped_count}\n'
            f'  Total testimonials: {Testimonials.objects.count()}'
        ))