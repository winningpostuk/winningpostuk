
import requests
import base64
from django.conf import settings


def get_paypal_access_token():
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def cancel_paypal_subscription(subscription_id):
    access_token = get_paypal_access_token()

    url = f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/cancel"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    data = {"reason": "Cancelled by admin via Django backend"}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return True
