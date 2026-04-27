from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import date, timedelta
from .models import Income, Expense, Category
from .forms import IncomeForm, ExpenseForm, CategoryForm

class FinanceDashboardView(ListView):
    template_name = 'Finance/finance_list.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        # Combine income and expense for display
        incomes = Income.objects.all()
        expenses = Expense.objects.all()
        # You can combine them if needed
        return incomes  # Default return
    
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
        
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
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
        
        # Recent incomes and expenses
        recent_incomes = Income.objects.all().order_by('-date_received')[:5]
        recent_expenses = Expense.objects.all().order_by('-date_incurred')[:5]
        
        context['dashboard'] = {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_balance': net_balance,
            'profit_margin': (net_balance / total_income * 100) if total_income > 0 else 0,
        }
        
        context['chart_months'] = months
        context['income_trends'] = income_trends
        context['expense_trends'] = expense_trends
        context['recent_incomes'] = recent_incomes
        context['recent_expenses'] = recent_expenses
        context['incomes'] = Income.objects.all().order_by('-date_received')[:10]
        context['expenses'] = Expense.objects.all().order_by('-date_incurred')[:10]
        
        return context


class IncomeCreateView(CreateView):
    model = Income
    form_class = IncomeForm
    template_name = 'Finance/income_form.html'
    success_url = reverse_lazy('finance_dashboard')
    
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, f'Income from {form.instance.source} has been added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Income'
        context['button_text'] = 'Add Income'
        return context


class ExpenseCreateView(CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'Finance/expense_form.html'
    success_url = reverse_lazy('finance_dashboard')
    
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, f'Expense {form.instance.name} has been added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Expense'
        context['button_text'] = 'Add Expense'
        return context


class IncomeUpdateView(UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = 'Finance/income_form.html'
    success_url = reverse_lazy('finance_dashboard')
    
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
    success_url = reverse_lazy('finance_dashboard')
    
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
    success_url = reverse_lazy('finance_dashboard')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'Income from {self.object.source} has been deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ExpenseDeleteView(DeleteView):
    model = Expense
    success_url = reverse_lazy('finance_dashboard')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'Expense {self.object.name} has been deleted successfully!')
        return super().delete(request, *args, **kwargs)