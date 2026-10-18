"""Guide profile pages: public profile, lead capture (form, QR code, events), owner inline editing and analytics."""
import csv
import datetime
import json
import logging
import re
import threading
import time
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.views.decorators.http import require_POST

from ClientRequests.antispam import get_client_ip, hit_rate_limit, lead_spam_reasons, lead_token, add_strike, is_blocked
from EmailSetup.utils import get_company, send_transactional_email

from .blogs_api import sanitise
from .models import Guide, GuideDayStat, GuideEvent, GuideLead

logger = logging.getLogger(__name__)

BOT_UA = re.compile(r'bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|curl|python|headless', re.I)
SOURCES = {'profile', 'qr', 'event', 'share'}
CATEGORY_ICONS = {'safari': 'fa-binoculars', 'trekking': 'fa-hiking', 'beach': 'fa-umbrella-beach', 'hotel': 'fa-hotel',
                  'cruise': 'fa-ship', 'flights': 'fa-plane', 'visa': 'fa-passport', 'transfer': 'fa-shuttle-van',
                  'custom': 'fa-magic', 'other': 'fa-comments'}
PLAIN_FIELDS = {'role': 120, 'short_bio': 200, 'motto': 200, 'specializations': 300, 'languages': 200, 'parks': 300,
                'email': 254, 'whatsapp': 25}


def can_manage(user, guide):
    return bool(user and user.is_authenticated and (user.is_staff or guide.user_id == user.pk))


def _count_view(request, guide):
    agent = request.META.get('HTTP_USER_AGENT', '')
    if not agent or BOT_UA.search(agent) or can_manage(request.user, guide):
        return
    today = timezone.localdate()
    row, _ = GuideDayStat.objects.get_or_create(guide=guide, date=today)
    fields = {'views': F('views') + 1}
    if request.GET.get('src') in ('qr', 'event'):
        fields['qr_scans'] = F('qr_scans') + 1
    GuideDayStat.objects.filter(pk=row.pk).update(**fields)


def _event(value):
    """The active event an `?event=<id>` link points to (None when missing or unknown)."""
    try:
        return GuideEvent.objects.filter(pk=int(value), is_active=True).first()
    except (TypeError, ValueError):
        return None


def guide_detail(request, slug):
    guide = get_object_or_404(Guide.objects.select_related('user'), slug=slug)
    manager = can_manage(request.user, guide)
    if not guide.is_active and not manager:
        raise Http404
    _count_view(request, guide)
    src = request.GET.get('src', 'profile')
    context = {
        'guide': guide, 'is_manager': manager,
        'other_guides': Guide.objects.filter(is_active=True).exclude(pk=guide.pk)[:4],
        'lead_token': lead_token(), 'categories': [(k, v, CATEGORY_ICONS[k]) for k, v in GuideLead.CATEGORIES],
        'src': src if src in SOURCES else 'profile', 'event': _event(request.GET.get('event')),
        'events': list(GuideEvent.objects.filter(is_active=True)[:30]) if manager else [],
        'profile_url': request.build_absolute_uri(request.path),
    }
    response = render(request, 'Home/guide_detail.html', context)
    if manager:
        response['Cache-Control'] = 'private, no-store'
    return response


def _notify(lead):
    guide = lead.guide

    def send():
        try:
            rows = [('Guide', guide.name), ('Name', lead.name), ('Phone', lead.phone), ('Email', lead.email or '-'),
                    ('Interested in', lead.get_category_display()), ('Group size', lead.group_size or '-'),
                    ('Travelling', lead.travel_date.strftime('%d %b %Y') if lead.travel_date else '-'), ('Message', lead.message or '-'),
                    ('Source', lead.get_source_display() + (f' ({lead.event})' if lead.event else ''))]
            body = ''.join(f"<tr><td style='padding:4px 12px 4px 0'><b>{escape(k)}</b></td>"
                           f"<td>{escape(str(v)).replace(chr(10), '<br>')}</td></tr>" for k, v in rows)
            digits = ''.join(c for c in lead.phone if c.isdigit())
            title = f'New lead for {guide.name}: {lead.name} ({lead.get_category_display()})'
            html = f"<h3>{escape(title)}</h3><table>{body}</table><p>Follow up: <a href='https://wa.me/{digits}'>wa.me/{digits}</a></p>"
            company = get_company()
            send_transactional_email(company.booking_confirmation_email if company else 'info@daysafarisadventures.co.ke',
                                     'Day Safaris Team', title, html)
            if guide.email:
                send_transactional_email(guide.email, guide.name, title, html)
        except Exception:
            logger.exception('Guide lead notification failed')

    threading.Thread(target=send, daemon=True).start()


