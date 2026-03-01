
from decimal import Decimal
from django.db import models
from tips.utils_profit import calculate_profit

# ---------------------------------------
# UK Racecourse list (centralised)
# ---------------------------------------
UK_RACECOURSES = [
    "Aintree", "Ascot", "Ayr", "Bangor-on-Dee", "Bath", "Beverley",
    "Brighton", "Carlisle", "Cartmel", "Catterick", "Chelmsford City",
    "Cheltenham", "Chepstow", "Chester", "Doncaster", "Epsom",
    "Exeter", "Fakenham", "Ffos Las", "Fontwell", "Goodwood", "Hamilton Park",
    "Haydock", "Hereford", "Hexham", "Huntingdon", "Kelso",
    "Kempton", "Leicester", "Lingfield", "Ludlow", "Market Rasen",
    "Musselburgh", "Newbury", "Newcastle", "Newmarket", "Newton Abbot",
    "Nottingham", "Perth", "Plumpton", "Redcar", "Ripon",
    "Salisbury", "Sandown", "Sedgefield", "Southwell", "Stratford",
    "Taunton", "Thirsk", "Uttoxeter", "Warwick", "Wetherby",
    "Wincanton", "Windsor", "Wolverhampton", "Worcester", "Yarmouth",
    "York",
]


class Tip(models.Model):

    CATEGORY_CHOICES = [
    ('NAP', 'NAP'),
    ('NB', 'Next Best'),
    ('WINNER', 'To Win'),
    ('DARKHORSE', 'Dark Horse'),
    ('EW', 'Each Way'),
]

    RESULT_CHOICES = [
        ("WON", "Won"),
        ("PLACED", "Placed"),
        ("LOST", "Lost"),
        ("VOID", "Void / Non‑Runner"),
        ("", "Not Settled"),
    ]

    CONFIDENCE_CHOICES = [
        (1, "⭐"),
        (2, "⭐⭐"),
        (3, "⭐⭐⭐"),
        (4, "⭐⭐⭐⭐"),
        (5, "⭐⭐⭐⭐⭐"),
    ]

    # ---------------------------------------
    # Fields (correctly indented inside class)
    # ---------------------------------------
    racecourse = models.CharField(
        max_length=100,
        choices=[(c, c) for c in UK_RACECOURSES]
    )

    race_date = models.DateField(
        help_text="Date of the race"
    )

    race_time = models.TimeField()
    horse_name = models.CharField(max_length=120)
    odds = models.CharField(max_length=20)

    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default="EW",
    )

    badge = models.CharField(
        max_length=120,
        blank=True,
        help_text="Filename of the racecourse badge (e.g. ascot.png)"
    )

    pros = models.TextField(
        blank=True,
        help_text="Add one pro per line (e.g. 'Trainer in form', 'Good ground record')."
    )

    cons = models.TextField(
        blank=True,
        help_text="Add one con per line (e.g. 'Steps up in class', 'Unproven at distance')."
    )

    confidence = models.IntegerField(
        choices=CONFIDENCE_CHOICES,
        default=3,
        help_text="1–5 star confidence rating"
    )

    result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES,
        default="",
        blank=True,
        help_text="Outcome of the tip"
    )

    profit = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Profit or loss in points"
    )

    settled = models.BooleanField(
        default=False,
        help_text="Tick when the race result is known"
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------------------
    # Meta + Methods
    # ---------------------------------------
    class Meta:
        ordering = ["race_time"]
        verbose_name = "Tip"
        verbose_name_plural = "Tips"


    def __str__(self):
        return f"{self.racecourse} {self.race_time} - {self.horse_name} ({self.category})"

    @property
    def category_colour(self):
        return {
            "NAP": "gold",
            "NB": "silver",
            "WINNER": "green",
            "DARKHORSE": "purple",
            "EW": "bronze",
        }.get(self.category, "bronze")

    @property
    def badge_path(self):
        if not self.badge:
            return ""
        return f"images/courses/{self.badge}"

    # ---------------------------------------
    # Auto-calc profit
    # ---------------------------------------
    def save(self, *args, **kwargs):

        # Only calculate profit once result exists
        if self.result in ["WON", "PLACED", "LOST", "VOID"]:
            self.profit = calculate_profit(
                self.odds,
                self.result,
                self.category
            )

        super().save(*args, **kwargs)
