from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, FormView
from EmailSetup.utils import send_booking_confirmation, handle_new_lead
from Places.models import AwesomePackages, Destinations
from django.utils import timezone
from time import sleep
from .models import (
    Bookings, Contact
)
from Home.models import Brochure
from .forms import (
    BookingsForm, ContactForm
)
from .antispam import AntiSpamViewMixin
import threading

def send_emails_async(booking):
    """Confirmation to the client (notify_staff_of_lead has its own thread)."""
    send_booking_confirmation(booking)

# Create your views here.
class BookingCreateView(AntiSpamViewMixin, CreateView):
    antispam_scope = 'booking'
    model = Bookings
    form_class = BookingsForm
    template_name = 'Requests/booking.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        # Set the client if user is logged in
        if self.request.user.is_authenticated:
            form.instance.client = self.request.user

        response = super().form_valid(form)

        # Add success message
        messages.success(self.request,
            _("Thank you %(name)s! Your booking request has been submitted successfully. "
              "We will contact you within 24 hours to confirm your safari.") % {'name': form.cleaned_data['name']}
        )

        # Send emails in background thread (non-blocking)
        handle_new_lead(self.object, send_booking_confirmation)

        return response

    def form_invalid(self, form):
        if form.spam_detected:
            return super().form_invalid(form)  # AntiSpamViewMixin: strike + 400
        # Add error message
        messages.error(self.request,
            _("There was an error with your booking. Please check the form and try again.")
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Book Your Safari Adventure'
        context['destinations'] = Destinations.objects.all()[:5]
        context['packages'] = AwesomePackages.objects.all()[:3]

        # Pre-fill form for logged-in users (never replace a submitted form,
        # or its validation errors would be lost)
        if self.request.user.is_authenticated and not self.request.POST:
            initial = {
                'name': f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username,
                'email': self.request.user.email,
            }
            context['form'] = BookingsForm(initial={**self.get_initial(), **initial})

        return context

class BookingDetailView(DetailView):
    model = Bookings
    context_object_name = 'booking'
    template_name = 'bookings/booking_detail.html'

# contact views
class ContactView(AntiSpamViewMixin, FormView):
    antispam_scope = 'contact'
    template_name = 'Requests/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        # Save the contact message with commit=False
        contact = form.save(commit=False)

        # Check if user is logged in and associate with the contact
        if self.request.user.is_authenticated:
            contact.client = self.request.user

            # Auto-fill name and email from user profile if fields are empty
            if not contact.name and self.request.user.get_full_name():
                contact.name = self.request.user.get_full_name()
            elif not contact.name:
                contact.name = self.request.user.username

            if not contact.email and self.request.user.email:
                contact.email = self.request.user.email
        else:
            contact.user = None

        # Save first: the lead must never be lost because an email failed
        contact.save()

        # No automatic reply to the submitted address (it is unverified; bots abuse it).
        handle_new_lead(contact)

        # Add success message
        messages.success(self.request,
            _("Thank you %(name)s! Your message has been sent successfully. "
              "We will get back to you within 24 hours.") % {'name': contact.name}
        )

        # Optional: Send email notification
        # self.send_notification_email(contact)

        return super().form_valid(form)

    def form_invalid(self, form):
        if form.spam_detected:
            return super().form_invalid(form)  # AntiSpamViewMixin: strike + 400
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pre-populate form if user is logged in
        if self.request.user.is_authenticated and not self.request.POST:
            initial_data = {
                'name': self.request.user.get_full_name() or self.request.user.username,
                'email': self.request.user.email,
            }
            context['form'] = self.form_class(initial=initial_data)

        context['brochures'] = Brochure.objects.all()[:3]
        context['title'] = 'Contact Us - Day Safaris Adventures'
        context['user'] = self.request.user

        return context

# ---------------------------------------------------------------------------
# "What's your next adventure?" popup: save the lead; the browser opens WhatsApp itself
# ---------------------------------------------------------------------------
import re as _re
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .antispam import rate_limited, get_client_ip, add_strike, lead_spam_reasons, trap
from .models import QuickLead


def _wa_phone(value):
    digits = _re.sub(r'\D', '', value or '')
    if not value or not _re.fullmatch(r'[+()\d\s.-]+', value) or not 7 <= len(digits) <= 15:
        return ''
    if value.strip().startswith('+'):
        return '+' + digits
    if _re.fullmatch(r'0[17]\d{8}', digits):
        return '+254' + digits[1:]
    if _re.fullmatch(r'254[17]\d{8}', digits):
        return '+' + digits
    return value.strip()[:25] if len(digits) >= 7 else ''


@require_POST
@rate_limited('quick-lead', [(4, 300), (15, 86400)])
def lead_capture(request):
    """Quote popup: name + email and/or WhatsApp + the questions that fit the page the visitor is on. Saved as a WhatsApp/quote lead."""
    from Home.service_forms import config_by_key
    data = request.POST
    contact_raw = data.get('whatsapp') or data.get('phone') or ''
    if data.get('website'):                      # honeypot: bots fill every field
        add_strike(get_client_ip(request), 'honeypot on popup', weight=3)
        trap('popup', ['honeypot'], data.get('name', ''), data.get('email', ''), contact_raw, data.get('message', ''), request)
        return JsonResponse({'success': True})
    name = ' '.join((data.get('name') or '').split())[:100]
    email = (data.get('email') or '').strip().lower()[:120]
    phone = _wa_phone((contact_raw or '').strip()[:30])
    notes = (data.get('message') or '').strip()[:600]
    if len(name) < 2:
        return JsonResponse({'success': False, 'error': 'name'}, status=400)
    if email and not _re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return JsonResponse({'success': False, 'error': 'email'}, status=400)
    if contact_raw.strip() and not phone:
        return JsonResponse({'success': False, 'error': 'phone'}, status=400)
    if not email and not phone:
        return JsonResponse({'success': False, 'error': 'contact'}, status=400)
    cfg = config_by_key(data.get('service', ''))
    lines = []
    for q in cfg['questions']:
        v = ' '.join((data.get('q_' + q['key']) or '').split())[:120]
        if v and (q.get('type') == 'text' or v in q['options']):
            lines.append(f"{q['label']} {v}")
    month = (data.get('travel_month') or '')[:20]
    if month and month != 'Still deciding' and _re.fullmatch(r'\d{4}-\d{2}', month):
        lines.append(f"{cfg['when_label']}: {month}")
    if cfg['show_people'] and (data.get('travellers') or '').isdigit():
        lines.append(f"{cfg['people_label']}: {min(int(data['travellers']), 99)}")
    if notes:
        lines.append(f"Notes: {notes}")
    tour = cfg['service'] or ' '.join((data.get('tour') or '').split())[:160]
    message = '\n'.join(lines)[:900]
    # Bots: judged on content, never told they failed, never saved and never emailed to the team.
    ip = get_client_ip(request)
    reasons = lead_spam_reasons(name, tour, notes, data.get('form_ts'))
    if reasons:
        add_strike(ip, 'spam lead: ' + ', '.join(reasons))
        trap('popup', reasons, name, email, phone, message, request)
        return JsonResponse({'success': True})
    lead = QuickLead.objects.create(
        name=name, phone=phone, email=email, tour=tour, message=message,
        page_url=(data.get('page') or '')[:300], language=(data.get('lang') or '')[:8],
        ip=get_client_ip(request) if get_client_ip(request) != 'unknown' else None,
    )
    try:
        from EmailSetup.utils import notify_staff_of_lead, forward_to_crm
        notify_staff_of_lead(lead)
        forward_to_crm(lead)
    except Exception:
        pass
    return JsonResponse({'success': True})