@require_POST
def guide_lead(request, slug):
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    ip = get_client_ip(request)
    manager = can_manage(request.user, guide)
    if is_blocked(ip):
        return JsonResponse({'ok': False, 'error': 'Too many requests.'}, status=429)
    if not manager and hit_rate_limit(ip, 'guide-lead', [(10, 300), (60, 86400)]):
        add_strike(ip, 'guide lead rate limit')
        return JsonResponse({'ok': False, 'error': 'Too many requests. Please slow down.'}, status=429)
    data = request.POST
    if data.get('website'):                                   # honeypot
        return JsonResponse({'ok': True})
    name = ' '.join((data.get('name') or '').split())[:100]
    phone = (data.get('phone') or '').strip()[:25]
    email = (data.get('email') or '').strip()[:254]
    message = (data.get('message') or '').strip()[:800]
    category = data.get('category') if data.get('category') in dict(GuideLead.CATEGORIES) else 'safari'
    source = data.get('src') if data.get('src') in SOURCES else 'profile'
    errors = {}
    if len(name) < 2:
        errors['name'] = 'Please enter your name.'
    if not re.fullmatch(r'\+?[0-9 ()\-]{7,22}', phone):
        errors['phone'] = 'Please enter a valid phone or WhatsApp number.'
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        errors['email'] = 'That email does not look right.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)
    if not manager:
        reasons = lead_spam_reasons(name, '', message, data.get('form_ts'))
        if reasons:
            add_strike(ip, 'spam guide lead: ' + ', '.join(reasons))
            return JsonResponse({'ok': True})                 # bots are never told
    try:
        group = min(max(int(data.get('group_size') or 0), 0), 200) or None
    except ValueError:
        group = None
    try:
        travel_date = datetime.date.fromisoformat((data.get('travel_date') or '')[:10])
    except ValueError:
        travel_date = None
    event = _event(data.get('event'))
    if event:
        source = 'event'
    lead = GuideLead.objects.create(
        guide=guide, name=name, phone=phone, email=email, category=category, group_size=group,
        travel_date=travel_date, message=message, source=source,
        event=event.name if event else '', ip=ip if ip != 'unknown' else None)
    _notify(lead)
    digits = ''.join(c for c in phone if c.isdigit())
    text = f"Hello {guide.name}, I am {name}. I am interested in: {lead.get_category_display()}."
    return JsonResponse({'ok': True, 'whatsapp': f'https://wa.me/{guide.whatsapp_digits}?text=' + text.replace(' ', '%20')})


@require_POST
def guide_edit(request, slug):
    """Inline editing by the guide (or staff): changes only whitelisted text fields."""
    guide = get_object_or_404(Guide, slug=slug)
    if not can_manage(request.user, guide):
        return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Invalid data.'}, status=400)
    changed = []
    for field, limit in PLAIN_FIELDS.items():
        if field in data and isinstance(data[field], str):
            value = ' '.join(strip_tags(data[field]).split())[:limit]
            if field in ('role',) and not value:
                continue
            if field == 'whatsapp':
                value = ''.join(c for c in value if c.isdigit())[:25]
            if getattr(guide, field) != value:
                setattr(guide, field, value); changed.append(field)
    if isinstance(data.get('bio'), str):
        bio = sanitise(data['bio'])[:12000]
        if guide.bio != bio:
            guide.bio = bio; changed.append('bio')
    if 'years_experience' in data:
        try:
            years = min(max(int(data['years_experience']), 0), 80)
        except (TypeError, ValueError):
            years = None
        if years is not None and guide.years_experience != years:
            guide.years_experience = years; changed.append('years_experience')
    if changed:
        guide.save()
    logger.info('Guide %s edited fields %s by %s', guide.slug, changed, request.user)
    return JsonResponse({'ok': True, 'changed': changed})


