import gzip
import shutil

from django.apps import AppConfig
from django.conf import settings


class SafarisConfig(AppConfig):
    name = 'safaris'

    def ready(self):
        # Pre-gzip text assets so WhiteNoise can serve them compressed, with no per-request CPU cost.
        for base in settings.STATICFILES_DIRS[:1]:  # our theme folder
            for f in base.rglob('*'):
                if f.suffix not in ('.css', '.js', '.svg') or not f.is_file():
                    continue
                gz = f.with_name(f.name + '.gz')
                if not gz.exists() or gz.stat().st_mtime < f.stat().st_mtime:
                    try:
                        with f.open('rb') as src, gzip.GzipFile(gz, 'wb', 9, mtime=0) as dst:
                            shutil.copyfileobj(src, dst)
                    except OSError:
                        pass
