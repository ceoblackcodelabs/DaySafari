from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('income', 'Income'), ('expense', 'Expense')])
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    class Meta:
        verbose_name_plural = 'Categories'


class Income(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('cheque', 'Cheque'),
    ]
    
    source = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'type': 'income'})
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source} - Ksh {self.amount}"
    
    class Meta:
        verbose_name_plural = 'Incomes'
        ordering = ['-date_received']


class Expense(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('cheque', 'Cheque'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_incurred = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'type': 'expense'})
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    vendor = models.CharField(max_length=200, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - Ksh {self.amount}"
    
    class Meta:
        verbose_name_plural = 'Expenses'
        ordering = ['-date_incurred']