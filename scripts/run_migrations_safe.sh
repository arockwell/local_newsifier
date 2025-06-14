#!/bin/bash
# Safe migration runner with proper error handling and state verification
set -e

echo "=== Safe Alembic Migration Runner ==="
echo "Time: $(date)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Function to run Python code safely
run_python() {
    python -c "$1" 2>&1
}

# Function to check database connectivity
check_db_connection() {
    echo "Checking database connection..."
    DB_CHECK=$(run_python "
from local_newsifier.config.settings import get_settings
from sqlalchemy import create_engine, text
try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('connected')
except Exception as e:
    print(f'connection_failed: {str(e)}')
")

    if [[ $DB_CHECK != "connected" ]]; then
        print_error "Database connection failed: $DB_CHECK"
        return 1
    fi
    print_success "Database connection successful"
    return 0
}

# Function to get detailed migration state
get_migration_state() {
    echo "Checking migration state..."

    # Check if alembic_version table exists
    ALEMBIC_EXISTS=$(run_python "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()
print('exists' if 'alembic_version' in tables else 'not_exists')
")

    echo "Alembic version table: $ALEMBIC_EXISTS"

    # Get current revision if table exists
    if [[ $ALEMBIC_EXISTS == "exists" ]]; then
        CURRENT_REV=$(alembic current 2>&1 | grep -oE '[a-f0-9]{12}' | head -1 || echo "none")
        echo "Current revision: $CURRENT_REV"

        # Get latest revision
        LATEST_REV=$(alembic heads 2>&1 | grep -oE '[a-f0-9]{12}' | head -1 || echo "none")
        echo "Latest revision: $LATEST_REV"

        # Check for pending migrations
        if [[ $CURRENT_REV == $LATEST_REV ]] && [[ $CURRENT_REV != "none" ]]; then
            print_success "Database is up to date!"
            return 0
        elif [[ $CURRENT_REV == "none" ]]; then
            print_warning "Alembic table exists but no revision is set"
            return 2
        else
            print_warning "Pending migrations detected"
            return 3
        fi
    else
        # Check if any tables exist
        TABLES_EXIST=$(run_python "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = set(inspector.get_table_names())
our_tables = {'articles', 'entities', 'analysis_results', 'rss_feeds', 'apify_source_configs'}
if tables.intersection(our_tables):
    print('exists')
else:
    print('not_exists')
")

        if [[ $TABLES_EXIST == "exists" ]]; then
            print_warning "Tables exist but Alembic is not initialized"
            return 4
        else
            echo "Fresh database detected"
            return 5
        fi
    fi
}

# Function to create lock file for migration
acquire_migration_lock() {
    LOCK_FILE="/tmp/alembic_migration.lock"

    if [ -f "$LOCK_FILE" ]; then
        LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        print_warning "Migration lock exists (PID: $LOCK_PID)"

        # Check if process is still running
        if ps -p "$LOCK_PID" > /dev/null 2>&1; then
            print_error "Another migration process is running"
            return 1
        else
            print_warning "Stale lock detected, removing..."
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
    return 0
}

release_migration_lock() {
    rm -f "/tmp/alembic_migration.lock"
}

# Function to backup current schema
backup_schema() {
    if command -v pg_dump &> /dev/null; then
        BACKUP_FILE="/tmp/schema_backup_$(date +%Y%m%d_%H%M%S).sql"
        echo "Creating schema backup: $BACKUP_FILE"
        pg_dump -s "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || print_warning "Schema backup failed"
    fi
}

# Main execution
main() {
    # Ensure we're in the right directory
    cd "$(dirname "$0")/.." || exit 1

    # Check database connection
    if ! check_db_connection; then
        exit 1
    fi

    # Acquire migration lock
    if ! acquire_migration_lock; then
        exit 1
    fi

    # Trap to ensure lock is released
    trap release_migration_lock EXIT

    # Get migration state
    get_migration_state
    STATE=$?

    case $STATE in
        0)
            print_success "No migrations needed"
            ;;
        2)
            print_warning "Fixing missing revision..."
            alembic stamp head
            print_success "Database stamped with head revision"
            ;;
        3)
            echo "Running pending migrations..."
            backup_schema

            # Show what will be applied
            echo "Migrations to apply:"
            alembic history -r current:head -v

            # Run migrations
            if alembic upgrade head; then
                print_success "Migrations completed successfully"
            else
                print_error "Migration failed!"
                echo "Check the error above and consider:"
                echo "1. Reviewing the migration files"
                echo "2. Checking for data conflicts"
                echo "3. Running 'alembic downgrade -1' to rollback"
                exit 1
            fi
            ;;
        4)
            print_error "Database has tables but no Alembic tracking"
            echo "This requires manual intervention:"
            echo "1. Verify the current schema matches a known migration"
            echo "2. Run: alembic stamp <appropriate-revision>"
            echo "3. Run this script again"
            exit 1
            ;;
        5)
            echo "Initializing fresh database..."
            if alembic upgrade head; then
                print_success "Database initialized successfully"
            else
                print_error "Database initialization failed!"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown migration state: $STATE"
            exit 1
            ;;
    esac

    # Final verification
    echo ""
    echo "Final state:"
    alembic current

    # Show table count
    TABLE_COUNT=$(run_python "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
print(len(inspector.get_table_names()))
")
    echo "Total tables in database: $TABLE_COUNT"
}

# Run main function
main "$@"
