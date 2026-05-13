#!/bin/bash

echo "=== Resetting Django migrations and database ==="

# Set backup filename with timestamp
BACKUP_FILE="db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"

# Stop any running Django server that might lock the database
echo "Checking for running Django server..."
pkill -f "python manage.py runserver" 2>/dev/null
sleep 2

# Remove any SQLite lock files
echo "Removing lock files..."
rm -f db.sqlite3-journal db.sqlite3-wal 2>/dev/null

# Backup database
if [ -f "db.sqlite3" ]; then
    echo "Backing up database to $BACKUP_FILE..."
    cp db.sqlite3 "$BACKUP_FILE"
    # Fix permissions on backup
    chmod 644 "$BACKUP_FILE"
else
    echo "No existing database found to backup."
fi

# Delete all migration files
echo "Deleting migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/__pycache__/*" -delete

# Also clean up pycache in apps
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Delete database
echo "Deleting database..."
rm -f db.sqlite3

# Fix directory permissions
echo "Setting correct permissions..."
chmod 775 . 2>/dev/null
chmod 775 Home/migrations/ 2>/dev/null

# Create new migrations
echo "Creating new migrations..."
python manage.py makemigrations

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Fix database permissions after creation
echo "Fixing database permissions..."
chmod 666 db.sqlite3

# Check if backup exists and restore
if [ -f "$BACKUP_FILE" ]; then
    echo "Restoring data from backup..."

    # Try simple restore first (faster)
    echo "Attempting simple restore..."
    cp "$BACKUP_FILE" db.sqlite3.restore
    chmod 666 db.sqlite3.restore

    # Check if we can use the simple restore
    if python manage.py check --database default > /dev/null 2>&1; then
        mv db.sqlite3.restore db.sqlite3
        chmod 666 db.sqlite3
        echo "Simple restore successful!"
    else
        echo "Simple restore failed, using selective restore..."
        rm -f db.sqlite3.restore

        # Create a temporary database from backup to dump data
        TEMP_DB="temp_restore_$$.sqlite3"
        cp "$BACKUP_FILE" "$TEMP_DB"
        chmod 644 "$TEMP_DB"

        # Dump data from specific apps (exclude auth and contenttypes to avoid conflicts)
        echo "Dumping data from backup..."
        python manage.py dumpdata --database=temp --exclude=admin --exclude=auth --exclude=contenttypes --exclude=sessions --exclude=authtoken --exclude=socialaccount --exclude=account --exclude=Home.bronchure --format=json > restored_data.json 2>/dev/null

        # Load data into new database
        if [ -s restored_data.json ]; then
            echo "Loading data into new database..."
            python manage.py loaddata restored_data.json

            # Clean up
            rm -f "$TEMP_DB" restored_data.json
            echo "Data restored successfully!"
        else
            echo "No data to restore or backup was empty."
            rm -f "$TEMP_DB" restored_data.json 2>/dev/null
        fi
    fi
else
    echo "No backup found to restore."
    echo "Creating superuser manually if needed..."
    python manage.py createsuperuser
fi

# Final permission fix
echo "Setting final permissions..."
chmod 666 db.sqlite3
chmod -R 664 Home/migrations/*.py 2>/dev/null

echo "=== Reset complete! ==="
echo "Database permissions: $(ls -la db.sqlite3)"
echo "You can now run: python manage.py runserver"