@require_POST
def guide_photo(request, slug):
    guide = get_object_or_404(Guide, slug=slug)
    if not can_manage(request.user, guide):
        return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
    upload = request.FILES.get('photo')
    if not upload:
        return JsonResponse({'ok': False, 'error': 'Choose a photo first.'}, status=400)
    if upload.size > 8 * 1024 * 1024:
        return JsonResponse({'ok': False, 'error': 'Photo is too big (max 8 MB).'}, status=400)
    try:
        from PIL import Image
        with Image.open(upload) as im:
            im.verify()
        upload.seek(0)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'That file is not a valid image.'}, status=400)
    guide.photo = upload
    guide.save()
    from .templatetags.image_tags import thumb
    return JsonResponse({'ok': True, 'url': thumb(guide.photo, 900)})


@login_required
def guide_analytics(request, slug):
    guide = get_object_or_404(Guide, slug=slug)
    if not can_manage(request.user, guide):
        raise Http404
    leads = guide.leads.exclude(status='Spam')
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{guide.slug}-leads.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Name', 'Phone', 'Email', 'Interest', 'Group', 'Travelling', 'Source', 'Event', 'Status', 'Message'])
        for l in leads:
            writer.writerow([l.created_at.strftime('%Y-%m-%d %H:%M'), l.name, l.phone, l.email, l.get_category_display(),
                             l.group_size or '', l.travel_date or '', l.get_source_display(), l.event, l.status, l.message])
        return response
    today = timezone.localdate()
    start = today - timedelta(days=29)
    per_day = {r['d']: r['n'] for r in leads.filter(created_at__date__gte=start)
               .annotate(d=TruncDate('created_at')).values('d').annotate(n=Count('id'))}
    views = {s.date: (s.views, s.qr_scans) for s in guide.daily_stats.filter(date__gte=start)}
    series = []
    for i in range(30):
        d = start + timedelta(days=i)
        series.append({'d': d.strftime('%d %b'), 'leads': per_day.get(d, 0), 'views': views.get(d, (0, 0))[0],
                       'scans': views.get(d, (0, 0))[1]})
    cats = dict(GuideLead.CATEGORIES)
    by_cat = [{'label': cats[r['category']], 'n': r['n'], 'icon': CATEGORY_ICONS[r['category']]}
              for r in leads.values('category').annotate(n=Count('id')).order_by('-n')]
    by_src = [{'label': dict(GuideLead.SOURCES)[r['source']], 'n': r['n']}
              for r in leads.values('source').annotate(n=Count('id')).order_by('-n')]
    by_event = [{'label': r['event'], 'n': r['n']} for r in leads.exclude(event='').values('event').annotate(n=Count('id')).order_by('-n')[:6]]
    total_views = sum(s['views'] for s in series)
    last30 = sum(s['leads'] for s in series)
    context = {
        'guide': guide, 'is_manager': True, 'analytics': True,
        'total': leads.count(), 'last7': sum(s['leads'] for s in series[-7:]), 'last30': last30,
        'views30': total_views, 'scans30': sum(s['scans'] for s in series),
        'conversion': round(100 * last30 / total_views, 1) if total_views else 0,
        'new_count': leads.filter(status='New').count(),
        'recent': leads[:25], 'statuses': [s for s, _ in GuideLead.STATUS if s != 'Spam'],
        'chart': {'series': series, 'cats': by_cat, 'src': by_src, 'events': by_event},
        'profile_url': request.build_absolute_uri(guide.get_absolute_url()),
    }
    response = render(request, 'Home/guide_analytics.html', context)
    response['Cache-Control'] = 'private, no-store'
    return response


