from django.urls import path
from .views import (
    AirBNBView, AirBNBDetailView
)

urlpatterns = [
    # airbnb
    path('airbnb/', AirBNBView.as_view(), name='airbnb'),
    path('airbnb/<int:pk>/', AirBNBDetailView.as_view(), name='bnb_detail'),
]
