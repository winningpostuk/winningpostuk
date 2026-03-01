
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html

from tips.models import Tip
from tips.management.commands.auto_settle_tips import Command as AutoSettle
from tips.management.commands.sync_race_badges import Command as SyncBadges
from tips.management.commands.monthly_profit_export import Command as ExportProfit


class ToolsAdmin(admin.ModelAdmin):
    change_list_template = "admin/tips/tools.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("auto-settle/", self.auto_settle_view, name="auto_settle_tools"),
            path("sync-badges/", self.sync_badges_view, name="sync_badges_tools"),
            path("export-profit/", self.export_profit_view, name="export_profit_tools"),
        ]
        return custom + urls

    def auto_settle_view(self, request):
        AutoSettle().handle()
        messages.success(request, "Auto-settle completed.")
        return redirect("admin:tips_tools_changelist")

    def sync_badges_view(self, request):
        SyncBadges().handle()
        messages.success(request, "Badge sync completed.")
        return redirect("admin:tips_tools_changelist")

    def export_profit_view(self, request):
        ExportProfit().handle(2026, 2)   # Example month, update as needed
        messages.success(request, "Monthly profit export complete.")
        return redirect("admin:tips_tools_changelist")


admin.site.register(Tip, admin.ModelAdmin)  # keep standard Tip admin

admin.site.register(type("Tools", (), {}), ToolsAdmin)
