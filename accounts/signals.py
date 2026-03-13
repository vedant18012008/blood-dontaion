from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DonorProfile


@receiver(post_save, sender=User)
def create_donor_profile(sender, instance, created, **kwargs):
    if created:
        DonorProfile.objects.create(user=instance)
