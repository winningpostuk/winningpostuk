
from datetime import date, timedelta
from members.models import Membership


# Membership durations
PLAN_DURATIONS = {
    'bronze': 30,
    'silver': 90,
    'gold': 180,
    'platinum': 365,
}


def renew_membership(user):
    """
    Automatically renews membership when PayPal payment is confirmed.
    Extends expiry date, re‑activates membership and resets warnings.
    """
    today = date.today()

    membership, created = Membership.objects.get_or_create(user=user)

    duration = PLAN_DURATIONS.get(membership.plan, 30)

    # If expired or not set, restart from today
    if not membership.expiry_date or membership.expiry_date < today:
        membership.expiry_date = today + timedelta(days=duration)
    else:
        # Extend from current expiry date
        membership.expiry_date = membership.expiry_date + timedelta(days=duration)

    membership.active = True
    membership.warning_sent = False    # Reset email warning flag
    membership.save()

    return membership
