
import json
from datetime import datetime
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from members.models import Membership


# Map PayPal plan IDs → internal plan names
PAYPAL_PLAN_MAP = {
    "P-6N7664305R105354XNFXGEHA": "bronze",
    "P-4XD80426AA510693ANFXGEWY": "silver",
    "P-37R819539W074244BNFXGE7Q": "gold",
    "P-93G55638CB141871UNFXGFIY": "platinum",
}

# Billing cycle lengths (in months)
PLAN_CYCLE_MONTHS = {
    "bronze": 1,
    "silver": 3,
    "gold": 6,
    "platinum": 12,
}


@csrf_exempt
def paypal_webhook(request):
    """
    Handles PayPal subscription lifecycle webhooks:
      - BILLING.SUBSCRIPTION.ACTIVATED
      - BILLING.SUBSCRIPTION.RENEWED
      - BILLING.SUBSCRIPTION.CANCELLED
      - BILLING.SUBSCRIPTION.SUSPENDED
      - PAYMENT.SALE.DENIED
    """

    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    # Parse JSON
    try:
        event = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    event_type = event.get("event_type", "")
    resource = event.get("resource", {})

    # Extract fields
    subscription_id = resource.get("id")
    payer_email = resource.get("subscriber", {}).get("email_address")
    plan_id = resource.get("plan_id")
    next_billing = resource.get("billing_info", {}).get("next_billing_time")

    # STEP 1 — Locate Membership
    membership = None

    # First: match by email
    if payer_email:
        membership = Membership.objects.filter(user__email__iexact=payer_email).first()

    # Second: fallback to subscription ID match
    if not membership and subscription_id:
        membership = Membership.objects.filter(paypal_subscription_id=subscription_id).first()

    if not membership:
        print(f"[PayPal Webhook] No membership found for email={payer_email}, sub_id={subscription_id}")
        return HttpResponse("No membership found", status=200)

    # STEP 2 — Ensure a valid plan exists BEFORE calculating expiry
    # (Fixes your 'active flag not set' issue)
    if plan_id in PAYPAL_PLAN_MAP:
        membership.plan = PAYPAL_PLAN_MAP[plan_id]
    elif not membership.plan:
        # Fallback if membership.plan was empty
        membership.plan = "bronze"

    # STEP 3 — Expiry calculation
    def update_expiry():
        """
        Expiry precedence:
        1. Use PayPal next_billing_time if provided
        2. Otherwise calculate based on cycle length
        """

        # Case 1 — PayPal sends next billing time
        if next_billing:
            try:
                dt = datetime.fromisoformat(next_billing.replace("Z", "")).date()
                membership.expiry_date = dt
                return
            except Exception:
                pass  # fallback to cycle logic

        # Case 2 — Internal cycle-based expiry
        months = PLAN_CYCLE_MONTHS.get(membership.plan, 1)
        membership.expiry_date = timezone.now().date() + relativedelta(months=months)

    # =====================================================================
    # EVENT HANDLERS
    # =====================================================================

    # ACTIVATED
    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        print(f"[PayPal] ACTIVATED for {payer_email}")
        membership.active = True
        membership.paypal_subscription_id = subscription_id
        update_expiry()
        membership.save()
        return HttpResponse("Subscription activated", status=200)

    # RENEWED
    if event_type == "BILLING.SUBSCRIPTION.RENEWED":
        print(f"[PayPal] RENEWED for {payer_email}")
        membership.active = True
        update_expiry()
        membership.save()
        return HttpResponse("Subscription renewed", status=200)

    # CANCELLED or SUSPENDED
    if event_type in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.SUSPENDED"):
        print(f"[PayPal] CANCELLED/SUSPENDED for {payer_email}")
        membership.active = False
        membership.save()
        return HttpResponse("Subscription cancelled", status=200)

    # PAYMENT FAILURE → deactivate
    if event_type == "PAYMENT.SALE.DENIED":
        print(f"[PayPal] PAYMENT FAILED for {payer_email}")
        membership.active = False
        membership.save()
        return HttpResponse("Payment failed — user deactivated", status=200)

    # Unknown
    print(f"[PayPal] Unhandled event: {event_type}")
    return HttpResponse("Unhandled event", status=200)
