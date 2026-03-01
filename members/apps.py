
from django.apps import AppConfig

class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'

    def ready(self):
        import members.paypal_webhooks
        import members.signals
