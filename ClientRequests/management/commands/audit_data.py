"""Read-only audit: list rows that look automated, seeded or like testing, across the models people fill in.

    python manage.py audit_data            # report only, never changes or deletes anything
    python manage.py audit_data --limit 40

Nothing is touched. To act on the result use the existing commands, which move or mark rows:
    python manage.py move_spam_to_trap --apply    (moves spam out of the real lists into the Bot trap, reversible)
"""
import re
from collections import Counter

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ClientRequests.models import Bookings, Contact, QuickLead
from ClientRequests.spamfilter import spam_reasons

TEST_WORDS = re.compile(r'(^|[\W_])(test|testing|tester|asdf|qwerty|lorem|dummy|sample|fake)([\W_]|$)', re.I)
TEST_EMAIL = re.compile(r'(example\.(com|org)|test@|riomachi|mailinator|yopmail|guerrillamail|tempmail|10minutemail)', re.I)


class Command(BaseCommand):
    help = 'Read-only audit of automated, seeded and test rows'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=25, help='Rows to print per section')

    def section(self, title, rows, limit):
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n{title}: {len(rows)}'))
        for r in rows[:limit]:
            self.stdout.write('  ' + r)
        if len(rows) > limit:
            self.stdout.write(f'  ... and {len(rows) - limit} more')

    def handle(self, *args, **o):
        n = o['limit']
        rows = []
        for b in Bookings.objects.all():
            why = spam_reasons(name=b.name, email=b.email, message=b.message or '', count_campaign=False)
            if not why and (TEST_EMAIL.search(b.email) or TEST_WORDS.search(b.name)):
                why = ['looks like testing']
            if why:
                rows.append(f'#{b.pk} {b.created_at:%Y-%m-%d %H:%M} {b.name} <{b.email}> [{b.status}] {", ".join(why)}')
        self.section('Bookings that look automated or like tests', rows, n)

        rows = []
        for c in Contact.objects.all():
            why = spam_reasons(name=c.name, email=c.email, subject=c.subject, message=c.message, count_campaign=False)
            if not why and (TEST_EMAIL.search(c.email) or TEST_WORDS.search(f'{c.name} {c.subject}')):
                why = ['looks like testing']
            if why:
                rows.append(f'#{c.pk} {c.created_at:%Y-%m-%d} {c.name} <{c.email}> "{c.subject[:40]}" {", ".join(why)}')
        self.section('Contact messages that look automated or like tests', rows, n)

        rows = []
        for l in QuickLead.objects.all():
            why = spam_reasons(name=l.name, message=l.message, count_campaign=False)
            if not why and TEST_WORDS.search(f'{l.name} {l.tour} {l.message}'):
                why = ['looks like testing']
            if why:
                rows.append(f'#{l.pk} {l.created_at:%Y-%m-%d} {l.name} {l.phone} {", ".join(why)}')
        self.section('Popup / WhatsApp leads that look automated or like tests', rows, n)

        try:
            from Home.models import GuideLead
            rows = []
            for l in GuideLead.objects.all():
                why = spam_reasons(name=l.name, email=l.email, message=l.message, count_campaign=False)
                if why:
                    rows.append(f'#{l.pk} {l.created_at:%Y-%m-%d} {l.name} {", ".join(why)}')
            self.section('Guide leads that look automated', rows, n)
        except Exception as exc:                                      # a missing table must not stop the audit
            self.stdout.write(f'Guide leads skipped: {exc}')

        rows = []
        for u in User.objects.filter(is_staff=False, is_superuser=False):
            local = (u.email or '').split('@')[0]
            if TEST_EMAIL.search(u.email or '') or TEST_WORDS.search(u.username) or re.search(r'\d{6,}', local) or u.last_login is None:
                rows.append(f'#{u.pk} {u.date_joined:%Y-%m-%d} {u.username} <{u.email}> last login: {u.last_login:%Y-%m-%d}' if u.last_login
                            else f'#{u.pk} {u.date_joined:%Y-%m-%d} {u.username} <{u.email}> never logged in')
        self.section('Sign-ups that look automated, test or never logged in (review before touching)', rows, n)

        from Home.models import Testimonials
        self.stdout.write(self.style.MIGRATE_HEADING(f'\nTestimonials on file: {Testimonials.objects.count()} (review these yourself)'))
        for t in Testimonials.objects.all()[:n]:
            self.stdout.write(f'  #{t.pk} {t.created_at:%Y-%m-%d} {t.name} ({t.location or "no location"}) {t.star_rating}*: {t.feedback[:60]}')

        self.stdout.write(self.style.WARNING('\nRead-only: nothing was changed. See move_spam_to_trap / purge_spam to act on spam.'))
