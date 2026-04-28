# transactions/admin.py
from django.contrib import admin
from .models import MpesaTransaction

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'amount', 'reference', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['phone_number', 'reference', 'mpesa_receipt_number']
    readonly_fields = ['created_at', 'raw_response']

    fieldsets = (
        ('Transaction Details', {
            'fields': ('phone_number', 'amount', 'reference', 'description')
        }),
        ('M-Pesa Response', {
            'fields': ('checkout_request_id', 'merchant_request_id', 'mpesa_receipt_number', 'transaction_date')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'raw_response')
        }),
    )