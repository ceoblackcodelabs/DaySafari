from django.urls import path

from . import content, views

# Language-prefixed landing pages (/en/kenya-safaris/ ...). Slugs owned by the main site (home, about, contact,
# services, cruises, hotels) are not registered here.
urlpatterns = [path(f"{p['slug']}/", views.page, {'slug': p['slug']}, name=f"landing_{p['slug']}") for p in content.LANDING_PAGES]

# Unprefixed JSON endpoints
api_urlpatterns = [
    path('api/enquiry/', views.enquiry, name='landing_enquiry'),
    path('api/reviews/', views.reviews, name='landing_reviews'),
]
