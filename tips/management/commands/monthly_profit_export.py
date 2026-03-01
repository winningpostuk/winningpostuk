
import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from tips.models import Tip
from django.db.models import Sum, Count, Q


class Command(BaseCommand):
    help = "Exports monthly profit data to CSV."

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Year (e.g. 2024)")
        parser.add_argument("month", type=int, help="Month (1-12)")

    def handle(self, *args, **options):
        year = options["year"]
        month = options["month"]

        tips = Tip.objects.filter(
            settled=True,
            race_date__year=year,
            race_date__month=month
        ).order_by("race_date")

        if not tips.exists():
            self.stdout.write(self.style.WARNING("No tips found for this month."))
            return

        # Prepare export folder
        export_dir = os.path.join(settings.BASE_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)

        filename = os.path.join(
            export_dir,
            f"monthly_profit_{year}_{str(month).zfill(2)}.csv"
        )

        # ---- Write CSV ----
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Date", "Tips", "Wins", "Strike Rate %", "Profit Points"])

            # Group by day
            days = tips.values("race_date").annotate(
                tips_count=Count("id"),
                wins=Count("id", filter=Q(result="WON")),
                profit=Sum("profit")
            )

            for day in days:
                strike_rate = (
                    (day["wins"] / day["tips_count"]) * 100
                    if day["tips_count"]
                    else 0
                )

                writer.writerow([
                    day["race_date"].strftime("%Y-%m-%d"),
                    day["tips_count"],
                    day["wins"],
                    round(strike_rate, 2),
                    float(day["profit"] or 0),
                ])

        self.stdout.write(
            self.style.SUCCESS(f"Export complete: {filename}")
        )
