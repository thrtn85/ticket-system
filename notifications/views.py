from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        qs = self.request.user.notifications.all()
        # Mark all as read when viewed
        qs.filter(is_read=False).update(is_read=True)
        return qs
