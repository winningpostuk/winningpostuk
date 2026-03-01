
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date


# ------------------------------------
# USER PROFILE (DOB + extra fields)
# ------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


# ------------------------------------
# MEMBERSHIP MODEL (Bronze/Silver/Gold/Platinum)
# ------------------------------------
class Membership(models.Model):
    PLAN_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES)
    paypal_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    warning_sent = models.BooleanField(default=False)  # 7‑day warning sent flag

    def __str__(self):
        return f"{self.user.username} - {self.plan.title()}"


# ------------------------------------
# CONTACT MESSAGES (Stored in Admin)
# ------------------------------------
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.submitted_at.strftime('%Y-%m-%d')}"


# ------------------------------------
# DEACTIVATE EXPIRED MEMBERSHIPS
# ------------------------------------
def deactivate_expired_memberships():
    today = date.today()

    for membership in Membership.objects.all():
        if membership.expiry_date and membership.expiry_date < today:
            if membership.active:
                membership.active = False
                membership.save()


# ------------------------------------
# MEMBER PROXY MODEL (for Members Admin section)
# ------------------------------------
class Member(User):
    class Meta:
        proxy = True
        verbose_name = "Member"
        verbose_name_plural = "Members"

    @property
    def membership_plan(self):
        try:
            return self.membership.plan.title()
        except Membership.DoesNotExist:
            return "None"

    @property
    def membership_active(self):
        try:
            return self.membership.active
        except Membership.DoesNotExist:
            return False
