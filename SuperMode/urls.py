from django.urls import path
from .views import (AdminDashboardView, InvoiceView, InvoiceCreateView,
                    UpdateInvoiceView, EmployeeListView, EmployeeCreateView, EmployeeUpdateView,
                    BookingListView, BookingCreateView, BookingUpdateView, BookingDeleteView
                    )

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dash'),
    path('invoices/', InvoiceView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='create_invoice'),
    path('invoices/update/<int:pk>/', UpdateInvoiceView.as_view(), name='update_invoice'),

    # employees
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='create_employee'),
    path('employees/update/<int:pk>/', EmployeeUpdateView.as_view(), name='update_employee'),

    # bookings
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/create/', BookingCreateView.as_view(), name='create_booking'),
    path('bookings/update/<int:pk>/', BookingUpdateView.as_view(), name='update_booking'),
    path('bookings/delete/<int:pk>/', BookingDeleteView.as_view(), name='delete_booking'),
]