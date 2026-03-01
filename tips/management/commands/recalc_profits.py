
from django.core.management.base import BaseCommand
from tips.models import Tip


class Command(BaseCommand):
    help = "Recalculates profit for all settled tips using current profit engine"

    def handle(self, *args, **options):
        settled_tips = Tip.objects.filter(settled=True)
        total = settled_tips.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No settled tips found."))
            return

        self.stdout.write(self.style.NOTICE(f"Recalculating profit for {total} settled tips..."))

        updated = 0
        for tip in settled_tips:
            old_profit = tip.profit
            tip.save()  # triggers calculate_profit via model.save()
            if tip.profit != old_profit:
                updated += 1
                self.stdout.write(
                    f"Updated Tip ID {tip.id}: {old_profit} -> {tip.profit}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {updated}/{total} tips updated."
        ))
