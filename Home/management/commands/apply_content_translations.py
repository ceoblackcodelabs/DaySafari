from django.core.management.base import BaseCommand

from Home import content_i18n as ci


class Command(BaseCommand):
    help = ('Fill the fr/sw/es/de/it columns of database content from Home/content_translations/*.json. '
            'Only empty columns are filled (use --force to overwrite). Safe to run after every deploy.')

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='overwrite translations that already exist')
        parser.add_argument('--missing', action='store_true', help='list English segments that have no translation')
        parser.add_argument('--export', metavar='FILE', help='write all English segments to FILE (json list)')

    def handle(self, *args, **opts):
        if opts['export']:
            return self.export(opts['export'])
        maps = {lang: ci.load(lang) for lang in ci.LANGS}
        missing = {}
        for model, fields in ci.translated_fields():
            counts = dict.fromkeys(ci.LANGS, 0)
            for obj in model._base_manager.all().iterator():
                for field in fields:
                    source = getattr(obj, f'{field}_en') or ''
                    if not source.strip():
                        continue
                    for lang in ci.LANGS:
                        current = getattr(obj, f'{field}_{lang}')
                        if current and not opts['force']:
                            continue
                        done = ci.translate_value(source, maps[lang])
                        if done is None:
                            for seg in ci.segments(source):
                                if seg not in maps[lang]:
                                    missing.setdefault(lang, set()).add(seg)
                            continue
                        if done != current:
                            setattr(obj, f'{field}_{lang}', done)
                            counts[lang] += 1
                obj.save()
            if any(counts.values()):
                self.stdout.write(f'{model._meta.label}: ' + ', '.join(f'{l}={n}' for l, n in counts.items() if n))
        total = sum(len(v) for v in missing.values())
        self.stdout.write(self.style.SUCCESS('Done.') if not total else
                          self.style.WARNING(f'{total} segments still have no translation (they stay in English). '
                                             'Run with --missing to list them.'))
        if opts['missing']:
            for lang, segs in sorted(missing.items()):
                for seg in sorted(segs):
                    self.stdout.write(f'[{lang}] {seg[:140]}')

    def export(self, path):
        import json
        seen = {}
        for model, fields in ci.translated_fields():
            for obj in model._base_manager.all().iterator():
                for field in fields:
                    for seg in ci.segments(getattr(obj, f'{field}_en') or ''):
                        seen.setdefault(seg, f'{model._meta.label}.{field}')
        json.dump(list(seen), open(path, 'w', encoding='utf-8'), ensure_ascii=False)
        self.stdout.write(f'{len(seen)} segments -> {path}')
