# management/commands/seed_categories.py
from django.core.management.base import BaseCommand
from FinanceManagement.models import Category

class Command(BaseCommand):
    help = 'Seed finance categories'

    def handle(self, *args, **options):
        categories = [
            # Income Categories
            ('Safari Bookings', 'income'),
            ('Accommodation', 'income'),
            ('Transport', 'income'),
            ('Tour Packages', 'income'),
            ('Consultancy', 'income'),
            ('Other Income', 'income'),
            # Expense Categories
            ('Salaries', 'expense'),
            ('Fuel', 'expense'),
            ('Vehicle Maintenance', 'expense'),
            ('Marketing', 'expense'),
            ('Office Rent', 'expense'),
            ('Utilities', 'expense'),
            ('Equipment', 'expense'),
            ('Park Fees', 'expense'),
            ('Guide Fees', 'expense'),
            ('Other Expense', 'expense'),
        ]
        
        for name, type in categories:
            Category.objects.get_or_create(name=name, type=type)
            self.stdout.write(f'Created category: {name} ({type})')
        
        self.stdout.write(self.style.SUCCESS('Categories seeded successfully!'))