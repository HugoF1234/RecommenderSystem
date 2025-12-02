#!/bin/bash
# Script to setup PostgreSQL database locally
# Usage: ./scripts/setup_postgres_local.sh

set -e

echo "=== Setting up PostgreSQL database locally ==="

# Database configuration
DB_NAME="saveeat"
DB_USER="saveeat_user"
DB_PASSWORD="saveeat_password"
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Please install it first:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "PostgreSQL is not running. Please start it first:"
    echo "  macOS: brew services start postgresql"
    echo "  Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

echo "PostgreSQL is running ✓"

# Create database and user
echo "Creating database and user..."

# Connect as postgres superuser to create database and user
sudo -u postgres psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

echo "Database and user created ✓"

# Create .env file for local development
cat > .env.local <<EOF
# PostgreSQL Configuration (Local)
DATABASE_TYPE=postgresql
POSTGRESQL_HOST=$DB_HOST
POSTGRESQL_PORT=$DB_PORT
POSTGRESQL_DATABASE=$DB_NAME
POSTGRESQL_USER=$DB_USER
POSTGRESQL_PASSWORD=$DB_PASSWORD
EOF

echo ".env.local file created ✓"
echo ""
echo "=== Setup complete! ==="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""
echo "To load data, run:"
echo "  python main.py load-db"
echo ""
echo "Connection string:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

