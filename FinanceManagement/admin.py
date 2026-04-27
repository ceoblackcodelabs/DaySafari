from django.contrib import admin
from django.db import models
from .models import Category, Income, Expense

class IncomeInline(admin.TabularInline):
    model = Income
    extra = 0
    fields = ['source', 'amount', 'payment_method', 'date_received']
    readonly_fields = ['date_received']
    can_delete = False
    max_num = 5

class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    fields = ['name', 'amount', 'payment_method', 'date_incurred']
    readonly_fields = ['date_incurred']
    can_delete = False
    max_num = 5

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'total_income', 'total_expense']
    list_filter = ['type']
    search_fields = ['name']
    
    def total_income(self, obj):
        if obj.type == 'income':
            total = Income.objects.filter(category=obj).aggregate(total=models.Sum('amount'))['total'] or 0
            return f'Ksh {total:,.2f}'
        return '-'
    total_income.short_description = 'Total Income'
    
    def total_expense(self, obj):
        if obj.type == 'expense':
            total = Expense.objects.filter(category=obj).aggregate(total=models.Sum('amount'))['total'] or 0
            return f'Ksh {total:,.2f}'
        return '-'
    total_expense.short_description = 'Total Expense'

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['source', 'amount_formatted', 'category', 'payment_method', 'date_received']
    list_filter = ['category', 'payment_method', 'date_received']
    search_fields = ['source', 'reference_number']
    date_hierarchy = 'date_received'
    
    def amount_formatted(self, obj):
        return f'Ksh {obj.amount:,.2f}'
    amount_formatted.short_description = 'Amount'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount_formatted', 'category', 'payment_method', 'date_incurred', 'vendor']
    list_filter = ['category', 'payment_method', 'date_incurred']
    search_fields = ['name', 'description', 'vendor']
    date_hierarchy = 'date_incurred'
    
    def amount_formatted(self, obj):
        return f'Ksh {obj.amount:,.2f}'
    amount_formatted.short_description = 'Amount'