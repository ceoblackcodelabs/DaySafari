"""Daily safety net: move any spam that slipped into Leads, Contact messages or Bookings into the bot trap.

Run it from cron once a day:   python manage.py sweep_spam
(It is `move_spam_to_trap --apply` with quiet output; the forms already stop almost all spam before saving.)
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Daily spam sweep (cron)'

    def handle(self, *args, **options):
        call_command('move_spam_to_trap', apply=True, block_min=0, stdout=self.stdout)
