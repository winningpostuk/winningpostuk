
from __future__ import annotations

import os
from datetime import datetime

from django.conf import settings
from django.contrib import admin, messages
from django.templatetags.static import static
from django.utils import timezone
from django.utils.html import format_html

from tips.models import Tip
from tips.utils_profit import calculate_profit
from tips.utils_notifications import send_daily_tip_notifications


# =====================================================================
# ACTIONS
# =====================================================================

@admin.action(description="Notify all paid subscribers that today's tips are ready")
def admin_notify_tips_ready(modeladmin, request, queryset):
    """
    Render-safe notification sender: batched BCC, throttled, exception-handled
    so the admin page always returns a response.
    """
    try:
        result = send_daily_tip_notifications(
            batch_size=50,                 # BCC size
            sleep_between_batches=1.5,     # throttle between batches
            max_recipients=None,           # set an int for test limiting (e.g., 50)
            request=request,
        )
        messages.success(
            request,
            f"Notifications sent to {result['recipients']} subscriber(s) "
            f"in {result['batches']} batch(es)."
            + (f" Skipped: {result['skipped']}." if result.get("skipped") else "")
        )
    except Exception as e:
        messages.error(request, f"Error sending notifications: {e}")


@admin.action(description="Auto-settle selected tips")
def admin_auto_settle(modeladmin, request, queryset):
    """
    For each selected tip, if the race time has passed and it's not settled,
    mark as LOST (if no result) and set settled=True. Does not change future or already settled tips.
    """
    now = timezone.localtime()
    today = now.date()
    time_now = now.time()

    settled_count = 0
    for tip in queryset:
        if tip.settled:
            continue

        # Build a datetime for the tip's scheduled date+time when possible
        tip_dt = None
        try:
            tip_dt = datetime.combine(tip.race_date, tip.race_time)
            if timezone.is_naive(tip_dt):
                tip_dt = timezone.make_aware(tip_dt, timezone.get_current_timezone())
        except Exception:
            tip_dt = None

        should_settle = False
        if tip_dt is not None:
            should_settle = tip_dt <= now
        else:
            # Fallback comparison
            if tip.race_date < today:
                should_settle = True
            elif tip.race_date == today and tip.race_time <= time_now:
                should_settle = True

        if should_settle:
            tip.result = tip.result or "LOST"
            tip.settled = True
            tip.save(update_fields=["result", "settled"])
            settled_count += 1

    modeladmin.message_user(request, f"Auto-settle complete. {settled_count} tip(s) updated.")


@admin.action(description="Recalculate profit for selected tips")
def admin_recalc_profit(modeladmin, request, queryset):
    """
    Saves each selected tip that is already settled to trigger any model-level
    recalculation (signals or overridden save()).
    """
    updated = 0
    for tip in queryset:
        if tip.settled:
            tip.save()  # triggers internal profit recalculation if implemented
            updated += 1
    modeladmin.message_user(request, f"Profit recalculated for {updated} settled tip(s).")


@admin.action(description="Sync badges for selected tips")
def admin_sync_badges(modeladmin, request, queryset):
    """
    Map racecourse -> badge filename based on files in static/images/courses.
    Uses lowercase hyphenated filename convention: 'Ascot' -> 'ascot.png'
    """
    badges_path = os.path.join(settings.BASE_DIR, "static", "images", "courses")
    if not os.path.isdir(badges_path):
        modeladmin.message_user(request, "Courses images folder not found.", level=messages.WARNING)
        return

    # Build lookup: "Chelmsford City" (title case) -> "chelmsford city.png"
    badge_lookup = {
        os.path.splitext(f)[0].replace("-", " ").title(): f
        for f in os.listdir(badges_path)
        if f.lower().endswith(".png")
    }

    updated = 0
    for tip in queryset:
        course = (tip.racecourse or "").strip().title()
        new_badge = badge_lookup.get(course)
        if new_badge and tip.badge != new_badge:
            tip.badge = new_badge
            tip.save(update_fields=["badge"])
            updated += 1

    modeladmin.message_user(request, f"Synced badge filenames. {updated} tip(s) updated.")


