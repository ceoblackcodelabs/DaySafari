"""Find (and optionally remove) spam leads and bot sign-ups already in the database.

Dry run by default: prints what it would do.

    python manage.py purge_spam                 # report only
    python manage.py purge_spam --quarantine    # mark as Spam (reversible, keeps the rows)
    python manage.py purge_spam --delete        # delete spam contacts/bookings
    python manage.py purge_spam --deactivate-users   # disable obvious bot accounts
"""
import collections

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from ClientRequests.models import Bookings, Contact, QuickLead
from ClientRequests.spamfilter import normalise, spam_reasons

BOT_USER_EMAIL = ('seo', 'backlink', 'casino', 'crypto', 'escort')


class Command(BaseCommand):
    help = 'Report/quarantine/delete spam contact messages, bookings and bot accounts'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete spam rows')
        parser.add_argument('--quarantine', action='store_true', help='Mark spam rows with status Spam instead of deleting')
        parser.add_argument('--deactivate-users', action='store_true', help='Deactivate obvious bot accounts')

    def classify(self, qs, fields):
        # Campaign detection from the data itself: identical text 3+ times is a campaign.
        counts = collections.Counter(normalise(f"{getattr(o, 'subject', '')} {o.message or ''}")[:400] for o in qs)
        spam, real = [], []
        for obj in qs:
            reasons = spam_reasons(count_campaign=False, **{f: (getattr(obj, f, '') or '') for f in fields})
            key = normalise(f"{getattr(obj, 'subject', '')} {obj.message or ''}")[:400]
            if len(key) >= 15 and counts[key] >= 3:      # empty/short texts repeat naturally; not a campaign
                reasons = reasons + [f'same text sent {counts[key]} times']
            (spam if reasons else real).append((obj, reasons))
        return spam, real

    @transaction.atomic
    def handle(self, *args, **opts):
        for label, model, fields in (('contact messages', Contact, ('name', 'email', 'subject', 'message')),
                                     ('bookings', Bookings, ('name', 'email', 'message')),
                                     ('WhatsApp popup leads', QuickLead, ('name', 'message'))):
            quarantined = model.objects.filter(status__in=('Spam', 'spam'))
            qs = list(model.objects.exclude(status__in=('Spam', 'spam')))
            spam, real = self.classify(qs, fields)
            self.stdout.write(f'\n{label}: {len(qs)} checked, {len(spam)} spam, {len(real)} look genuine; '
                              f'{quarantined.count()} already quarantined as Spam')
            for obj, reasons in real[:25]:
                self.stdout.write(f'   keep  #{obj.pk} {obj.name[:25]!r} <{getattr(obj, 'email', getattr(obj, 'phone', ''))[:35]}> {getattr(obj, "subject", "")[:40]!r}')
            if opts['delete']:
                # new spam found now + everything already quarantined by the live filter
                total = quarantined.count() + len(spam)
                model.objects.filter(pk__in=[o.pk for o, _ in spam]).delete()
                quarantined.delete()
                self.stdout.write(self.style.SUCCESS(f'   deleted {total} spam {label} (genuine ones untouched)'))
            elif opts['quarantine']:
                status = 'spam' if model is Bookings else 'Spam'
                model.objects.filter(pk__in=[o.pk for o, _ in spam]).update(status=status)
                self.stdout.write(self.style.SUCCESS(f'   quarantined {len(spam)} {label} (status {status})'))

        self.stdout.write('\nSuspicious accounts (never staff/superusers):')
        sus = []
        for user in User.objects.filter(is_staff=False, is_superuser=False):
            domain = user.email.split('@')[-1].lower()
            local = user.email.split('@')[0]
            if any(k in domain for k in BOT_USER_EMAIL) or local.count('.') >= 4:
                sus.append(user)
                self.stdout.write(f'   #{user.pk} {user.username} <{user.email}> joined {user.date_joined:%Y-%m-%d}')
        if opts['deactivate_users'] and sus:
            User.objects.filter(pk__in=[u.pk for u in sus]).update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f'   deactivated {len(sus)} accounts'))
        if not (opts['delete'] or opts['quarantine'] or opts['deactivate_users']):
            self.stdout.write(self.style.WARNING('\nDry run only. Re-run with --delete, --quarantine and/or --deactivate-users.'))
