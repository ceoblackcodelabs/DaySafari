#!/bin/bash

echo "=== COMPLETE FIX FOR MIGRATIONS & BROCHURE MODEL ==="

# Kill any running Django server
echo "Stopping Django server..."
pkill -f "python manage.py" 2>/dev/null
sleep 2

# Remove lock files
echo "Removing lock files..."
rm -f db.sqlite3-journal db.sqlite3-wal

# Backup database
echo "Backing up database..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
fi

# Delete ALL migration files including init files (CAREFUL!)
echo "Cleaning all migrations..."
find . -path "*/migrations/*.py" -delete
find . -path "*/migrations/__pycache__" -delete 2>/dev/null

# Recreate migration directories with __init__.py
echo "Recreating migration structure..."
mkdir -p Home/migrations
touch Home/migrations/__init__.py
touch Home/__init__.py

# Delete and recreate database
echo "Recreating database..."
rm -f db.sqlite3
touch db.sqlite3
chmod 666 db.sqlite3

# Make sure you're in the right directory
echo "Current directory: $(pwd)"

# Check if model exists
echo "Checking for Brochure model in models.py..."
if grep -q "class.*Brochure" Home/models.py; then
    echo "✓ Brochure model found"
else
    echo "✗ Brochure model NOT found in Home/models.py"
    echo "Please add the Brochure model to Home/models.py first"
    exit 1
fi

# Create fresh migrations
echo "Creating fresh migrations..."
python manage.py makemigrations

# Show what migrations were created
echo "Migrations created:"
ls -la Home/migrations/

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Fix permissions
chmod 666 db.sqlite3

# Check if table was created
echo "Checking if Brochure table exists..."
python manage.py dbshell << EOF
.tables
.exit
EOF

# Try to create a test entry
echo "Testing brochure model..."
python manage.py shell << EOF
from Home.models import Brochure
try:
    # Just check if model works
    print(f"Brochure model exists. Count: {Brochure.objects.count()}")
    print("✓ Brochure model is working!")
except Exception as e:
    print(f"✗ Error: {e}")
EOF

echo "=== COMPLETE ==="
echo "Run: python manage.py runserver"