# =====================================================================
# MAIN TIP ADMIN — OPTIMISED FOR RENDER
# =====================================================================

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    actions = [
        admin_notify_tips_ready,
        admin_auto_settle,
        admin_recalc_profit,
        admin_sync_badges,
    ]

    # Keep this list light to avoid OOM on free-tier containers
    list_display = (
        "racecourse",
        "race_date",
        "race_time",
        "horse_name",
        "category",
        "result",
    )

    list_filter = (
        "racecourse",
        "category",
        "result",
        "active",
        "created_at",
        "confidence",
    )

    search_fields = ("horse_name", "racecourse")
    ordering = ("race_date",)

    # ⭐ Critical memory saver on Render free tier
    list_per_page = 25

    # These are only used on the object form page (not on the list page)
    readonly_fields = ("created_at", "profit_preview", "badge_preview")

    fieldsets = (
        ("Race Information", {
            "fields": ("racecourse", "race_date", "race_time", "badge", "badge_preview")
        }),
        ("Horse Details", {
            "fields": ("horse_name", "odds", "category", "confidence")
        }),
        ("Insights", {
            "fields": ("pros", "cons")
        }),
        ("Analytics", {
            "fields": ("result", "profit", "profit_preview", "settled")
        }),
        ("Status", {
            "fields": ("active", "created_at")
        }),
    )

    # Canonical list of supported racecourses (used for form dropdown and badge mapping)
    RACECOURSE_CHOICES = [
        "Aintree", "Ascot", "Ayr", "Bangor-on-Dee", "Bath", "Beverley",
        "Brighton", "Carlisle", "Cartmel", "Catterick", "Chelmsford City",
        "Cheltenham", "Chepstow", "Chester", "Doncaster", "Epsom",
        "Exeter", "Fakenham", "Fontwell", "Goodwood", "Hamilton Park",
        "Haydock", "Hereford", "Hexham", "Huntingdon", "Kelso",
        "Kempton", "Leicester", "Lingfield", "Ludlow", "Market Rasen",
        "Musselburgh", "Newbury", "Newcastle", "Newmarket", "Newton Abbot",
        "Nottingham", "Perth", "Plumpton", "Redcar", "Ripon",
        "Salisbury", "Sandown", "Sedgefield", "Southwell", "Stratford",
        "Taunton", "Thirsk", "Uttoxeter", "Warwick", "Wetherby",
        "Wincanton", "Windsor", "Wolverhampton", "Worcester", "Yarmouth",
        "York",
    ]

    BADGE_MAP = {
        name: name.lower().replace(" ", "-") + ".png"
        for name in RACECOURSE_CHOICES
    }

    # ----------------------------------------
    # CUSTOM DISPLAY METHODS (detail page)
    # ----------------------------------------

    def confidence_stars(self, obj):
        """
        Render confidence as 0–5 star string (not used in list_display here).
        """
        try:
            val = int(obj.confidence or 0)
            val = max(0, min(5, val))
        except Exception:
            val = 0
        return "★" * val + "☆" * (5 - val)
    confidence_stars.short_description = "Confidence"
    confidence_stars.admin_order_field = "confidence"

    def profit_preview(self, obj):
        """
        Preview profit for the row (does not persist changes).
        """
        try:
            preview = calculate_profit(obj.odds, obj.result, obj.category)
            return f"{preview} pts"
        except Exception:
            return "-"
    profit_preview.short_description = "Profit Preview"

    def badge_preview(self, obj):
        """
        Show the mapped racecourse badge if present (only on detail form).
        """
        if obj.badge:
            url = static(f"images/courses/{obj.badge}")
            return format_html('<img src="{}" style="height:60px;" />', url)
        return "No badge"
    badge_preview.short_description = "Badge Preview"

    # ----------------------------------------
    # FORM FIELD CUSTOMISATION
    # ----------------------------------------

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "racecourse":
            formfield.choices = [(c, c) for c in self.RACECOURSE_CHOICES]
        return formfield

    # ----------------------------------------
    # AUTO-ASSIGN BADGE ON SAVE
    # ----------------------------------------

    def save_model(self, request, obj, form, change):
        """
        Assign a badge file based on the racecourse whenever saving a tip.
        """
        obj.badge = self.BADGE_MAP.get(obj.racecourse, "") or obj.badge
        super().save_model(request, obj, form, change)
