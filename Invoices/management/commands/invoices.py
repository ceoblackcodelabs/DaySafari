from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from Invoices.models import Invoice 
from datetime import date, timedelta
from django.db import models
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed invoices into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed invoices...'))
        
        # Get or create default user
        default_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@daysafaris.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Customer names
        customers = [
            'Sarah Thompson', 'David Chen', 'Robert van der Berg', 'Jennifer Williams',
            'Ahmed Khalid', 'Emma Watson', 'Hans Mueller', 'Priya Patel',
            'Michael Otieno', 'Grace Mwangi', 'James Kamau', 'Lisa Anderson',
            'John Mwangi', 'Mary Wanjiku', 'Peter Ochieng', 'Jane Akinyi'
        ]
        
        # Invoice titles and descriptions
        invoice_templates = [
            {
                'title': 'Masai Mara Safari Package',
                'description': '4-day luxury safari experience in Masai Mara National Reserve. Includes game drives, accommodation at Mara Serena Lodge, meals, and park entry fees.'
            },
            {
                'title': 'Zanzibar Beach Holiday',
                'description': '6-day tropical paradise getaway to Zanzibar. Includes beachfront resort, Stone Town tour, spice plantation visit, and sunset dhow cruise.'
            },
            {
                'title': 'Serengeti Migration Safari',
                'description': '5-day wildlife photography safari in Serengeti National Park. Includes luxury tented camp, hot air balloon option, and expert photography guide.'
            },
            {
                'title': 'Amboseli Elephant Experience',
                'description': '3-day family safari to Amboseli National Park. Features elephant encounters with Mount Kilimanjaro backdrop, nature walks, and cultural village visit.'
            },
            {
                'title': 'Mount Kilimanjaro Climb',
                'description': '7-day trekking expedition to summit Africa\'s highest peak via Machame Route. Includes guides, porters, camping equipment, and park fees.'
            },
            {
                'title': 'Gorilla Trekking Adventure',
                'description': '4-day gorilla trekking experience in Bwindi Impenetrable Forest, Uganda. Includes permits, jungle lodge, guide, and community visit.'
            },
            {
                'title': 'Kenya Highlights Safari',
                'description': '7-day combo safari covering Amboseli, Lake Nakuru, and Masai Mara. Includes 4x4 transport, mid-range lodges, meals, and park fees.'
            },
            {
                'title': 'Lake Nakuru Bird Watching Tour',
                'description': '2-day bird watching safari to Lake Nakuru National Park to see millions of flamingos and other bird species.'
            },
            {
                'title': 'Tsavo East Safari Adventure',
                'description': '3-day safari exploring Tsavo East National Park, known for its red elephants and dramatic landscapes.'
            },
            {
                'title': 'Diani Beach Vacation',
                'description': '5-day beach holiday at Diani Beach, Kenya\'s premier coastal destination. Includes resort accommodation, water sports, and excursions.'
            },
            {
                'title': 'Maasai Cultural Experience',
                'description': '1-day immersive cultural tour to a traditional Maasai village. Includes dances, crafts, and authentic cultural learning.'
            },
            {
                'title': 'Helicopter Tour Over Mara',
                'description': '1-hour scenic helicopter flight over Masai Mara during the great migration season.'
            }
        ]
        
        # Invoice data
        invoices_data = [
            # 2025 Invoices
            {
                'customer_name': 'Sarah Thompson',
                'title': 'Masai Mara Safari Package',
                'amount': Decimal('849.00'),
                'amount_paid': Decimal('849.00'),
                'date': date(2025, 1, 15)
            },
            {
                'customer_name': 'David Chen',
                'title': 'Zanzibar Beach Holiday',
                'amount': Decimal('1299.00'),
                'amount_paid': Decimal('649.50'),
                'date': date(2025, 1, 20)
            },
            {
                'customer_name': 'Robert van der Berg',
                'title': 'Serengeti Migration Safari',
                'amount': Decimal('1499.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2025, 2, 5)
            },
            {
                'customer_name': 'Jennifer Williams',
                'title': 'Amboseli Elephant Experience',
                'amount': Decimal('649.00'),
                'amount_paid': Decimal('649.00'),
                'date': date(2025, 2, 10)
            },
            {
                'customer_name': 'Ahmed Khalid',
                'title': 'Mount Kilimanjaro Climb',
                'amount': Decimal('1899.00'),
                'amount_paid': Decimal('569.70'),
                'date': date(2025, 3, 1)
            },
            {
                'customer_name': 'Emma Watson',
                'title': 'Gorilla Trekking Adventure',
                'amount': Decimal('1899.00'),
                'amount_paid': Decimal('1899.00'),
                'date': date(2025, 3, 15)
            },
            {
                'customer_name': 'Michael Otieno',
                'title': 'Kenya Highlights Safari',
                'amount': Decimal('1599.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2025, 4, 1)
            },
            {
                'customer_name': 'Grace Mwangi',
                'title': 'Lake Nakuru Bird Watching Tour',
                'amount': Decimal('350.00'),
                'amount_paid': Decimal('350.00'),
                'date': date(2025, 4, 10)
            },
            {
                'customer_name': 'Hans Mueller',
                'title': 'Tsavo East Safari Adventure',
                'amount': Decimal('450.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2025, 5, 5)
            },
            {
                'customer_name': 'Priya Patel',
                'title': 'Diani Beach Vacation',
                'amount': Decimal('850.00'),
                'amount_paid': Decimal('425.00'),
                'date': date(2025, 5, 20)
            },
            
            # 2026 Invoices
            {
                'customer_name': 'James Kamau',
                'title': 'Maasai Cultural Experience',
                'amount': Decimal('120.00'),
                'amount_paid': Decimal('120.00'),
                'date': date(2026, 1, 5)
            },
            {
                'customer_name': 'Lisa Anderson',
                'title': 'Helicopter Tour Over Mara',
                'amount': Decimal('450.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2026, 1, 15)
            },
            {
                'customer_name': 'John Mwangi',
                'title': 'Masai Mara Safari Package',
                'amount': Decimal('849.00'),
                'amount_paid': Decimal('849.00'),
                'date': date(2026, 2, 1)
            },
            {
                'customer_name': 'Mary Wanjiku',
                'title': 'Zanzibar Beach Holiday',
                'amount': Decimal('1299.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2026, 2, 10)
            },
            {
                'customer_name': 'Peter Ochieng',
                'title': 'Amboseli Elephant Experience',
                'amount': Decimal('649.00'),
                'amount_paid': Decimal('324.50'),
                'date': date(2026, 3, 5)
            },
            {
                'customer_name': 'Jane Akinyi',
                'title': 'Mount Kilimanjaro Climb',
                'amount': Decimal('1899.00'),
                'amount_paid': Decimal('1899.00'),
                'date': date(2026, 3, 20)
            },
            {
                'customer_name': 'Elizabeth Njeri',
                'title': 'Serengeti Migration Safari',
                'amount': Decimal('1499.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2026, 4, 1)
            },
            {
                'customer_name': 'Paul Kimani',
                'title': 'Kenya Highlights Safari',
                'amount': Decimal('1599.00'),
                'amount_paid': Decimal('799.50'),
                'date': date(2026, 4, 10)
            },
            {
                'customer_name': 'Lucy Wambui',
                'title': 'Gorilla Trekking Adventure',
                'amount': Decimal('1899.00'),
                'amount_paid': Decimal('1899.00'),
                'date': date(2026, 4, 15)
            },
            {
                'customer_name': 'Kevin Odhiambo',
                'title': 'Diani Beach Vacation',
                'amount': Decimal('850.00'),
                'amount_paid': Decimal('0.00'),
                'date': date(2026, 4, 20)
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for data in invoices_data:
            # Find the template for title and description
            template = next(
                (t for t in invoice_templates if t['title'] == data['title']),
                {'title': data['title'], 'description': 'Invoice for safari services provided.'}
            )
            
            # Check if invoice already exists
            if Invoice.objects.filter(
                customer_name=data['customer_name'],
                date=data['date'],
                amount=data['amount']
            ).exists():
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  ○ Invoice exists for: {data["customer_name"]}'))
                continue
            
            # Create invoice (invoice_number will be auto-generated by save method)
            invoice = Invoice.objects.create(
                user=default_user,
                customer_name=data['customer_name'],
                invoice_title=template['title'],
                invoice_description=template['description'],
                amount=data['amount'],
                amount_paid=data['amount_paid'],
                date=data['date']
            )
            # Note: status and balance are auto-calculated in save() method
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Created: {invoice.invoice_number} - {invoice.customer_name} '
                f'({invoice.status}, Balance: Ksh {invoice.balance})'
            ))
        
        # Summary statistics
        total_invoices = Invoice.objects.count()
        total_amount = Invoice.objects.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        total_paid = Invoice.objects.aggregate(total=models.Sum('amount_paid'))['total'] or Decimal('0.00')
        total_balance = total_amount - total_paid
        
        paid_count = Invoice.objects.filter(status='Paid').count()
        partial_count = Invoice.objects.filter(status='Partial').count()
        unpaid_count = Invoice.objects.filter(status='Unpaid').count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Invoices created: {created_count}\n'
            f'  Invoices skipped: {skipped_count}\n'
            f'  Total invoices: {total_invoices}\n'
            f'\n📊 Financial Summary:\n'
            f'  Total Amount: Ksh {total_amount:,.2f}\n'
            f'  Total Paid: Ksh {total_paid:,.2f}\n'
            f'  Total Balance: Ksh {total_balance:,.2f}\n'
            f'\n📈 Status Breakdown:\n'
            f'  Paid: {paid_count} invoices\n'
            f'  Partial: {partial_count} invoices\n'
            f'  Unpaid: {unpaid_count} invoices'
        ))