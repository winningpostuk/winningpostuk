
from django.core.management.base import BaseCommand
from django.utils import timezone
from tips.models import Tip


class Command(BaseCommand):
    help = "Automatically deactivates all tips older than today."

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        updated_count = Tip.objects.exclude(created_at__date=today).update(active=False)

        self.stdout.write(
            self.style.SUCCESS(f"Deactivated {updated_count} old tips.")
        )
