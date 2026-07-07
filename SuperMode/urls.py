from django.urls import path
from .views import *

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dash'),
    path('invoices/', InvoiceView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='create_invoice'),
    path('invoices/update/<int:pk>/', UpdateInvoiceView.as_view(), name='update_invoice'),
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),

    # employees
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='create_employee'),
    path('employees/update/<int:pk>/', EmployeeUpdateView.as_view(), name='update_employee'),

    # bookings
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/create/', BookingCreateView.as_view(), name='create_booking'),
    path('bookings/update/<int:pk>/', BookingUpdateView.as_view(), name='update_booking'),
    path('bookings/delete/<int:pk>/', BookingDeleteView.as_view(), name='delete_booking'),

    # contact
    path('contacts/', ContactListView.as_view(), name='contact_list'),
    path('contacts/update/<int:pk>/', ContactUpdateView.as_view(), name='update_contact'),
    path('contacts/delete/<int:pk>/', ContactDeleteView.as_view(), name='delete_contact'),
    path('contact/<int:pk>/reply/', ContactReplyView.as_view(), name='reply_contact'),

    # finance
    path('finance/', FinanceDashboardView.as_view(), name='finance_dashboard'),

    # income
    path('finance/income/', IncomeListView.as_view(), name='income_list'),
    path('finance/income/<int:pk>/edit/', IncomeUpdateView.as_view(), name='update_income'),
    path('finance/income/<int:pk>/delete/', IncomeDeleteView.as_view(), name='delete_income'),
    path('finance/income/add/', IncomeCreateView.as_view(), name='add_income'),

    # expense
    path('finance/expense/', ExpenseListView.as_view(), name='expense_list'),
    path('finance/expense/add/', ExpenseCreateView.as_view(), name='add_expense'),
    path('finance/expense/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='update_expense'),
    path('finance/expense/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='delete_expense'),

    # hotels
    path('hotels/', HoteslListView.as_view(), name='hotels_list'),
]