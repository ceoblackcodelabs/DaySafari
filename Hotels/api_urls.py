from django.urls import path

from . import api

urlpatterns = [
    path('hotels/schema/', api.schema, name='api_hotels_schema'),
    path('hotels/', api.hotels_collection, name='api_hotels'),
    path('hotels/<slug:slug>/', api.hotel_detail, name='api_hotel_detail'),
    path('hotels/<slug:slug>/photos/', api.hotel_photos, name='api_hotel_photos'),
]
