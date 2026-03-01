
from django.utils import timezone
from .models import Tip

def deactivate_old_tips():
    today = timezone.now().date()
    Tip.objects.exclude(created_at__date=today).update(active=False)
