from django.db import models
from django.conf import settings

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets_created'
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_assigned'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='low',
    )

    def __str__(self):
        return f"Ticket #{self.id}"

class Comment(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on Ticket #{self.ticket.id} by {self.user.email}"
    
class TicketHistory(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    
    previous_status = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES, null=True, blank=True)
    
    previous_agent = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    new_agent = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    previous_priority = models.CharField(max_length=10, choices=Ticket.PRIORITY_CHOICES, null=True, blank=True)
    new_priority = models.CharField(max_length=10, choices=Ticket.PRIORITY_CHOICES, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
