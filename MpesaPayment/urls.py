# transactions/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_page, name='payment_page'),
    path('stk-push/', views.InitiateSTKPush.as_view(), name='initiate_stk_push'),
    path('callback/', views.stk_push_callback, name='stk_push_callback'),
    path('transaction/<int:transaction_id>/', views.TransactionStatusView.as_view(), name='transaction_status'),
    path('simulate-success/<int:transaction_id>/', views.simulate_success, name='simulate_success'),
]