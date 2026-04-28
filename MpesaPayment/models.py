# Transactions/models.py
from django.db import models

class MpesaTransaction(models.Model):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    raw_response = models.JSONField(default=dict)  # Store complete API response

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - KES {self.amount} - {self.status}"