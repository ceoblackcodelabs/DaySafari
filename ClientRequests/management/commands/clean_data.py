"""One command to clean automated spam and your own test rows out of the lists people fill in.

    python manage.py clean_data            # dry run: shows what it would do, changes nothing
    python manage.py clean_data --apply    # do it

What it does (bookings, contact messages, popup/WhatsApp leads, guide leads):
  * spam           -> moved into the Bot trap (admin > Bot trap), so it can still be inspected or restored
  * test rows      -> deleted (names/emails like test, riomachi, example.com ...)
It never touches users, testimonials, packages, hotels or any content. Take a backup first (./deploy.sh does).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from ClientRequests.management.commands.audit_data import TEST_EMAIL, TEST_WORDS
from ClientRequests.models import BotAttempt, Bookings, Contact, QuickLead
from ClientRequests.spamfilter import spam_reasons


class Command(BaseCommand):
    help = 'Move spam to the Bot trap and delete test rows (dry run unless --apply)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **o):
        plan = []   # (obj, action, form, reasons, name, email, phone, message, ip)
        for b in Bookings.objects.all():
            r = spam_reasons(name=b.name, email=b.email, message=b.message or '', count_campaign=False)
            if r or b.status == 'spam':
                plan.append((b, 'trap', 'booking', r or ['marked spam'], b.name, b.email, b.phone, b.message or '', None))
            elif TEST_EMAIL.search(b.email) or TEST_WORDS.search(b.name):
                plan.append((b, 'delete', 'booking', ['test'], b.name, b.email, b.phone, '', None))
        for c in Contact.objects.all():
            r = spam_reasons(name=c.name, email=c.email, subject=c.subject, message=c.message, count_campaign=False)
            if r or c.status == 'Spam':
                plan.append((c, 'trap', 'contact', r or ['marked spam'], c.name, c.email, '', f'{c.subject}\n{c.message}', None))
            elif TEST_EMAIL.search(c.email) or TEST_WORDS.search(f'{c.name} {c.subject}'):
                plan.append((c, 'delete', 'contact', ['test'], c.name, c.email, '', '', None))
        for l in QuickLead.objects.exclude(status='Booked'):
            r = spam_reasons(name=l.name, message=l.message, count_campaign=False)
            if r or l.status == 'Spam':
                plan.append((l, 'trap', 'popup', r or ['marked spam'], l.name, getattr(l, 'email', ''), l.phone, l.message, l.ip))
            elif TEST_WORDS.search(f'{l.name} {l.tour} {l.message}'):
                plan.append((l, 'delete', 'popup', ['test'], l.name, '', l.phone, '', l.ip))
        try:
            from Home.models import GuideLead
            for l in GuideLead.objects.all():
                r = spam_reasons(name=l.name, email=l.email, message=l.message, count_campaign=False)
                if r or l.status == 'Spam':
                    plan.append((l, 'trap', 'guide', r or ['marked spam'], l.name, l.email, l.phone, l.message, l.ip))
        except Exception as exc:
            self.stdout.write(f'Guide leads skipped: {exc}')

        counts = {}
        for obj, action, form, *_ in plan:
            counts[(form, action)] = counts.get((form, action), 0) + 1
        for (form, action), n in sorted(counts.items()):
            self.stdout.write(f'  {form:8} {"-> Bot trap" if action == "trap" else "delete    "}  {n}')
        self.stdout.write(f'Total: {len(plan)} rows')
        if not o['apply']:
            self.stdout.write(self.style.WARNING('Dry run. Add --apply to do it.'))
            return
        for obj, action, form, reasons, name, email, phone, msg, ip in plan:
            if action == 'trap':
                row = BotAttempt(ip=ip, form=form[:12], reasons=', '.join(reasons)[:300], name=(name or '')[:120],
                                 email=(email or '')[:254], phone=(phone or '')[:40], message=(msg or '')[:1500])
                row.save()
                when = getattr(obj, 'created_at', None)
                if when:
                    BotAttempt.objects.filter(pk=row.pk).update(created_at=when)
            obj.delete()
        self.stdout.write(self.style.SUCCESS(f'Done: {len(plan)} rows cleaned.'))
