"""Create or revoke access keys for the hotels API.

    python manage.py create_api_key --name "Claude assistant"     # prints the token ONCE
    python manage.py create_api_key --list
    python manage.py create_api_key --revoke 1a2b3c4d             # by the key's prefix

The token is shown only once and stored only as a hash. Treat it like a password: it lets its holder add and edit
hotels (it cannot delete anything and cannot read bookings, contacts or users).
"""
from django.core.management.base import BaseCommand, CommandError

from Hotels.models import ApiKey


class Command(BaseCommand):
    help = 'Create, list or revoke hotels-API keys'

    def add_arguments(self, parser):
        parser.add_argument('--name', help='Label for the new key (who will use it)')
        parser.add_argument('--list', action='store_true', help='List existing keys')
        parser.add_argument('--revoke', metavar='PREFIX', help='Revoke the key with this prefix')

    def handle(self, *args, **opts):
        if opts['list']:
            for key in ApiKey.objects.order_by('-created_at'):
                used = key.last_used_at.strftime('%Y-%m-%d %H:%M') if key.last_used_at else 'never'
                self.stdout.write(f'{key.prefix}  {"active " if key.is_active else "REVOKED"}  {key.name}  (last used: {used})')
            return
        if opts['revoke']:
            updated = ApiKey.objects.filter(prefix=opts['revoke']).update(is_active=False)
            if not updated:
                raise CommandError('No key with that prefix.')
            self.stdout.write(self.style.SUCCESS('Key revoked. It stops working immediately.'))
            return
        if not opts['name']:
            raise CommandError('Give the key a name with --name "..."')
        key, token = ApiKey.create_key(opts['name'])
        self.stdout.write(self.style.SUCCESS(f'API key created for "{key.name}" (prefix {key.prefix}).'))
        self.stdout.write('\nCopy this token now. It is shown only once and cannot be recovered:\n')
        self.stdout.write(f'    {token}\n')
        self.stdout.write(f'Revoke it any time with:  python manage.py create_api_key --revoke {key.prefix}')
