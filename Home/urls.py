from django.urls import path
from . import guides
from .views import (BrochureView, HomeView, AboutView, ServicesView, ServiceDetailView,
                    CruisesView, AirLineView, BlogsView, GalleryView,
                    AfricanWildLifeToursView, TravelPartnershipsView, HolidayTailorMadeToursView, AirportTransfersView,
                    BlogDetailView, TanzaniaTrekking, KenyaTrekking, KilimanjaroTrekking, SuswaTrekking, LongonotTrekking,
                    TrekkingDetailView, MeruTrekking, FAQView, LegalPageView, SitemapPageView
                    )

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('legal-notice/', LegalPageView.as_view(template_name='Legal/legal_notice.html'), name='legal_notice'),
    path('privacy-policy/', LegalPageView.as_view(template_name='Legal/privacy_policy.html'), name='privacy_policy'),
    path('terms-and-conditions/', LegalPageView.as_view(template_name='Legal/terms.html'), name='terms_and_conditions'),
    path('cookie-policy/', LegalPageView.as_view(template_name='Legal/cookie_policy.html'), name='cookie_policy'),
    path('site-map/', SitemapPageView.as_view(), name='sitemap_page'),

    # services
    path('services/', ServicesView.as_view(), name='services'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('guides/<slug:slug>/', guides.guide_detail, name='guide_detail'),
    path('guides/<slug:slug>/lead/', guides.guide_lead, name='guide_lead'),
    path('guides/<slug:slug>/edit/', guides.guide_edit, name='guide_edit'),
    path('guides/<slug:slug>/photo/', guides.guide_photo, name='guide_photo'),
    path('guides/<slug:slug>/analytics/', guides.guide_analytics, name='guide_analytics'),
    path('guides/<slug:slug>/leads/<int:pk>/status/', guides.guide_lead_status, name='guide_lead_status'),
    path('african-wildlife-tours/', AfricanWildLifeToursView.as_view(), name='african_wildlife_tours'),
    path('travel-partnerships/', TravelPartnershipsView.as_view(), name='travel_partnerships'),
    path('holiday-tailor-made-tours/', HolidayTailorMadeToursView.as_view(), name='holiday_tailor_made_tours'),
    path('airport-transfers/', AirportTransfersView.as_view(), name='airport_transfers'),

    path('cruises/', CruisesView.as_view(), name='cruises'),
    path('airline/', AirLineView.as_view(), name='airline'),
    path('gallery/', GalleryView.as_view(), name='gallary'),

    # blogs
    path('blog/', BlogsView.as_view(), name='blog'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),

    path('brochures/', BrochureView.as_view(), name='brochures'),

    path("trekking/Mt-Kenya/", KenyaTrekking.as_view(), name="trekking_kenya"),
    path("trekking/Mt-Longonot/", LongonotTrekking.as_view(), name="trekking_longonot"),
    path("trekking/Mt-Suswa/", SuswaTrekking.as_view(), name="trekking_suswa"),
    path("trekking/Mt-Kilimanjaro/", KilimanjaroTrekking.as_view(), name="trekking_kilimanjaro"),
    path("trekking/Mt-Meru/", MeruTrekking.as_view(), name="trekking_meru"),
    path("trekking/Mt-Trekking/<int:pk>/", TrekkingDetailView.as_view(), name="kili_detail"),
]