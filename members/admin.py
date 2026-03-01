
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from members.models import ContactMessage, Membership
from datetime import date

# =====================================================================
# 1. Default Django User admin (unchanged)
# =====================================================================
# Gives access to passwords, permissions, staff controls, etc.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =====================================================================
# 2. Customer Proxy Model (separates website users)
# =====================================================================
class Customer(User):
    class Meta:
        proxy = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    """
    Shows ONLY normal website users (non-staff)
    Clean customer view, separate from admin users.
    """
    list_display = ("username", "email", "first_name", "last_name", "date_joined")
    ordering = ("username",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_staff=False)


# =====================================================================
# 3. AdminUser Proxy Model (separates admin/staff users)
# =====================================================================
class AdminUser(User):
    class Meta:
        proxy = True
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
    """
    Shows only staff & superusers for management convenience.
    """
    list_display = ("username", "email", "is_staff", "is_superuser", "last_login")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_staff=True)


# =====================================================================
# 4. Membership Admin (subscription management)
# =====================================================================
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'user_email',
        'plan',
        'active',
        'expiry_date',
        'paypal_subscription_id',
        'date_joined',
    )

    search_fields = ('user__email', 'user__username', 'paypal_subscription_id')
    list_filter = ('plan', 'active')

    # For expiry automation (optional)
    def get_queryset(self, request):
        from members.utils_notifications import deactivate_expired_memberships, send_7_day_expiry_warning
        deactivate_expired_memberships()
        send_7_day_expiry_warning()
        return super().get_queryset(request)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def date_joined(self, obj):
        return obj.user.date_joined
    date_joined.short_description = "Joined"

    # ==============================
    # Cancel Subscription Action
    # ==============================
    actions = ["cancel_subscription"]

    @admin.action(description="Cancel Subscription")
    def cancel_subscription(self, request, queryset):
        count = 0
        for membership in queryset:
            membership.active = False
            membership.expiry_date = None
            membership.warning_sent = False
            membership.save()
            count += 1

        self.message_user(request, f"{count} subscription(s) cancelled.")


# =====================================================================
# 5. Contact Messages Admin
# =====================================================================
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    readonly_fields = ('name', 'email', 'message', 'submitted_at')
    ordering = ('-submitted_at',)
