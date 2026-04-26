from django.shortcuts import render
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
from datetime import date

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