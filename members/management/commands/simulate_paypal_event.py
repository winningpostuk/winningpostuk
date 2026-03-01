
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from members.models import Membership

# Your plan ID map (same as webhook)
PAYPAL_PLAN_MAP = {
    "bronze": "P-6N7664305R105354XNFXGEHA",
    "silver": "P-4XD80426AA510693ANFXGEWY",
    "gold": "P-37R819539W074244BNFXGE7Q",
    "platinum": "P-93G55638CB141871UNFXGFIY",
}

class Command(BaseCommand):
    help = (
        "Simulate a PayPal webhook event for testing.\n"
        "Usage:\n"
        "  python manage.py simulate_paypal_event gold\n"
        "  python manage.py simulate_paypal_event gold --cancel\n"
        "  python manage.py simulate_paypal_event bronze --email=test@example.com\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "plan",
            type=str,
            help="Plan to simulate: bronze, silver, gold, platinum",
        )

        parser.add_argument(
            "--email",
            type=str,
            help="User email to simulate event for",
            default=None,
        )

        parser.add_argument(
            "--cancel",
            action="store_true",
            help="Simulate cancellation instead of activation",
        )

    def handle(self, *args, **options):
        plan = options["plan"].lower()

        if plan not in PAYPAL_PLAN_MAP:
            self.stdout.write(self.style.ERROR(f"Invalid plan: {plan}"))
            return

        plan_id = PAYPAL_PLAN_MAP[plan]

        # Pick a user
        if options["email"]:
            try:
                user = User.objects.get(email=options["email"])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR("User does not exist."))
                return
        else:
            user = User.objects.filter(is_staff=False).order_by("-date_joined").first()
            if not user:
                self.stdout.write(self.style.ERROR("No non-staff users available to test with."))
                return

        # Ensure membership exists
        membership, created = Membership.objects.get_or_create(user=user)

        # Fake PayPal subscription ID
        timestamp = int(timezone.now().timestamp())
        fake_sub_id = f"I-TEST-{plan.upper()}-{timestamp}"

        # Pick event type
        if options["cancel"]:
            event_type = "BILLING.SUBSCRIPTION.CANCELLED"
            self.stdout.write(self.style.WARNING("Simulating cancellation event..."))
        else:
            event_type = "BILLING.SUBSCRIPTION.ACTIVATED"

        # Build webhook payload
        payload = {
            "event_type": event_type,
            "resource": {
                "id": fake_sub_id,
                "plan_id": plan_id,
                "subscriber": {
                    "email_address": user.email,
                },
                "billing_info": {
                    "next_billing_time": None  # Let your cycle logic handle expiry
                },
            },
        }

        # Send POST request to webhook
        client = Client(HTTP_HOST="testserver")  # required for ALLOWED_HOSTS
        response = client.post(
            "/paypal/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Output results
        self.stdout.write(
            self.style.SUCCESS(
                f"Webhook sent for {user.email} ({plan}) — Event={event_type} — HTTP {response.status_code}"
            )
        )

        membership.refresh_from_db()

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated Membership → "
                f"plan={membership.plan}, active={membership.active}, "
                f"expiry={membership.expiry_date}, sub_id={membership.paypal_subscription_id}"
            )
        )
