from django.shortcuts import render, redirect
from django.views.generic import (TemplateView, ListView, DetailView, 
                                  CreateView, UpdateView, DeleteView
                                  )
from Invoices.models import Invoice
from django.db.models import Sum
from decimal import Decimal
from django.db import models
from django.urls import reverse_lazy
from django.contrib import messages
from Invoices.forms import InvoiceForm
from datetime import date, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

class AdminDashboardView(ListView):
    template_name = 'Dashboard/index.html'
    model = Invoice
    context_object_name = 'invoices'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Invoice statistics
        context['total_invoices'] = Invoice.objects.count()
        context['paid_invoices'] = Invoice.objects.filter(status='Paid').count()
        context['unpaid_invoices'] = Invoice.objects.filter(status='Unpaid').count()
        context['partial_invoices'] = Invoice.objects.filter(status='Partial').count()
        
        # Financial totals
        context['total_amount'] = Invoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        context['total_paid'] = Invoice.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['total_unpaid'] = context['total_amount'] - context['total_paid']
        
        # Cash flow data for bar chart (Last 6 months)
        from datetime import date, timedelta
        months = []
        cash_in = []
        cash_out = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Calculate cash in (paid invoices for this month)
            month_paid = Invoice.objects.filter(
                status='Paid',
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            cash_in.append(float(month_paid))
            
            # Calculate cash out (expenses - you can adjust this based on your expense model)
            # For now using 60% of cash in as approximate expenses
            cash_out.append(float(month_paid) * 0.6)
        
        context['chart_months'] = months
        context['chart_cash_in'] = cash_in
        context['chart_cash_out'] = cash_out
        
        # Invoice data for area chart (Last 6 months)
        invoice_counts = []
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            count = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).count()
            invoice_counts.append(count)
        
        context['invoice_counts'] = invoice_counts
        
        return context
    
class InvoiceView(ListView):
    template_name = 'Invoices/invoices.html'
    model = Invoice
    context_object_name = 'invoices'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Invoice statistics
        context['total_invoices'] = Invoice.objects.count()
        context['paid_invoices'] = Invoice.objects.filter(status='Paid').count()
        context['unpaid_invoices'] = Invoice.objects.filter(status='Unpaid').count()
        context['partial_invoices'] = Invoice.objects.filter(status='Partial').count()
        
        # Financial totals
        context['total_amount'] = Invoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        context['total_paid'] = Invoice.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['total_unpaid'] = context['total_amount'] - context['total_paid']
        
        # Cash flow data for bar chart (Last 6 months)
        from datetime import date, timedelta
        months = []
        cash_in = []
        cash_out = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Calculate cash in (paid invoices for this month)
            month_paid = Invoice.objects.filter(
                status='Paid',
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            cash_in.append(float(month_paid))
            
            # Calculate cash out (expenses - you can adjust this based on your expense model)
            # For now using 60% of cash in as approximate expenses
            cash_out.append(float(month_paid) * 0.6)
        
        context['chart_months'] = months
        context['chart_cash_in'] = cash_in
        context['chart_cash_out'] = cash_out
        
        # Invoice data for area chart (Last 6 months)
        invoice_counts = []
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            count = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).count()
            invoice_counts.append(count)
        
        context['invoice_counts'] = invoice_counts
        
        return context
    
