from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from Office.models import Employee
from datetime import date, timedelta
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed employees into the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed employees...'))
        
        # Kenyan names for employees
        first_names = [
            'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Joseph', 'Thomas', 'Charles', 'Christopher',
            'Mary', 'Patricia', 'Jennifer', 'Elizabeth', 'Linda', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
            'Peter', 'Paul', 'George', 'Kenneth', 'Steven', 'Edward', 'Brian', 'Ronald', 'Anthony', 'Kevin',
            'Grace', 'Ann', 'Alice', 'Catherine', 'Rose', 'Jane', 'Margaret', 'Ruth', 'Esther', 'Lucy'
        ]
        
        last_names = [
            'Mwangi', 'Otieno', 'Kimani', 'Omondi', 'Wanjiku', 'Kamau', 'Ochieng', 'Njeri', 'Kipchoge', 'Chebet',
            'Maina', 'Ndirangu', 'Wambui', 'Odhiambo', 'Akinyi', 'Mutua', 'Njuguna', 'Chepkoech', 'Korir', 'Atieno'
        ]
        
        # Email domains
        email_domains = ['daysafaris.co.ke', 'daysafarisadventures.co.ke', 'safari.com']
        
        # Roles with typical salaries
        role_salaries = {
            'manager': (80000, 150000),
            'supervisor': (50000, 80000),
            'guide': (35000, 60000),
            'driver': (30000, 50000),
            'office': (25000, 45000),
            'accountant': (40000, 70000),
            'marketing': (35000, 65000),
            'chef': (25000, 45000),
            'housekeeping': (15000, 30000),
            'employee': (20000, 40000),
        }
        
        # Department based on role
        role_dept = {
            'manager': 'management',
            'supervisor': 'management',
            'guide': 'operations',
            'driver': 'operations',
            'office': 'operations',
            'accountant': 'accounts',
            'marketing': 'sales',
            'chef': 'logistics',
            'housekeeping': 'logistics',
            'employee': 'operations',
        }
        
        # Phone prefixes
        phone_prefixes = ['0712', '0722', '0733', '0744', '0755', '0766', '0777', '0788', '0799']
        
        employees_data = [
            # Management
            {'name': 'James Mwangi', 'role': 'manager', 'salary': 120000, 'hire_date': date(2025, 1, 15)},
            {'name': 'Grace Wanjiku', 'role': 'manager', 'salary': 110000, 'hire_date': date(2025, 3, 10)},
            {'name': 'Peter Otieno', 'role': 'supervisor', 'salary': 75000, 'hire_date': date(2025, 6, 5)},
            
            # Safari Guides
            {'name': 'David Kimani', 'role': 'guide', 'salary': 55000, 'hire_date': date(2025, 2, 20)},
            {'name': 'Joseph Omondi', 'role': 'guide', 'salary': 52000, 'hire_date': date(2025, 4, 12)},
            {'name': 'Michael Ndirangu', 'role': 'guide', 'salary': 60000, 'hire_date': date(2025, 7, 8)},
            {'name': 'Robert Kipchoge', 'role': 'guide', 'salary': 58000, 'hire_date': date(2026, 1, 15)},
            {'name': 'William Chebet', 'role': 'guide', 'salary': 53000, 'hire_date': date(2026, 3, 20)},
            {'name': 'Thomas Korir', 'role': 'guide', 'salary': 56000, 'hire_date': date(2026, 6, 10)},
            
            # Drivers
            {'name': 'Paul Odhiambo', 'role': 'driver', 'salary': 45000, 'hire_date': date(2025, 5, 18)},
            {'name': 'George Akinyi', 'role': 'driver', 'salary': 42000, 'hire_date': date(2025, 8, 22)},
            {'name': 'Kenneth Maina', 'role': 'driver', 'salary': 48000, 'hire_date': date(2026, 2, 14)},
            {'name': 'Steven Mutua', 'role': 'driver', 'salary': 40000, 'hire_date': date(2026, 5, 5)},
            
            # Office Staff
            {'name': 'Mary Njeri', 'role': 'office', 'salary': 40000, 'hire_date': date(2025, 9, 1)},
            {'name': 'Elizabeth Wambui', 'role': 'office', 'salary': 38000, 'hire_date': date(2025, 11, 15)},
            {'name': 'Susan Chepkoech', 'role': 'office', 'salary': 42000, 'hire_date': date(2026, 4, 8)},
            {'name': 'Linda Atieno', 'role': 'office', 'salary': 35000, 'hire_date': date(2026, 7, 12)},
            
            # Accountants
            {'name': 'Charles Njuguna', 'role': 'accountant', 'salary': 65000, 'hire_date': date(2025, 10, 10)},
            {'name': 'Sarah Kamau', 'role': 'accountant', 'salary': 60000, 'hire_date': date(2026, 1, 25)},
            
            # Marketing
            {'name': 'Brian Ochieng', 'role': 'marketing', 'salary': 60000, 'hire_date': date(2025, 12, 5)},
            {'name': 'Jennifer Akinyi', 'role': 'marketing', 'salary': 55000, 'hire_date': date(2026, 3, 18)},
            
            # Chefs
            {'name': 'Anthony Chebet', 'role': 'chef', 'salary': 40000, 'hire_date': date(2025, 7, 20)},
            {'name': 'Ruth Wambui', 'role': 'chef', 'salary': 38000, 'hire_date': date(2026, 2, 28)},
            
            # Housekeeping
            {'name': 'Lucy Wangari', 'role': 'housekeeping', 'salary': 25000, 'hire_date': date(2025, 8, 15)},
            {'name': 'Jane Muthoni', 'role': 'housekeeping', 'salary': 28000, 'hire_date': date(2026, 4, 22)},
            {'name': 'Margaret Wanjiru', 'role': 'housekeeping', 'salary': 26000, 'hire_date': date(2026, 6, 30)},
            
            # Regular Employees
            {'name': 'Edward Maina', 'role': 'employee', 'salary': 35000, 'hire_date': date(2026, 5, 12)},
            {'name': 'Ronald Otieno', 'role': 'employee', 'salary': 32000, 'hire_date': date(2026, 7, 8)},
            {'name': 'Anthony Kimani', 'role': 'employee', 'salary': 30000, 'hire_date': date(2026, 8, 15)},
            {'name': 'Kevin Odhiambo', 'role': 'employee', 'salary': 28000, 'hire_date': date(2026, 9, 20)},
            {'name': 'Brian Omondi', 'role': 'employee', 'salary': 34000, 'hire_date': date(2026, 10, 5)},
            {'name': 'Catherine Wanjiku', 'role': 'employee', 'salary': 36000, 'hire_date': date(2026, 11, 10)},
            {'name': 'Rose Akinyi', 'role': 'employee', 'salary': 33000, 'hire_date': date(2025, 1, 8)},
            {'name': 'Esther Chebet', 'role': 'employee', 'salary': 31000, 'hire_date': date(2025, 2, 15)},
            {'name': 'Lucy Korir', 'role': 'employee', 'salary': 29000, 'hire_date': date(2025, 3, 20)},
            {'name': 'Alice Muthoni', 'role': 'employee', 'salary': 37000, 'hire_date': date(2025, 4, 5)},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for data in employees_data:
            # Generate email
            name_parts = data['name'].lower().split()
            email = f"{name_parts[0]}.{name_parts[1]}@{random.choice(email_domains)}"
            
            # Generate phone number
            phone = f"{random.choice(phone_prefixes)}{random.randint(100000, 999999)}"
            
            # Get department based on role
            department = role_dept.get(data['role'], 'operations')
            
            # Generate emergency contact
            emergency_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            emergency_phone = f"{random.choice(phone_prefixes)}{random.randint(100000, 999999)}"
            
            # Check if employee already exists
            if Employee.objects.filter(name=data['name'], email=email).exists():
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  ○ Employee exists: {data["name"]}'))
                continue
            
            # Create employee
            employee = Employee.objects.create(
                name=data['name'],
                email=email,
                contact=phone,
                role=data['role'],
                department=department,
                salary=Decimal(data['salary']),
                hire_date=data['hire_date'],
                is_active=True,
                address=f"{data['name'].split()[1]} Street, Nairobi, Kenya",
                emergency_name=emergency_name,
                emergency_contact=emergency_phone
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Created: {employee.employee_id} - {employee.name} ({employee.role}) - Ksh {employee.salary:,.2f}'
            ))
        
        # Summary statistics
        total_employees = Employee.objects.count()
        total_salary = Employee.objects.aggregate(total=models.Sum('salary'))['total'] or 0
        avg_salary = total_salary / total_employees if total_employees > 0 else 0
        
        active_count = Employee.objects.filter(is_active=True).count()
        inactive_count = Employee.objects.filter(is_active=False).count()
        
        # Role breakdown
        role_breakdown = {}
        for role_choice in Employee.ROLE_CHOICES:
            role = role_choice[0]
            count = Employee.objects.filter(role=role).count()
            if count > 0:
                role_breakdown[role] = count
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Employees created: {created_count}\n'
            f'  Employees skipped: {skipped_count}\n'
            f'  Total employees: {total_employees}\n'
            f'\n📊 Salary Summary:\n'
            f'  Total Monthly Salary: Ksh {total_salary:,.2f}\n'
            f'  Average Salary: Ksh {avg_salary:,.2f}\n'
            f'\n📈 Status Breakdown:\n'
            f'  Active: {active_count} employees\n'
            f'  Inactive: {inactive_count} employees\n'
            f'\n👥 Role Breakdown:'
        ))
        
        for role, count in role_breakdown.items():
            self.stdout.write(f'  • {role.title()}: {count} employees')

# Add models import at the top
from django.db import models