@require_POST
def guide_lead_status(request, slug, pk):
    guide = get_object_or_404(Guide, slug=slug)
    if not can_manage(request.user, guide):
        return JsonResponse({'ok': False}, status=403)
    status = request.POST.get('status')
    if status not in dict(GuideLead.STATUS) or status == 'Spam':
        return JsonResponse({'ok': False}, status=400)
    updated = GuideLead.objects.filter(pk=pk, guide=guide).update(status=status)
    return JsonResponse({'ok': bool(updated)})


# ---------------------------------------------------------------------------------------------- link preview image
OG_W, OG_H = 1200, 630


def _wrap(draw, text, font, width):
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=font) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _make_og(guide, path):
    """1200x630 share card: the guide's photo on the right, name, role and brand on the left."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    img = Image.new('RGB', (OG_W, OG_H), (66, 13, 36))
    px = img.load()
    for y in range(OG_H):                                   # soft diagonal maroon gradient
        for x in range(0, OG_W, 4):
            t = (x / OG_W + y / OG_H) / 2
            c = (int(46 + 61 * t), int(8 + 20 * t), int(24 + 37 * t))
            for dx in range(4):
                px[x + dx, y] = c
    d = ImageDraw.Draw(img)
    panel = 460
    if guide.photo:
        try:
            with Image.open(guide.photo.path) as src:
                photo = ImageOps.fit(ImageOps.exif_transpose(src).convert('RGB'), (panel, OG_H), Image.LANCZOS, centering=(0.5, 0.35))
            img.paste(photo, (OG_W - panel, 0))
            d.rectangle([OG_W - panel - 6, 0, OG_W - panel, OG_H], fill=(246, 197, 130))
        except Exception:
            pass
    else:                                                    # no photo yet: the Day Safaris logo on a light card
        try:
            from django.contrib.staticfiles import finders
            logo = Image.open(finders.find('img/logo-nav.png')).convert('RGBA')
            logo.thumbnail((340, 340))
            cx, cy = OG_W - panel // 2, OG_H // 2
            d.rounded_rectangle([cx - 190, cy - 190, cx + 190, cy + 190], radius=40, fill=(255, 255, 255))
            img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
        except Exception:
            pass
    f = lambda size: ImageFont.load_default(size=size)
    left, width = 64, OG_W - panel - 64 - 56
    d.text((left, 58), 'DAY SAFARIS ADVENTURES', font=f(26), fill=(246, 197, 130))
    d.rectangle([left, 100, left + 70, 104], fill=(246, 197, 130))
    y = 150
    for line in _wrap(d, guide.name, f(84), width)[:2]:
        d.text((left, y), line, font=f(84), fill=(255, 255, 255)); y += 96
    y += 8
    for line in _wrap(d, guide.role, f(38), width)[:2]:
        d.text((left, y), line, font=f(38), fill=(246, 197, 130)); y += 48
    tag = 'Plan your safari with me'
    tw = d.textlength(tag, font=f(30)) + 56
    d.rounded_rectangle([left, OG_H - 118, left + tw, OG_H - 56], radius=31, fill=(246, 197, 130))
    d.text((left + 28, OG_H - 104), tag, font=f(30), fill=(66, 13, 36))
    img.save(path, 'JPEG', quality=82, optimize=True, progressive=True)


def guide_og(request, slug):
    import hashlib
    import os
    from django.conf import settings
    from django.http import FileResponse
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    try:
        stamp = int(os.path.getmtime(guide.photo.path)) if guide.photo else 0
    except OSError:
        stamp = 0
    key = hashlib.md5(f'{guide.name}|{guide.role}|{guide.photo.name if guide.photo else ""}|{stamp}'.encode()).hexdigest()[:12]
    folder = os.path.join(settings.MEDIA_ROOT, 'og')
    path = os.path.join(folder, f'guide-{guide.pk}-{key}.jpg')
    if not os.path.exists(path):
        os.makedirs(folder, exist_ok=True)
        _make_og(guide, path)
    response = FileResponse(open(path, 'rb'), content_type='image/jpeg')
    response['Cache-Control'] = 'public, max-age=86400'
    return response
