#!/bin/bash

echo "=== Resetting Django migrations and database ==="

# Backup database
if [ -f "db.sqlite3" ]; then
    echo "Backing up database..."
    cp db.sqlite3 db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
fi

# Delete all migration files
echo "Deleting migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/__pycache__/*" -delete

# Delete database
echo "Deleting database..."
rm -f db.sqlite3

# Create new migrations
echo "Creating new migrations..."
python manage.py makemigrations

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py createsuperuser

echo "=== Reset complete! ==="