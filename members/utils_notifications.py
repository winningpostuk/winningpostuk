
from datetime import date
from django.core.mail import send_mail
from members.models import Membership


def deactivate_expired_memberships():
    """
    Automatically deactivate memberships where expiry_date has passed.
    """
    today = date.today()

    for m in Membership.objects.filter(active=True):
        if m.expiry_date and m.expiry_date < today:
            m.active = False
            m.save()


def send_7_day_expiry_warning():
    """
    Sends a user‑facing reminder email when a membership expires in 7 days.
    Ensures this is only sent once per renewal cycle.
    """
    today = date.today()

    # LIVE SITE URL
    renew_url = "https://winningpostuk.com/membership/"

    # DEV URL (uncomment to use locally)
    # renew_url = "http://127.0.0.1:8000/membership/"

    for m in Membership.objects.filter(active=True):
        if not m.expiry_date:
            continue

        days_left = (m.expiry_date - today).days

        if days_left == 7 and not m.warning_sent:
            send_mail(
                subject="Your WinningPostUK Membership Expires in 7 Days",
                message=(
                    f"Hi {m.user.first_name},\n\n"
                    f"This is a reminder that your {m.plan.title()} membership "
                    f"will expire in 7 days.\n\n"
                    f"To avoid missing your daily tips, please renew now:\n"
                    f"{renew_url}\n\n"
                    f"Best Regards,\n"
                    f"WinningPostUK Team"
                ),
                from_email="support@winningpostuk.com",
                recipient_list=[m.user.email],
            )

            m.warning_sent = True
            m.save()
