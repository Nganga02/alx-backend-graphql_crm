from django.utils import timezone
from datetime import timedelta
from django.core.management.base import BaseCommand
from crm.models import Customer

class Command(BaseCommand):
    help = "Delete customers who are marked as inactive (is_active=False)"

    def handle(self, *args, **options):
        

        cutoff_date = timezone.now() - timedelta(days=365)
        # Count how many we are about to delete
        to_delete = Customer.objects.filter(purchases__order_date__lte=cutoff_date)
        count = to_delete.count()

        # Actually delete them
        deleted_count, _ = to_delete.delete()

        # Print ONLY the number (this is what your bash script captures)
        print(deleted_count)

        # Optional: also write a nice message to stderr so it doesn't interfere with the number
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} inactive customer(s).")
        )