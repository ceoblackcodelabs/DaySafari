# seed_finance_detailed.py - Fixed with timezone-aware dates
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from FinanceManagement.models import Income, Expense, Category
from datetime import timedelta
import random
from decimal import Decimal
from django.db import models

class Command(BaseCommand):
    help = 'Seed detailed finance records for safari company'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed detailed finance records...'))
        
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@daysafaris.com', 'is_staff': True, 'is_superuser': True}
        )
        
        # Create categories if not exist
        income_cats = [
            ('Masai Mara Safaris', 'income'), ('Serengeti Tours', 'income'),
            ('Zanzibar Packages', 'income'), ('Mountain Climbing', 'income'),
            ('Accommodation Bookings', 'income'), ('Transport Services', 'income'),
            ('Consultation Fees', 'income'), ('Other Income', 'income')
        ]
        
        expense_cats = [
            ('Staff Salaries', 'expense'), ('Fuel & Transport', 'expense'),
            ('Vehicle Maintenance', 'expense'), ('Marketing & Ads', 'expense'),
            ('Office Operations', 'expense'), ('Park & Entry Fees', 'expense'),
            ('Guide Payments', 'expense'), ('Equipment', 'expense'),
            ('Insurance', 'expense'), ('Taxes', 'expense'), ('Other Expenses', 'expense')
        ]
        
        categories = {}
        for name, cat_type in income_cats + expense_cats:
            cat, _ = Category.objects.get_or_create(name=name, type=cat_type)
            categories[name] = cat
        
        # Monthly income data (realistic seasonality)
        monthly_income = {
            'Jan': [120000, 150000, 180000],
            'Feb': [130000, 160000, 190000],
            'Mar': [140000, 170000, 200000],
            'Apr': [80000, 100000, 120000],
            'May': [75000, 95000, 115000],
            'Jun': [200000, 250000, 300000],
            'Jul': [250000, 300000, 350000],
            'Aug': [280000, 330000, 380000],
            'Sep': [260000, 310000, 360000],
            'Oct': [220000, 270000, 320000],
            'Nov': [100000, 130000, 160000],
            'Dec': [180000, 220000, 260000]
        }
        
        # Seed income for last 12 months
        income_created = 0
        current_date = timezone.now()
        
        for month_offset in range(11, -1, -1):
            month_date = current_date - timedelta(days=30*month_offset)
            month_name = month_date.strftime('%b')
            
            base_range = monthly_income.get(month_name, [100000, 150000, 200000])
            
            num_entries = random.randint(2, 4)
            for i in range(num_entries):
                amount = Decimal(random.uniform(base_range[0], base_range[2]))
                
                if i % 3 == 0:
                    category = categories.get('Masai Mara Safaris')
                    source = f"Masai Mara Safari - Booking {random.randint(100, 999)}"
                elif i % 3 == 1:
                    category = categories.get('Zanzibar Packages')
                    source = f"Zanzibar Beach Holiday - Guest {random.randint(100, 999)}"
                else:
                    category = categories.get('Serengeti Tours')
                    source = f"Serengeti Migration Tour - Group {random.randint(100, 999)}"
                
                # Make date timezone-aware
                random_day = random.randint(1, 28)
                naive_date = month_date.replace(day=random_day)
                aware_date = timezone.make_aware(naive_date) if timezone.is_naive(naive_date) else naive_date
                
                Income.objects.create(
                    source=source,
                    amount=amount,
                    date_received=aware_date,
                    category=category,
                    payment_method=random.choice(['mpesa', 'bank', 'card']),
                    reference_number=f"INV-{month_date.year}-{random.randint(1000, 9999)}",
                    created_by=admin_user
                )
                income_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {income_created} income records'))
        
        # Seed expenses
        expense_created = 0
        
        fixed_expenses = [
            ('Staff Salaries', 250000, 'Monthly salaries for all staff'),
            ('Office Rent', 50000, 'Monthly office rent in Nairobi'),
            ('Vehicle Maintenance', 30000, 'Monthly vehicle servicing'),
            ('Marketing', 40000, 'Monthly advertising budget'),
        ]
        
        variable_expenses = [
            ('Fuel & Transport', [15000, 25000, 35000]),
            ('Park & Entry Fees', [10000, 20000, 30000]),
            ('Guide Payments', [20000, 30000, 40000]),
            ('Equipment', [5000, 10000, 15000]),
            ('Insurance', [15000, 20000, 25000]),
        ]
        
        for month_offset in range(11, -1, -1):
            month_date = current_date - timedelta(days=30*month_offset)
            
            # Create fixed expenses
            for name, amount, desc in fixed_expenses:
                random_day = random.randint(1, 10)
                naive_date = month_date.replace(day=random_day)
                aware_date = timezone.make_aware(naive_date) if timezone.is_naive(naive_date) else naive_date
                
                Expense.objects.create(
                    name=name,
                    description=f"{desc} for {month_date.strftime('%B %Y')}",
                    amount=Decimal(amount),
                    date_incurred=aware_date,
                    category=categories.get(name),
                    payment_method='bank',
                    vendor='Various',
                    created_by=admin_user
                )
                expense_created += 1
            
            # Create variable expenses
            for name, amount_range in variable_expenses:
                amount = Decimal(random.uniform(amount_range[0], amount_range[2]))
                random_day = random.randint(10, 28)
                naive_date = month_date.replace(day=random_day)
                aware_date = timezone.make_aware(naive_date) if timezone.is_naive(naive_date) else naive_date
                
                Expense.objects.create(
                    name=name,
                    description=f"{name} for {month_date.strftime('%B %Y')}",
                    amount=amount,
                    date_incurred=aware_date,
                    category=categories.get(name.split()[0] if '&' in name else name),
                    payment_method=random.choice(['mpesa', 'cash', 'card']),
                    vendor=random.choice(['Total Energies', 'KWS', 'Independent', 'Various']),
                    created_by=admin_user
                )
                expense_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {expense_created} expense records'))
        
        # Summary
        total_income = Income.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        net_balance = total_income - total_expense
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Income records: {Income.objects.count()}\n'
            f'  Expense records: {Expense.objects.count()}\n'
            f'\n💰 Financial Summary:\n'
            f'  Total Income: Ksh {total_income:,.2f}\n'
            f'  Total Expense: Ksh {total_expense:,.2f}\n'
            f'  Net Profit: Ksh {net_balance:,.2f}\n'
            f'  Profit Margin: {(net_balance/total_income*100) if total_income > 0 else 0:.1f}%'
        ))