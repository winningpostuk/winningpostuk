
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from tips.models import Tip


class Command(BaseCommand):
    help = "Auto-assigns correct racecourse badge filenames to all tips."

    def handle(self, *args, **options):

        badges_path = os.path.join(settings.BASE_DIR, "static", "images", "courses")

        # Normalise: “York” -> “york.png”
        badge_lookup = {
            os.path.splitext(f)[0].replace('-', ' ').title(): f
            for f in os.listdir(badges_path)
            if f.lower().endswith(".png")
        }

        updated = 0
        tips = Tip.objects.all()

        for tip in tips:
            course = tip.racecourse.strip().title()

            if course in badge_lookup:
                correct_badge = badge_lookup[course]
                if tip.badge != correct_badge:
                    tip.badge = correct_badge
                    tip.save(update_fields=["badge"])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated badge filenames for {updated} tips."
            )
        )
