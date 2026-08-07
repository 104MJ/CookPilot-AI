"""Cree automatiquement un Profile a la creation d'un User."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    """Cree un Profile vide pour chaque nouvel utilisateur."""
    if created:
        Profile.objects.get_or_create(user=instance)
