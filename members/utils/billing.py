
from members.models import Membership

def user_has_active_subscription(user):
    """
    Unified billing status checker.
    Works with PayPal or any provider that sets Membership.active = True.

    Returns:
        True if user has an active subscription.
        False otherwise.
    """

    if not user.is_authenticated:
        return False

    return Membership.objects.filter(
        user=user,
        active=True
    ).exists()
