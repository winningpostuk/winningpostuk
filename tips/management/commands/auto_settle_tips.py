
from django.core.management.base import BaseCommand
from django.utils import timezone
from tips.models import Tip


class Command(BaseCommand):
    help = "Auto-settles tips whose race time has already passed."

    def handle(self, *args, **options):

        now = timezone.now()

        overdue = Tip.objects.filter(
            settled=False,
            race_date__lt=now.date()
        ) | Tip.objects.filter(
            settled=False,
            race_date=now.date(),
            race_time__lt=now.time()
        )

        overdue = overdue.distinct()

        if not overdue.exists():
            self.stdout.write(self.style.WARNING("No unsettled, overdue tips found."))
            return

        updated_count = 0

        for tip in overdue:
            tip.result = tip.result or "LOST"         # default fallback
            tip.settled = True
            tip.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Auto-settled {updated_count} overdue tips."
            )
        )
