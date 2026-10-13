"""Back up the live database and uploaded media, outside git.

    python manage.py backup_data            # writes into ./backups/
    python manage.py backup_data --keep 14  # keep the 14 newest of each kind
    python manage.py backup_data --no-media # database only (fast; fine for hourly)

SQLite is copied with its online-backup API, so it is safe while the site is
running. Schedule it with cron, e.g. daily at 02:30:
    30 2 * * * cd /path/to/DaySafari && /path/to/venv/bin/python manage.py backup_data
Then copy ./backups/ somewhere off the server (rsync / rclone / cloud storage).
"""
import sqlite3
import tarfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Back up the SQLite database and media files to ./backups/'

    def add_arguments(self, parser):
        parser.add_argument('--keep', type=int, default=14, help='How many backups of each kind to keep')
        parser.add_argument('--no-media', action='store_true', help='Skip the media archive')
        parser.add_argument('--dir', default=None, help='Backup directory (default: <project>/backups)')

    def handle(self, *args, **opts):
        db = settings.DATABASES['default']
        if 'sqlite3' not in db['ENGINE']:
            raise CommandError('backup_data only supports SQLite; use your database tool for other engines.')
        out = Path(opts['dir'] or settings.BASE_DIR / 'backups')
        out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')

        db_file = out / f'db-{stamp}.sqlite3'
        source = sqlite3.connect(str(db['NAME']))
        target = sqlite3.connect(str(db_file))
        with target:
            source.backup(target)
        source.close(); target.close()
        self.stdout.write(self.style.SUCCESS(f'Database -> {db_file.name} ({db_file.stat().st_size // 1024} KB)'))

        if not opts['no_media']:
            media = Path(settings.MEDIA_ROOT)
            archive = out / f'media-{stamp}.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                tar.add(media, arcname='media', filter=lambda i: None if '/thumbs' in i.name or i.name.endswith('/thumbs') else i)
            self.stdout.write(self.style.SUCCESS(f'Media    -> {archive.name} ({archive.stat().st_size // 1048576} MB)'))

        for pattern in ('db-*.sqlite3', 'media-*.tar.gz'):
            for old in sorted(out.glob(pattern))[:-opts['keep']]:
                old.unlink()
        self.stdout.write(f'Backups kept in {out} (newest {opts["keep"]} of each).')
