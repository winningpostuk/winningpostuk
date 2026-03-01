
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Membership


@receiver(post_save, sender=User)
def create_profile_and_membership(sender, instance, created, **kwargs):
    if created:
        # Create profile
        Profile.objects.create(user=instance)
        # Create empty membership (inactive until payment)
        Membership.objects.create(user=instance, plan='bronze', active=False)
