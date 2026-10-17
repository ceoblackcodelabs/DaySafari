from django.urls import path

from . import api
from Home import blogs_api, offers_api
from Places import packages_api

urlpatterns = [
    path('blogs/schema/', blogs_api.blogs_schema, name='api_blogs_schema'),
    path('blogs/', blogs_api.blogs_collection, name='api_blogs'),
    path('blogs/<slug:slug>/', blogs_api.blog_detail, name='api_blog_detail'),
    path('blogs/<slug:slug>/image/', blogs_api.blog_image, name='api_blog_image'),
    path('offers/schema/', offers_api.offers_schema, name='api_offers_schema'),
    path('offers/', offers_api.offers_collection, name='api_offers'),
    path('offers/<int:pk>/', offers_api.offer_detail, name='api_offer_detail'),
    path('offers/<int:pk>/image/', offers_api.offer_image, name='api_offer_image'),
    path('packages/', packages_api.packages_collection, name='api_packages'),
    path('packages/<slug:slug>/', packages_api.package_detail, name='api_package_detail'),
    path('hotels/schema/', api.schema, name='api_hotels_schema'),
    path('hotels/', api.hotels_collection, name='api_hotels'),
    path('hotels/<slug:slug>/', api.hotel_detail, name='api_hotel_detail'),
    path('hotels/<slug:slug>/photos/', api.hotel_photos, name='api_hotel_photos'),
]
