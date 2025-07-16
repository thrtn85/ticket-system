from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from notifications.models import Notification


@receiver(post_save, sender=Ticket)
def create_ticket_update_notification(sender, instance, created, **kwargs):
    if not created and instance.agent:
        Notification.objects.create(
            user=instance.agent,
            message=f'Ticket #{instance.id} was updated.'
        )
