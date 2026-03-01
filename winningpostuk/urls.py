
from django.contrib import admin
from django.urls import path, include
from members.views import logout_view
from members.paypal_webhooks import paypal_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('paypal/webhook/', paypal_webhook, name='paypal_webhook'),

    # Include app URLs
    path('', include('members.urls')),
    path('tips/', include('tips.urls', namespace='tips')),   # <-- MISSING COMMA ADDED HERE

    path('captcha/', include('captcha.urls')),

    # Correct working logout URL
    path('logout/', logout_view, name='logout'),
]
