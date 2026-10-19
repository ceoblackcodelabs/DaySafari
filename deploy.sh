#!/usr/bin/env bash
# Safe deploy for the PRODUCTION server. Run it instead of a bare `git pull`:
#     ./deploy.sh
# It can never leave you without your live database or uploads:
#   1. backs up the live database + media first (./backups/)
#   2. pulls fast-forward only (never merges, never `reset --hard`, never discards local changes)
#   3. if the incoming commits changed or deleted db.sqlite3, puts the live copy back
#   4. installs the content-translation package, migrates, applies the DB translations,
#      collects static files, warms image thumbnails, restarts the app
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python}"          # e.g. PYTHON=/home/user/venv/bin/python ./deploy.sh
STAMP="$(date +%Y%m%d-%H%M%S)"
SAFE_COPY="backups/live-db-before-deploy-$STAMP.sqlite3"
mkdir -p backups

echo "==> 1/4 Backing up live data"
"$PY" manage.py backup_data --keep 30
[ -f db.sqlite3 ] && cp -p db.sqlite3 "$SAFE_COPY"

echo "==> 2/4 Pulling (fast-forward only)"
OLD_HEAD="$(git rev-parse HEAD)"
git fetch -q origin || true

# (a) logs are not tracked any more: a local edit to the old tracked log must not block the pull (a copy is kept in backups/)
if git ls-files --error-unmatch logs/django-error.log >/dev/null 2>&1 && ! git diff --quiet -- logs/django-error.log; then
    cp -p logs/django-error.log "backups/django-error-$STAMP.log"
    git checkout -- logs/django-error.log
    echo "    old tracked log reset (copy kept in backups/django-error-$STAMP.log)"
fi

# (b) files the pull would ADD that already exist here as untracked files (typically media uploaded straight to the server):
#     identical to the repo copy -> removed (the pull brings the same file back);
#     different from the repo copy -> moved to backups/ so nothing live is ever lost, and listed below.
CLASH="backups/media-clash-$STAMP"
git diff --name-only --diff-filter=A HEAD '@{u}' 2>/dev/null | while IFS= read -r f; do
    [ -e "$f" ] || continue
    git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 && continue
    if [ "$(git hash-object -- "$f")" = "$(git rev-parse "@{u}:$f")" ]; then
        rm -f -- "$f"
    else
        mkdir -p "$CLASH/$(dirname "$f")"
        mv -- "$f" "$CLASH/$f"
        echo "    differs from the repo copy, kept in $CLASH/: $f"
    fi
done
if ! git pull --ff-only; then
    cat <<MSG

Pull was refused. Your live database and uploads were NOT touched.
Do NOT run 'git checkout .', 'git reset --hard' or 'git stash' to get past this:
those can destroy live data. Send the error above to your developer, or restore
from $SAFE_COPY if the database ever goes missing.
MSG
    exit 1
fi

echo "==> 3/4 Checking the live database survived"
if [ -f "$SAFE_COPY" ] && { [ ! -f db.sqlite3 ] || ! git diff --quiet "$OLD_HEAD" HEAD -- db.sqlite3; }; then
    cp -p "$SAFE_COPY" db.sqlite3
    echo "    Incoming commits touched db.sqlite3 -> restored your live copy from $SAFE_COPY"
fi
[ -f db.sqlite3 ] || { echo "ERROR: db.sqlite3 is missing and no backup copy exists"; exit 1; }

echo "==> 4/4 Updating the app"
# Only this package: a blanket `pip install -r requirements.txt` could change the server's Django version.
"$PY" -m pip install --quiet "django-modeltranslation==0.20.6"
"$PY" manage.py migrate --noinput
"$PY" manage.py apply_content_translations
"$PY" manage.py collectstatic --noinput || true
"$PY" manage.py warm_thumbnails || true
mkdir -p tmp && touch tmp/restart.txt      # Passenger / cPanel restart
echo "Done. Live database kept; backup in backups/."