class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'Invoices/create.html'
    success_url = reverse_lazy('invoice_list')  
    
    def form_valid(self, form):
        # Set the user if logged in
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        
        messages.success(self.request, f'Invoice {form.instance.invoice_number} created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add dashboard data for the metrics cards
        context['dashboard'] = {
            'cash_at_hand': self.get_total_paid_this_month(),
            'cash_at_bank': self.get_total_paid_all_time(),
            'expenses': self.get_total_expenses(),
            'total_sales': self.get_total_invoice_amount(),
        }

        # Add chart data for the line graph
        from datetime import date, timedelta
        
        months = []
        invoiced_amounts = []
        paid_amounts = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Calculate invoiced amount for this month
            month_invoiced = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            invoiced_amounts.append(float(month_invoiced))
            
            # Calculate paid amount for this month
            month_paid = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
            paid_amounts.append(float(month_paid))
        
        context['chart_months'] = months
        context['chart_invoiced_amounts'] = invoiced_amounts
        context['chart_paid_amounts'] = paid_amounts

        return context
    
    def get_total_paid_this_month(self):
        today = date.today()
        total = Invoice.objects.filter(
            status='Paid',
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        return float(total)
    
    def get_total_paid_all_time(self):
        total = Invoice.objects.filter(status='Paid').aggregate(total=models.Sum('amount_paid'))['total'] or 0
        return float(total)
    
    def get_total_expenses(self):
        # This would come from an Expense model - for now using 40% of total paid
        total_paid = self.get_total_paid_all_time()
        return float(total_paid * 0.4)
    
    def get_total_invoice_amount(self):
        total = Invoice.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        return float(total)
    
class UpdateInvoiceView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'Invoices/update.html'
    success_url = reverse_lazy('invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add dashboard data for the metrics cards
        context['dashboard'] = {
            'cash_at_hand': self.get_total_paid_this_month(),
            'cash_at_bank': self.get_total_paid_all_time(),
            'expenses': self.get_total_expenses(),
            'total_sales': self.get_total_invoice_amount(),
        }

        # Add chart data for the line graph
        from datetime import date, timedelta
        
        months = []
        invoiced_amounts = []
        paid_amounts = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Calculate invoiced amount for this month
            month_invoiced = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            invoiced_amounts.append(float(month_invoiced))
            
            # Calculate paid amount for this month
            month_paid = Invoice.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
            paid_amounts.append(float(month_paid))
        
        context['chart_months'] = months
        context['chart_invoiced_amounts'] = invoiced_amounts
        context['chart_paid_amounts'] = paid_amounts

        return context
    
    def get_total_paid_this_month(self):
        today = date.today()
        total = Invoice.objects.filter(
            status='Paid',
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        return float(total)
    
    def get_total_paid_all_time(self):
        total = Invoice.objects.filter(status='Paid').aggregate(total=models.Sum('amount_paid'))['total'] or 0
        return float(total)
    
    def get_total_expenses(self):
        # This would come from an Expense model - for now using 40% of total paid
        total_paid = self.get_total_paid_all_time()
        return float(total_paid * 0.4)
    
    def get_total_invoice_amount(self):
        total = Invoice.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        return float(total)
    

# class Employee
from Office.models import Employee
class EmployeeListView(ListView):
    model = Employee
    template_name = 'Employees/employees.html'
    context_object_name = 'employees'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard summary data
        total_employees = Employee.objects.filter(is_active=True).count()
        total_salary = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0
        
        # Role distribution
        role_counts = {}
        for role_choice in Employee.ROLE_CHOICES:
            role = role_choice[0]
            count = Employee.objects.filter(role=role, is_active=True).count()
            if count > 0:
                role_counts[role] = count
        
        # Department distribution
        dept_counts = {}
        for dept_choice in Employee.DEPT_CHOICES:
            dept = dept_choice[0]
            count = Employee.objects.filter(department=dept, is_active=True).count()
            if count > 0:
                dept_counts[dept] = count
        
        # Monthly hiring trends (last 6 months)
        months = []
        hiring_counts = []
        salary_trends = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Hiring count for this month
            hired_count = Employee.objects.filter(
                hire_date__year=month_date.year,
                hire_date__month=month_date.month
            ).count()
            hiring_counts.append(hired_count)
            
            # New hires salary trend
            new_salaries = Employee.objects.filter(
                hire_date__year=month_date.year,
                hire_date__month=month_date.month
            ).aggregate(total=Sum('salary'))['total'] or 0
            salary_trends.append(float(new_salaries))
        
        context['dashboard'] = {
            'total_employees': total_employees,
            'total_salary': float(total_salary),
            'avg_salary': float(total_salary / total_employees if total_employees > 0 else 0),
            'active_count': total_employees,
            'new_hires': Employee.objects.filter(hire_date__month=date.today().month).count(),
        }
        
        context['role_counts'] = role_counts
        context['dept_counts'] = dept_counts
        context['chart_months'] = months
        context['hiring_counts'] = hiring_counts
        context['salary_trends'] = salary_trends
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['employees'] = context['employees'].filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(role__icontains=search_query)
            )
            context['search_query'] = search_query
        
        return context

from Office.forms import EmployeeForm
class EmployeeCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'Employees/add_employee.html'
    success_url = reverse_lazy('employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Employee {form.instance.name} has been added successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Employee'
        context['button_text'] = 'Add Employee'
        return context


class EmployeeUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'Employees/update_employee.html'
    success_url = reverse_lazy('employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Employee {form.instance.name} has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        total_employees = Employee.objects.filter(is_active=True).count()
        total_salary = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0
        
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit-{self.object.name}'
        context['button_text'] = 'Update Employee'
        context['dashboard'] = {
            'total_employees': total_employees,
            'total_salary': float(total_salary),
            'avg_salary': float(total_salary / total_employees if total_employees > 0 else 0),
            'active_count': total_employees,
            'new_hires': Employee.objects.filter(hire_date__month=date.today().month).count(),
        }
        return context
    

# bookings
from ClientRequests.models import Bookings
class BookingListView(ListView):
    model = Bookings
    template_name = 'Bookings/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard summary data
        total_bookings = Bookings.objects.count()
        pending_bookings = Bookings.objects.filter(date__gte=date.today()).count()
        completed_bookings = Bookings.objects.filter(date__lt=date.today()).count()
        total_persons = Bookings.objects.aggregate(total=Sum('persons'))['total'] or 0
        
        # Monthly booking trends (last 6 months)
        months = []
        booking_counts = []
        persons_trends = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Booking count for this month
            count = Bookings.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).count()
            booking_counts.append(count)
            
            # Persons count for this month
            persons = Bookings.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).aggregate(total=Sum('persons'))['total'] or 0
            persons_trends.append(persons)
        
        # Destinations distribution
        destination_counts = {}
        for booking in Bookings.objects.select_related('destination').all():
            dest_name = booking.destination.name if booking.destination else 'TBD'
            destination_counts[dest_name] = destination_counts.get(dest_name, 0) + 1
        
        context['dashboard'] = {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_persons': total_persons,
        }
        
        context['chart_months'] = months
        context['booking_counts'] = booking_counts
        context['persons_trends'] = persons_trends
        context['destination_counts'] = destination_counts
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['bookings'] = context['bookings'].filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(destination__name__icontains=search_query)
            )
            context['search_query'] = search_query
        
        return context
    
from ClientRequests.forms import SudoBookingsForm
class BookingCreateView(CreateView):
    model = Bookings
    form_class = SudoBookingsForm
    template_name = 'Bookings/create.html'
    success_url = reverse_lazy('booking_list')
    
    def form_valid(self, form):
        # Set the client if user is logged in
        if self.request.user.is_authenticated:
            form.instance.client = self.request.user
        
        messages.success(self.request, f'Booking for {form.instance.name} has been created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Booking'
        context['button_text'] = 'Create Booking'
        
        # Add dashboard data for the metrics cards
        from django.db.models import Sum, Count
        from datetime import date, timedelta
        
        total_bookings = Bookings.objects.count()
        pending_bookings = Bookings.objects.filter(date__gte=date.today()).count()
        completed_bookings = Bookings.objects.filter(date__lt=date.today()).count()
        total_persons = Bookings.objects.aggregate(total=Sum('persons'))['total'] or 0
        
        context['dashboard'] = {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_persons': total_persons,
        }
        
        return context
    
class BookingUpdateView(UpdateView):
    model = Bookings
    form_class = SudoBookingsForm
    template_name = 'Bookings/update_bookings.html'
    success_url = reverse_lazy('booking_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Booking for {form.instance.name} has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Booking - {self.object.name}'
        context['button_text'] = 'Update Booking'
        
        # Add dashboard data for the metrics cards
        from django.db.models import Sum, Count
        from datetime import date, timedelta
        
        total_bookings = Bookings.objects.count()
        pending_bookings = Bookings.objects.filter(date__gte=date.today()).count()
        completed_bookings = Bookings.objects.filter(date__lt=date.today()).count()
        total_persons = Bookings.objects.aggregate(total=Sum('persons'))['total'] or 0
        
        context['dashboard'] = {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_persons': total_persons,
        }
        
        return context
    
class BookingDeleteView(DeleteView):
    model = Bookings
    success_url = reverse_lazy('booking_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        booking_name = self.object.name
        self.object.delete()
        messages.success(request, f'Booking for {booking_name} has been deleted successfully!')
        return redirect(self.success_url)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
    
from ClientRequests.models import Contact
class ContactListView(ListView):
    model = Contact
    template_name = 'Contacts/contacts.html'
    context_object_name = 'contacts'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard summary data
        total_contacts = Contact.objects.count()
        new_contacts = Contact.objects.filter(status='New').count()
        read_contacts = Contact.objects.filter(status='Read').count()
        closed_contacts = Contact.objects.filter(status='Closed').count()
        
        # Monthly contact trends (last 6 months)
        months = []
        total_trends = []
        new_trends = []
        closed_trends = []
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Total contacts for this month
            total = Contact.objects.filter(
                created_at__year=month_date.year,
                created_at__month=month_date.month
            ).count()
            total_trends.append(total)
            
            # New contacts for this month
            new = Contact.objects.filter(
                status='New',
                created_at__year=month_date.year,
                created_at__month=month_date.month
            ).count()
            new_trends.append(new)
            
            # Closed contacts for this month
            closed = Contact.objects.filter(
                status='Closed',
                created_at__year=month_date.year,
                created_at__month=month_date.month
            ).count()
            closed_trends.append(closed)
        
        context['dashboard'] = {
            'total_contacts': total_contacts,
            'new_contacts': new_contacts,
            'read_contacts': read_contacts,
            'closed_contacts': closed_contacts,
        }
        
        context['chart_months'] = months
        context['total_trends'] = total_trends
        context['new_trends'] = new_trends
        context['closed_trends'] = closed_trends
        
        return context
    

from ClientRequests.forms import SudoContactForm    
class ContactUpdateView(UpdateView):
    model = Contact
    form_class = SudoContactForm
    template_name = 'Contacts/update_contact.html'
    success_url = reverse_lazy('contact_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Contact message from {form.instance.name} has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Contact Message'
        context['button_text'] = 'Update Message'
        
        # Dashboard summary data
        total_messages = Contact.objects.count()
        unread_messages = Contact.objects.filter(status='New').count()
        read_messages = Contact.objects.filter(status='Read').count()
        total_responded = Contact.objects.filter(~Q(response='')).count() if hasattr(Contact, 'response') else 0
        
        context['dashboard'] = {
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'read_messages': read_messages,
            'total_responded': total_responded,
        }
        
        return context
    
class ContactDeleteView(DeleteView):
    model = Contact
    success_url = reverse_lazy('contact_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        contact_name = self.object.name
        self.object.delete()
        messages.success(request, f'Contact message from {contact_name} has been deleted successfully!')
        return redirect(self.success_url)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

# Finance Management Views
from FinanceManagement.models import Income, Expense
from FinanceManagement.forms import IncomeForm, ExpenseForm
class FinanceDashboardView(ListView):
    template_name = 'Finance/dashboard.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        return Income.objects.all()  # Default queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Financial Summary
        total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        net_balance = total_income - total_expense
        
        # Monthly trends (last 6 months)
        months = []
        income_trends = []
        expense_trends = []
        
        current_date = timezone.now()
        
        for i in range(5, -1, -1):
            month_date = current_date - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            # Income for this month
            month_income = Income.objects.filter(
                date_received__year=month_date.year,
                date_received__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            income_trends.append(float(month_income))
            
            # Expense for this month
            month_expense = Expense.objects.filter(
                date_incurred__year=month_date.year,
                date_incurred__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            expense_trends.append(float(month_expense))
        
        context['dashboard'] = {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_balance': net_balance,
            'profit_margin': (net_balance / total_income * 100) if total_income > 0 else 0,
        }
        
        context['chart_months'] = months
        context['income_trends'] = income_trends
        context['expense_trends'] = expense_trends
        context['incomes'] = Income.objects.all().order_by('-date_received')[:10]
        context['expenses'] = Expense.objects.all().order_by('-date_incurred')[:10]
        
        # Debug output (check console)
        print(f"Months: {months}")
        print(f"Income Trends: {income_trends}")
        print(f"Expense Trends: {expense_trends}")
        
        return context


class IncomeListView(ListView):
    model = Income
    template_name = 'Finance/incomes.html'
    context_object_name = 'incomes'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Total income
        total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly trends (last 6 months)
        months = []
        income_trends = []
        current_date = timezone.now()
        
        for i in range(5, -1, -1):
            month_date = current_date - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            month_income = Income.objects.filter(
                date_received__year=month_date.year,
                date_received__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            income_trends.append(float(month_income))
        
        # Monthly count
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_income_count = Income.objects.filter(
            date_received__year=current_year,
            date_received__month=current_month
        ).count()
        
        # Average income
        avg_income = total_income / Income.objects.count() if Income.objects.count() > 0 else 0
        
        context['total_income'] = total_income
        context['chart_months'] = months
        context['income_trends'] = income_trends
        context['monthly_income_count'] = monthly_income_count
        context['average_income'] = avg_income
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['incomes'] = context['incomes'].filter(
                Q(source__icontains=search_query) |
                Q(reference_number__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
            context['search_query'] = search_query
        
        return context

class IncomeCreateView(CreateView):
    model = Income
    form_class = IncomeForm
    template_name = 'Finance/income_form.html'
    success_url = reverse_lazy('income_list')
    
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, f'Income from {form.instance.source} has been added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Income'
        context['button_text'] = 'Add Income'
        
        # Dashboard data
        total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        income_count = Income.objects.count()
        
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_income_count = Income.objects.filter(
            date_received__year=current_year,
            date_received__month=current_month
        ).count()
        
        avg_income = total_income / income_count if income_count > 0 else 0
        
        context['total_income'] = total_income
        context['income_count'] = income_count
        context['monthly_income_count'] = monthly_income_count
        context['average_income'] = avg_income
        
        return context



class ExpenseListView(ListView):
    model = Expense
    template_name = 'Finance/expenses.html'
    context_object_name = 'expenses'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Total expense
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly trends (last 6 months)
        months = []
        expense_trends = []
        current_date = timezone.now()
        
        for i in range(5, -1, -1):
            month_date = current_date - timedelta(days=30*i)
            month_name = month_date.strftime('%b %Y')
            months.append(month_name)
            
            month_expense = Expense.objects.filter(
                date_incurred__year=month_date.year,
                date_incurred__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            expense_trends.append(float(month_expense))
        
        # Monthly count
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_expense_count = Expense.objects.filter(
            date_incurred__year=current_year,
            date_incurred__month=current_month
        ).count()
        
        # Average expense
        avg_expense = total_expense / Expense.objects.count() if Expense.objects.count() > 0 else 0
        
        context['total_expense'] = total_expense
        context['chart_months'] = months
        context['expense_trends'] = expense_trends
        context['monthly_expense_count'] = monthly_expense_count
        context['average_expense'] = avg_expense
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['expenses'] = context['expenses'].filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(vendor__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
            context['search_query'] = search_query
        
        return context

class ExpenseCreateView(CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'Finance/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, f'Expense {form.instance.name} has been added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Expense'
        context['button_text'] = 'Add Expense'
        
        # Dashboard data
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        expense_count = Expense.objects.count()
        
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_expense_count = Expense.objects.filter(
            date_incurred__year=current_year,
            date_incurred__month=current_month
        ).count()
        
        avg_expense = total_expense / expense_count if expense_count > 0 else 0
        
        context['total_expense'] = total_expense
        context['expense_count'] = expense_count
        context['monthly_expense_count'] = monthly_expense_count
        context['average_expense'] = avg_expense
        
        return context


class IncomeUpdateView(UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = 'Finance/income_form.html'
    success_url = reverse_lazy('income_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Income has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Income'
        context['button_text'] = 'Update Income'
        return context


class ExpenseUpdateView(UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'Finance/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Expense has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Expense'
        context['button_text'] = 'Update Expense'
        return context


class IncomeDeleteView(DeleteView):
    model = Income
    success_url = reverse_lazy('income_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'Income from {self.object.source} has been deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ExpenseDeleteView(DeleteView):
    model = Expense
    success_url = reverse_lazy('expense_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'Expense {self.object.name} has been deleted successfully!')
        return super().delete(request, *args, **kwargs)