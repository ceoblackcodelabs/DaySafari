from django.urls import path

from . import api
from Home import offers_api

urlpatterns = [
    path('offers/schema/', offers_api.offers_schema, name='api_offers_schema'),
    path('offers/', offers_api.offers_collection, name='api_offers'),
    path('offers/<int:pk>/', offers_api.offer_detail, name='api_offer_detail'),
    path('offers/<int:pk>/image/', offers_api.offer_image, name='api_offer_image'),
    path('hotels/schema/', api.schema, name='api_hotels_schema'),
    path('hotels/', api.hotels_collection, name='api_hotels'),
    path('hotels/<slug:slug>/', api.hotel_detail, name='api_hotel_detail'),
    path('hotels/<slug:slug>/photos/', api.hotel_photos, name='api_hotel_photos'),
]
