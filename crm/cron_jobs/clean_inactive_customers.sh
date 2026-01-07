PROJECT_DIR="/home/kamau/Documents/EDUCATION/programming_bckend/projects/ALX/alx-backend-graphql_crm"
cd $PROJECT_DIR || exit 1

#If using a virtual environment
source $PROJECT_DIR/.venv/bin/activate

DELETED_COUNT=$(python3 manage.py customer_cleanup.)

echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted customers: $DELETED_COUNT" >> /tmp/customer_cleanup_log.txt