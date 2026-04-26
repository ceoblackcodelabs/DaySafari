from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=20, default='INV-0001')
    invoice_title = models.CharField(max_length=100, default='Invoice')
    invoice_description = models.TextField(blank=True, default='Invoice description goes here.')
    customer_name = models.CharField(max_length=100, default='John Doe')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='Unpaid', choices=[
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
    ])
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Calculate balance and update status before saving
        self.balance = self.amount - self.amount_paid
        if self.balance <= 0:
            self.status = 'Paid'
        elif self.amount_paid > 0:
            self.status = 'Partial'
        else:
            self.status = 'Unpaid'

        # random invoice number generation
        if not self.invoice_number or self.invoice_number == 'INV-0001':
            last_invoice = Invoice.objects.order_by('id').last()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.invoice_number = f"INV-{timezone.now().year}-{new_number:04d}"
        super().save(*args, **kwargs)