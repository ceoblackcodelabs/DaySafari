from django.db import models
from django.utils import timezone

class Employee(models.Model):
    # Employee Roles
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('supervisor', 'Supervisor'),
        ('guide', 'Safari Guide'),
        ('driver', 'Driver'),
        ('office', 'Office Staff'),
        ('accountant', 'Accountant'),
        ('marketing', 'Marketing'),
        ('chef', 'Chef'),
        ('housekeeping', 'Housekeeping'),
        ('employee', 'Employee'),
    ]
    
    # Department Choices
    DEPT_CHOICES = [
        ('management', 'Management'),
        ('operations', 'Operations'),
        ('sales', 'Sales & Marketing'),
        ('accounts', 'Accounts'),
        ('hr', 'Human Resources'),
        ('logistics', 'Logistics'),
    ]
    
    name = models.CharField(default='', max_length=100)
    email = models.EmailField(unique=False, default='email@example.com')
    contact = models.CharField(default='', max_length=20)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='employee')
    department = models.CharField(max_length=50, choices=DEPT_CHOICES, default='operations')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hire_date = models.DateField(default=timezone.now)
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    address = models.TextField(default='', blank=True)
    emergency_contact = models.CharField(default='', max_length=20, blank=True)
    emergency_name = models.CharField(default='', max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.role}"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employee.objects.order_by('id').last()
            if last_employee and last_employee.employee_id:
                try:
                    last_num = int(last_employee.employee_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.employee_id = f"EMP-{timezone.now().year}-{str(new_num).zfill(4)}"
        super().save(*args, **kwargs)