from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'name', 'email', 'contact', 'role', 'department', 'salary', 'hire_date', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['name', 'email', 'contact', 'employee_id']
    list_editable = ['salary']
    readonly_fields = ['employee_id']
    
    actions = ['activate_employees', 'deactivate_employees']
    
    def activate_employees(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} employee(s) activated.')
    activate_employees.short_description = 'Activate selected employees'
    
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} employee(s) deactivated.')
    deactivate_employees.short_description = 'Deactivate selected employees'