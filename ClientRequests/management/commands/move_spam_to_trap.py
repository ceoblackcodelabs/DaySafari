"""Move spam already sitting in the real lists (WhatsApp leads, contact messages, bookings) into the bot trap.

    python manage.py move_spam_to_trap                 # report only
    python manage.py move_spam_to_trap --apply         # move them (they are removed from the real lists)
    python manage.py move_spam_to_trap --apply --block-min 3   # also blacklist every IP seen 3+ times
"""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from ClientRequests.models import BotAttempt, Bookings, Contact, QuickLead, set_ip_blocked
from ClientRequests.spamfilter import spam_reasons


class Command(BaseCommand):
    help = 'Move existing spam into the bot trap (dry run by default)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--block-min', type=int, default=0, help='Blacklist IPs with at least this many entries (0 = none)')

    @transaction.atomic
    def handle(self, *args, **o):
        found = []   # (model, obj, form, reasons, name, email, phone, message, ip)
        for l in QuickLead.objects.exclude(status='Booked'):
            r = spam_reasons(name=l.name, message=l.message, count_campaign=False)
            if r or l.status == 'Spam':
                found.append((l, 'popup', r or ['marked spam'], l.name, '', l.phone, l.message, l.ip))
        for c in Contact.objects.all():
            r = spam_reasons(name=c.name, email=c.email, subject=c.subject, message=c.message, count_campaign=False)
            if r or c.status == 'Spam':
                found.append((c, 'contact', r or ['marked spam'], c.name, c.email, '', f'{c.subject}\n{c.message}', None))
        for b in Bookings.objects.all():
            r = spam_reasons(name=b.name, email=b.email, message=b.message or '', count_campaign=False)
            if r or b.status == 'spam':
                found.append((b, 'booking', r or ['marked spam'], b.name, b.email, b.phone, b.message or '', None))
        by = Counter(f[1] for f in found)
        self.stdout.write(f'Spam found: {dict(by)}  total {len(found)}')
        ips = Counter(f[7] for f in found if f[7])
        self.stdout.write(f'Distinct IPs: {len(ips)}  | top: {ips.most_common(5)}')
        if not o['apply']:
            self.stdout.write(self.style.WARNING('Dry run. Add --apply to move them.'))
            return
        for obj, form, reasons, name, email, phone, msg, ip in found:
            row = BotAttempt(ip=ip, form=form, reasons=', '.join(reasons)[:300], name=name[:120], email=email[:254], phone=phone[:40], message=msg[:1500])
            row.save()
            when = getattr(obj, 'created_at', None)
            if when:
                BotAttempt.objects.filter(pk=row.pk).update(created_at=when)
            obj.delete()
        blocked = 0
        if o['block_min']:
            for ip, n in ips.items():
                if n >= o['block_min']:
                    set_ip_blocked(ip, True, f'Seen {n} times in spam', auto=True); blocked += 1
        self.stdout.write(self.style.SUCCESS(f'Moved {len(found)} entries to the bot trap; blacklisted {blocked} IP(s).'))
