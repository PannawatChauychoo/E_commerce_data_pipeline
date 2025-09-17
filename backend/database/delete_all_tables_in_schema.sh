#!/bin/bash

# Get the .env file path and source it
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"

if [ $# -eq 0 ]; then
	echo "Usage: $0 <schema_name>"
	exit 1
fi

if [ -f "$ENV_FILE" ]; then
	set -a
	source "$ENV_FILE"
	set +a
	echo "Environment variables loaded"
else
	echo "Error: .env file not found at $ENV_FILE"
	exit 1
fi

# Specify the schema name (modify as needed)
SCHEMA_NAME="$1" # or whatever your schema name is

echo "Connecting to database: $DB_NAME on $DB_HOST:$DB_PORT"
echo "This will DELETE ALL TABLES in schema: $SCHEMA_NAME"
read -p "Are you sure? (y/N): " confirm

if [ "$confirm" != "y" ]; then
	echo "Operation cancelled"
	exit 0
fi

# Generate and execute the DROP TABLE commands
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
DO \$\$ 
DECLARE
    r RECORD;
BEGIN
    -- Disable foreign key checks temporarily
    SET session_replication_role = replica;
    
    -- Drop all tables in the specified schema
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '$SCHEMA_NAME') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS $SCHEMA_NAME.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Re-enable foreign key checks
    SET session_replication_role = DEFAULT;
END
\$\$;
EOF

echo "All tables in schema '$SCHEMA_NAME' have been deleted"
