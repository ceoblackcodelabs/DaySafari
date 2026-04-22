from django.contrib import admin
from .models import (
    Employee
)
# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'contact', 'role', 'salary']
    list_filter = ['role']
    search_fields = ['name', 'email', 'contact']
