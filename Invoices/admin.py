from django.contrib import admin
from .models import Invoice
from django.db import models

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'amount', 'amount_paid', 'balance', 'status', 'date']
    list_filter = ['status', 'date']
    search_fields = ['invoice_number', 'customer_name']
    list_editable = ['status']
    readonly_fields = ['balance']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'customer_name', 'date')
        }),
        ('Financial Details', {
            'fields': ('amount', 'amount_paid', 'status', 'balance')
        }),
        ('User Information', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )
    
    def balance(self, obj):
        balance = obj.amount - obj.amount_paid
        return f"${balance:,.2f}"
    balance.short_description = 'Remaining Balance'
    
    actions = ['mark_as_paid', 'mark_as_unpaid', 'mark_as_partial']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='Paid', amount_paid=models.F('amount'))
        self.message_user(request, f'{updated} invoice(s) marked as paid.')
    mark_as_paid.short_description = 'Mark selected invoices as Paid'
    
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(status='Unpaid', amount_paid=0)
        self.message_user(request, f'{updated} invoice(s) marked as unpaid.')
    mark_as_unpaid.short_description = 'Mark selected invoices as Unpaid'
    
    def mark_as_partial(self, request, queryset):
        updated = queryset.update(status='Partial')
        self.message_user(request, f'{updated} invoice(s) marked as partial payment.')
    mark_as_partial.short_description = 'Mark selected invoices as Partial Payment'