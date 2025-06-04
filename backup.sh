#!/bin/bash
# Simple wrapper script for database backup operations

# Make sure we're in the correct directory
cd "$(dirname "$0")"

# Check if Python script exists
if [ ! -f "backup_database.py" ]; then
    echo "Error: backup_database.py not found"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Discord Bot Database Backup Utility"
    echo "Usage: ./backup.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backup [sql|json]     Create a backup (default: sql)"
    echo "  restore <file>        Restore from backup file"
    echo "  list                  List available backups"
    echo "  stats                 Show database statistics"
    echo ""
    echo "Examples:"
    echo "  ./backup.sh backup              # Create SQL backup"
    echo "  ./backup.sh backup json         # Create JSON backup"
    echo "  ./backup.sh restore backup.sql  # Restore from SQL backup"
    echo "  ./backup.sh list                # List all backups"
    echo "  ./backup.sh stats               # Show database stats"
}

# Parse command line arguments
case "$1" in
    "backup")
        FORMAT=${2:-sql}
        python3 backup_database.py backup --format "$FORMAT"
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo "Error: Backup file required for restore"
            echo "Usage: ./backup.sh restore <backup_file>"
            exit 1
        fi
        python3 backup_database.py restore --file "$2"
        ;;
    "list")
        python3 backup_database.py list
        ;;
    "stats")
        python3 backup_database.py stats
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac