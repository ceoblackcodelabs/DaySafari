from django.urls import path
from .views import (AdminDashboardView, InvoiceView, InvoiceCreateView,
                    UpdateInvoiceView
                    )

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dash'),
    path('invoices/', InvoiceView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='create_invoice'),
    path('invoices/update/<int:pk>/', UpdateInvoiceView.as_view(), name='update_invoice'),
]